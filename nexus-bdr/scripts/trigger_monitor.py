#!/usr/bin/env python3
"""
Trigger Event Monitor — Nexus BDR Agent
=========================================
Scans for buying signals across your prospect universe daily.
Surfaces "reach out NOW because X just happened" alerts.

Trigger Events Monitored:
  - New facility / expansion announcements
  - Hiring signals (extraction techs, lab managers, production staff)
  - New product launches (new SKUs, new product lines)
  - Funding rounds / acquisitions
  - License approvals (new state, new license type)
  - Trade show registrations / upcoming exhibits
  - Leadership changes (new CEO, new VP Sales)
  - Competitor supplier issues (recalls, shortages, price hikes)
  - Social media signals (posts about terpenes, new equipment)
  - Regulatory changes affecting their market

Usage:
    python3 trigger_monitor.py --scan-all
    python3 trigger_monitor.py --scan-list watchlist.json
    python3 trigger_monitor.py --scan-company "Green Dot Labs"
    python3 trigger_monitor.py --scan-industry --vertical "cannabis extracts" --state "CO"
    python3 trigger_monitor.py --briefing

Environment:
    ANTHROPIC_API_KEY
"""

import os
import sys
import json
import re
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
CONFIG_DIR = SKILL_DIR / "config"
WATCHLIST_DIR = CONFIG_DIR / "watchlists"
ALERTS_DIR = OUTPUT_DIR / "alerts"

for d in [OUTPUT_DIR, CONFIG_DIR, WATCHLIST_DIR, ALERTS_DIR]:
    d.mkdir(exist_ok=True)


def call_claude(system_prompt, user_prompt):
    """Call Claude with web search."""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    }
    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=180)
        if resp.status_code == 429:
            print("    ⏳ Rate limited, waiting 60s...")
            time.sleep(60)
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=180)
        if resp.status_code != 200:
            print(f"    ❌ Claude error {resp.status_code}: {resp.text[:200]}")
            return ""
        data = resp.json()
        return "\n".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return ""


def parse_json(response):
    """Extract JSON from Claude response."""
    if not response:
        return None
    m = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
    else:
        arr = response.find('[')
        obj = response.find('{')
        if arr != -1 and (obj == -1 or arr < obj):
            end = response.rfind(']')
            cleaned = response[arr:end+1] if end > arr else ""
        elif obj != -1:
            end = response.rfind('}')
            cleaned = response[obj:end+1] if end > obj else ""
        else:
            return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ─── WATCHLIST MANAGEMENT ───────────────────────────────────

def load_watchlist():
    """Load the master watchlist of companies to monitor."""
    path = WATCHLIST_DIR / "master_watchlist.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"companies": [], "competitors": [], "industry_keywords": [], "updated_at": None}


def save_watchlist(watchlist):
    """Save the master watchlist."""
    watchlist["updated_at"] = datetime.utcnow().isoformat()
    path = WATCHLIST_DIR / "master_watchlist.json"
    with open(path, "w") as f:
        json.dump(watchlist, f, indent=2)


def add_to_watchlist(company_name, domain=None, category="prospect"):
    """Add a company to the watchlist."""
    wl = load_watchlist()
    existing = {c["name"].lower() for c in wl["companies"]}
    if company_name.lower() not in existing:
        wl["companies"].append({
            "name": company_name,
            "domain": domain or "",
            "category": category,  # prospect, customer, competitor
            "added_at": datetime.utcnow().isoformat(),
            "last_scanned": None,
            "alert_count": 0,
        })
        save_watchlist(wl)
        return True
    return False


def build_watchlist_from_enriched():
    """Auto-build watchlist from all enriched prospect files."""
    wl = load_watchlist()
    existing = {c["name"].lower() for c in wl["companies"]}
    added = 0

    for f in OUTPUT_DIR.glob("enriched_*.json"):
        with open(f) as fh:
            data = json.load(fh)
        for lead in data.get("leads", []):
            name = lead.get("company_name", "")
            if name and name.lower() not in existing:
                wl["companies"].append({
                    "name": name,
                    "domain": lead.get("company_domain", lead.get("domain", "")),
                    "category": "prospect",
                    "brand": lead.get("nexus_brand", ""),
                    "score": lead.get("nexus_lead_score", 0),
                    "state": lead.get("state", ""),
                    "added_at": datetime.utcnow().isoformat(),
                    "last_scanned": None,
                    "alert_count": 0,
                })
                existing.add(name.lower())
                added += 1

    # Add known competitors
    competitors = [
        {"name": "True Terpenes", "domain": "trueterpenes.com", "category": "competitor"},
        {"name": "Abstrax Tech", "domain": "abstraxtech.com", "category": "competitor"},
        {"name": "Floraplex Terpenes", "domain": "floraplex.com", "category": "competitor"},
        {"name": "Denver Terpenes", "domain": "denverterpenes.com", "category": "competitor"},
        {"name": "Peak Supply Co", "domain": "peaksupplyco.com", "category": "competitor"},
        {"name": "Xtra Laboratories", "domain": "xtralaboratories.com", "category": "competitor"},
        {"name": "Eybna Technologies", "domain": "eybna.com", "category": "competitor"},
        {"name": "Mr Extractor", "domain": "mrextractor.com", "category": "competitor"},
    ]
    for comp in competitors:
        if comp["name"].lower() not in existing:
            comp["added_at"] = datetime.utcnow().isoformat()
            comp["last_scanned"] = None
            comp["alert_count"] = 0
            wl["companies"].append(comp)
            existing.add(comp["name"].lower())
            added += 1

    save_watchlist(wl)
    return added


# ─── TRIGGER SCANNING ──────────────────────────────────────

def scan_company(company_name, domain="", category="prospect"):
    """Scan a single company for trigger events."""

    system_prompt = """You are a B2B sales intelligence analyst for Nexus Agriscience, a botanical terpene supplier.
Your job is to find RECENT trigger events — things that happened in the last 30 days that signal this company might be ready to buy terpenes or change suppliers.

TRIGGER EVENTS TO WATCH FOR:
1. EXPANSION: New facility, new state, new market, scaling production
2. HIRING: Job postings for extraction techs, lab managers, production staff, formulators
3. PRODUCT LAUNCH: New product lines, new SKUs, new brands
4. FUNDING: Series A/B/C, acquisition, merger, private equity investment
5. LICENSE: New state license approved, license renewal, new license type
6. TRADE SHOW: Registered for upcoming events (MJBizCon, Hall of Flowers, etc.)
7. LEADERSHIP: New CEO, VP Ops, Head of Production, any C-suite change
8. SUPPLIER ISSUES: Current terpene supplier problems, switching signals
9. SOCIAL SIGNALS: Posts about terpenes, new equipment, production upgrades
10. REGULATORY: New state going legal, regulation changes affecting their products

Return ONLY valid JSON — no other text. If no events found, return an empty events array."""

    search_hint = company_name
    if domain:
        search_hint += f" {domain}"

    user_prompt = f"""Search for recent news and activity about "{company_name}" ({domain or 'no domain'}).

Do multiple searches:
1. "{company_name} news 2026" — recent news
2. "{company_name} hiring" or "{company_name} jobs" — job postings
3. "{company_name} expansion" OR "{company_name} new facility" — growth signals
4. "{company_name} funding" OR "{company_name} acquisition" — financial moves
5. "{domain}" if domain provided — check their website for announcements

Return:
{{
  "company": "{company_name}",
  "domain": "{domain}",
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "events": [
    {{
      "type": "EXPANSION|HIRING|PRODUCT_LAUNCH|FUNDING|LICENSE|TRADE_SHOW|LEADERSHIP|SUPPLIER_ISSUE|SOCIAL_SIGNAL|REGULATORY",
      "headline": "Brief description of what happened",
      "detail": "2-3 sentence explanation with specifics",
      "source_url": "URL where you found this",
      "date_detected": "approximate date",
      "urgency": "HIGH|MEDIUM|LOW",
      "sales_action": "Specific action to take — what to say, who to contact, what to offer",
      "outreach_hook": "Opening line for outreach email based on this event"
    }}
  ],
  "overall_status": "HOT (multiple recent signals)|WARM (some activity)|QUIET (nothing notable)|COLD (negative signals)",
  "recommended_action": "What should the sales team do right now?",
  "next_scan_days": 7
}}

Only include events you actually found evidence for. Never fabricate."""

    print(f"    🔍 Scanning: {company_name}...", end=" ", flush=True)
    response = call_claude(system_prompt, user_prompt)
    result = parse_json(response)

    if result:
        events = result.get("events", [])
        status = result.get("overall_status", "QUIET")
        if events:
            print(f"🚨 {len(events)} events ({status})")
        else:
            print(f"📭 quiet ({status})")
    else:
        print("⚠️  parse error")
        if response:
            raw_path = ALERTS_DIR / f"raw_scan_{company_name[:20].replace(' ', '_')}_{datetime.utcnow().strftime('%H%M')}.txt"
            raw_path.write_text(response)
        result = {"company": company_name, "events": [], "overall_status": "ERROR"}

    result["scanned_at"] = datetime.utcnow().isoformat()
    result["category"] = category
    return result


def scan_industry(vertical, state, max_results=10):
    """Scan for industry-wide trigger events."""

    system_prompt = """You are a B2B sales intelligence analyst for Nexus Agriscience, a botanical terpene supplier.
Search for recent industry news and events that create sales opportunities.
Return ONLY valid JSON — no other text."""

    user_prompt = f"""Search for recent events in the {vertical} industry in {state} from the past 30 days.

Search for:
1. "{vertical} {state} news 2026"
2. "cannabis extraction {state} new license"
3. "{state} cannabis industry expansion"
4. "terpene" + "{state}" recent news
5. Cannabis industry events near {state}

Find events that create terpene sales opportunities:
{{
  "vertical": "{vertical}",
  "state": "{state}",
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "industry_events": [
    {{
      "type": "NEW_COMPANY|REGULATION|MARKET_SHIFT|TRADE_SHOW|COMPETITOR_NEWS|SUPPLY_CHAIN",
      "headline": "",
      "detail": "",
      "source_url": "",
      "companies_affected": ["Company A", "Company B"],
      "urgency": "HIGH|MEDIUM|LOW",
      "opportunity": "How this creates a terpene sales opportunity",
      "recommended_action": "What to do about it"
    }}
  ],
  "upcoming_trade_shows": [
    {{
      "name": "",
      "date": "",
      "location": "",
      "relevance": "Why attend for terpene sales"
    }}
  ],
  "market_sentiment": "GROWING|STABLE|CONTRACTING",
  "key_insight": "Most important takeaway for terpene sales"
}}"""

    print(f"    🔍 Scanning industry: {vertical} in {state}...", end=" ", flush=True)
    response = call_claude(system_prompt, user_prompt)
    result = parse_json(response)

    if result:
        events = result.get("industry_events", [])
        print(f"📊 {len(events)} events found")
    else:
        print("⚠️")
        result = {"vertical": vertical, "state": state, "industry_events": []}

    result["scanned_at"] = datetime.utcnow().isoformat()
    return result


# ─── COMPETITOR SCAN ────────────────────────────────────────

def scan_competitors():
    """Dedicated competitor intelligence scan."""
    wl = load_watchlist()
    competitors = [c for c in wl.get("companies", []) if c.get("category") == "competitor"]

    if not competitors:
        print("  ⚠️  No competitors in watchlist. Building from defaults...")
        build_watchlist_from_enriched()
        wl = load_watchlist()
        competitors = [c for c in wl.get("companies", []) if c.get("category") == "competitor"]

    system_prompt = """You are a competitive intelligence analyst for Nexus Agriscience (brands: Terpene Belt Farms, Duty Free Terpenes).
Analyze competitor terpene suppliers for actionable intelligence.
Return ONLY valid JSON — no other text."""

    comp_names = [c["name"] for c in competitors]
    comp_list = ", ".join(comp_names)

    user_prompt = f"""Research these terpene supplier competitors: {comp_list}

Search for recent news about each. Focus on:
1. Pricing changes, sales, promotions
2. New product launches
3. Quality issues, recalls, complaints
4. Customer reviews and sentiment
5. Trade show presence
6. Hiring (growing or shrinking?)
7. Website changes, new messaging

Return:
{{
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "competitors": [
    {{
      "name": "",
      "domain": "",
      "recent_activity": "Summary of what they've been up to",
      "pricing_intel": "Any pricing info found",
      "new_products": "New launches",
      "weaknesses": "Problems, complaints, vulnerabilities",
      "strengths": "What they're doing well",
      "threat_level": "HIGH|MEDIUM|LOW",
      "opportunity": "How to exploit against them — specific talking points"
    }}
  ],
  "key_takeaway": "Most important competitive insight for Nexus",
  "displacement_targets": ["Company X customers who might switch because of Y"]
}}"""

    print(f"\n  🔍 Scanning {len(competitors)} competitors...")
    print(f"  ⏳ This takes 60-120 seconds...\n")

    response = call_claude(system_prompt, user_prompt)
    result = parse_json(response)
    if result:
        result["scanned_at"] = datetime.utcnow().isoformat()
    return result


# ─── DAILY BRIEFING ─────────────────────────────────────────

def generate_briefing(scan_results):
    """Generate a morning briefing from scan results."""
    hot_alerts = []
    warm_alerts = []

    for result in scan_results:
        company = result.get("company", "")
        events = result.get("events", [])
        status = result.get("overall_status", "QUIET")

        for event in events:
            alert = {
                "company": company,
                "type": event.get("type", ""),
                "headline": event.get("headline", ""),
                "urgency": event.get("urgency", "LOW"),
                "sales_action": event.get("sales_action", ""),
                "outreach_hook": event.get("outreach_hook", ""),
            }
            if event.get("urgency") == "HIGH":
                hot_alerts.append(alert)
            elif event.get("urgency") == "MEDIUM":
                warm_alerts.append(alert)

    briefing = f"""
{'='*60}
  🌅 NEXUS BDR — DAILY INTELLIGENCE BRIEFING
  {datetime.utcnow().strftime('%A, %B %d, %Y')}
{'='*60}

  📊 Companies Scanned: {len(scan_results)}
  🚨 Hot Alerts: {len(hot_alerts)}
  🟡 Warm Alerts: {len(warm_alerts)}
"""

    if hot_alerts:
        briefing += f"\n  {'─'*50}\n  🔥 HOT — REACH OUT TODAY\n  {'─'*50}\n"
        for a in hot_alerts:
            briefing += f"""
  ▸ {a['company']} [{a['type']}]
    {a['headline']}
    📧 Action: {a['sales_action']}
    💬 Hook: "{a['outreach_hook']}"
"""

    if warm_alerts:
        briefing += f"\n  {'─'*50}\n  🟡 WARM — MONITOR THIS WEEK\n  {'─'*50}\n"
        for a in warm_alerts:
            briefing += f"""
  ▸ {a['company']} [{a['type']}]
    {a['headline']}
    📧 Action: {a['sales_action']}
"""

    quiet = [r for r in scan_results if not r.get("events")]
    if quiet:
        briefing += f"\n  {'─'*50}\n  📭 QUIET ({len(quiet)} companies — no signals)\n  {'─'*50}\n"
        for r in quiet:
            briefing += f"  ▸ {r.get('company', '?')}\n"

    briefing += f"\n{'='*60}\n"
    return briefing


# ─── MAIN ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Trigger Event Monitor — Nexus BDR")
    parser.add_argument("--scan-all", action="store_true", help="Scan entire watchlist")
    parser.add_argument("--scan-list", help="Scan companies from a JSON file")
    parser.add_argument("--scan-company", help="Scan a single company")
    parser.add_argument("--scan-industry", action="store_true", help="Scan industry-wide events")
    parser.add_argument("--scan-competitors", action="store_true", help="Scan competitor terpene suppliers")
    parser.add_argument("--vertical", default="cannabis extraction")
    parser.add_argument("--state", default="CO")
    parser.add_argument("--briefing", action="store_true", help="Generate morning briefing from latest scan")
    parser.add_argument("--build-watchlist", action="store_true", help="Build watchlist from enriched data")
    parser.add_argument("--add-company", help="Add a company to watchlist")
    parser.add_argument("--domain", default="", help="Domain for --add-company")
    parser.add_argument("--max", type=int, default=20, help="Max companies to scan")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  🔔 NEXUS BDR — Trigger Event Monitor")
    print(f"{'='*60}\n")

    if args.build_watchlist:
        added = build_watchlist_from_enriched()
        wl = load_watchlist()
        print(f"  ✅ Watchlist updated: {added} added, {len(wl['companies'])} total")
        for c in wl["companies"]:
            icon = "🎯" if c.get("category") == "competitor" else "👤"
            print(f"     {icon} {c['name']} ({c.get('category', '?')}) — {c.get('domain', 'no domain')}")
        return

    if args.add_company:
        added = add_to_watchlist(args.add_company, args.domain)
        print(f"  {'✅ Added' if added else '⏭️  Already exists'}: {args.add_company}")
        return

    if args.scan_competitors:
        result = scan_competitors()
        if result:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
            path = ALERTS_DIR / f"competitor_intel_{timestamp}.json"
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n  💾 Saved: {path}")

            # Display
            for comp in result.get("competitors", []):
                threat = comp.get("threat_level", "?")
                icon = "🔴" if threat == "HIGH" else "🟡" if threat == "MEDIUM" else "🟢"
                print(f"\n  {icon} {comp['name']} (Threat: {threat})")
                print(f"     Activity: {(comp.get('recent_activity') or 'N/A')[:100]}")
                print(f"     Weakness: {(comp.get('weaknesses') or 'N/A')[:100]}")
                print(f"     Exploit:  {(comp.get('opportunity') or 'N/A')[:100]}")

            takeaway = result.get("key_takeaway", "")
            if takeaway:
                print(f"\n  💡 Key Insight: {takeaway}")
        return

    if args.scan_industry:
        result = scan_industry(args.vertical, args.state)
        if result:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
            path = ALERTS_DIR / f"industry_{args.state.lower()}_{timestamp}.json"
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n  💾 Saved: {path}")

            for event in result.get("industry_events", []):
                icon = "🔴" if event.get("urgency") == "HIGH" else "🟡" if event.get("urgency") == "MEDIUM" else "🔵"
                print(f"\n  {icon} [{event.get('type', '?')}] {event.get('headline', '?')}")
                print(f"     {(event.get('opportunity') or 'N/A')[:100]}")

            shows = result.get("upcoming_trade_shows", [])
            if shows:
                print(f"\n  📅 Upcoming Trade Shows:")
                for s in shows:
                    print(f"     • {s.get('name', '?')} — {s.get('date', '?')} @ {s.get('location', '?')}")
        return

    if args.scan_company:
        result = scan_company(args.scan_company)
        if result:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
            name_slug = args.scan_company[:20].replace(" ", "_").lower()
            path = ALERTS_DIR / f"scan_{name_slug}_{timestamp}.json"
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"\n  💾 Saved: {path}")

            for event in result.get("events", []):
                icon = "🔴" if event.get("urgency") == "HIGH" else "🟡" if event.get("urgency") == "MEDIUM" else "🔵"
                print(f"\n  {icon} [{event['type']}] {event['headline']}")
                print(f"     {event.get('detail', '')[:120]}")
                print(f"     📧 {event.get('sales_action', '')[:120]}")
                print(f"     💬 \"{event.get('outreach_hook', '')}\"")

            print(f"\n  📋 Status: {result.get('overall_status', '?')}")
            print(f"  🎯 Action: {result.get('recommended_action', 'None')}")
        return

    # Scan all or scan list
    scan_targets = []

    if args.scan_all:
        wl = load_watchlist()
        if not wl["companies"]:
            print("  ⚠️  Watchlist empty. Run --build-watchlist first.")
            return
        scan_targets = wl["companies"][:args.max]
        print(f"  📋 Scanning {len(scan_targets)} companies from watchlist\n")

    elif args.scan_list:
        list_path = Path(args.scan_list)
        if list_path.exists():
            with open(list_path) as f:
                data = json.load(f)
            if isinstance(data, list):
                scan_targets = data
            elif "companies" in data:
                scan_targets = data["companies"]
            elif "leads" in data:
                scan_targets = [{"name": l.get("company_name", ""), "domain": l.get("company_domain", l.get("domain", ""))} for l in data["leads"]]
        scan_targets = scan_targets[:args.max]
        print(f"  📋 Scanning {len(scan_targets)} companies from {args.scan_list}\n")

    if not scan_targets:
        parser.print_help()
        return

    # Execute scan
    results = []
    for i, company in enumerate(scan_targets):
        name = company.get("name", company.get("company_name", ""))
        domain = company.get("domain", company.get("company_domain", ""))
        category = company.get("category", "prospect")

        if not name:
            continue

        print(f"  [{i+1}/{len(scan_targets)}]", end="")
        result = scan_company(name, domain, category)
        results.append(result)

        if i < len(scan_targets) - 1:
            time.sleep(3)  # Rate limit

    # Generate briefing
    briefing = generate_briefing(results)
    print(briefing)

    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    results_path = ALERTS_DIR / f"scan_results_{timestamp}.json"
    with open(results_path, "w") as f:
        json.dump({"results": results, "scanned_at": datetime.utcnow().isoformat()}, f, indent=2)

    briefing_path = ALERTS_DIR / f"briefing_{timestamp}.txt"
    briefing_path.write_text(briefing)

    print(f"  💾 Results: {results_path}")
    print(f"  💾 Briefing: {briefing_path}")

    # Update watchlist scan dates
    wl = load_watchlist()
    scanned_names = {r.get("company", "").lower() for r in results}
    for c in wl["companies"]:
        if c["name"].lower() in scanned_names:
            c["last_scanned"] = datetime.utcnow().isoformat()
            matching = [r for r in results if r.get("company", "").lower() == c["name"].lower()]
            if matching:
                c["alert_count"] = c.get("alert_count", 0) + len(matching[0].get("events", []))
    save_watchlist(wl)

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
