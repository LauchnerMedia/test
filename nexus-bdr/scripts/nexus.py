#!/usr/bin/env python3
"""
Nexus Master Orchestrator v7 — The Brain
==========================================
Single entry point for the entire Nexus BDR system.
Coordinates all agents, manages credits, generates daily briefings.

Commands:
    python3 nexus.py sweep              # Free intel sweep (Reddit, FDA, news, competitors)
    python3 nexus.py brief "Company"    # Run Sales Intel Brief on target
    python3 nexus.py brief-batch 5      # Brief top 5 prospects from pipeline
    python3 nexus.py video "Company"    # Generate HeyGen scripts from brief
    python3 nexus.py triggers           # Scan for buying signals across watchlist
    python3 nexus.py daily              # Full daily briefing (sweep + triggers + priorities)
    python3 nexus.py pipeline           # Show pipeline status and priorities
    python3 nexus.py status             # System health check
    python3 nexus.py costs              # Show API spend and budget remaining
    python3 nexus.py demo               # Full demo run (for Shareef presentation)

Architecture:
    ┌─────────────────────────────────────────────┐
    │              NEXUS ORCHESTRATOR              │
    │  (this file — coordinates everything)       │
    ├─────────────────────────────────────────────┤
    │  FREE INTEL          │  PAID INTEL          │
    │  ─────────           │  ──────────          │
    │  Reddit Harvester    │  Sales Intel Brief   │
    │  FDA Scanner         │  Social Analysis     │
    │  News Monitor        │  Trigger Analysis    │
    │  Competitor Watch    │  HeyGen Scripts      │
    │  SEC EDGAR           │  Custom Research     │
    ├─────────────────────────────────────────────┤
    │  PIPELINE            │  CREATIVE            │
    │  ────────            │  ────────            │
    │  Apollo Importer     │  HeyGen Templates    │
    │  Scoring Engine      │  Email Sequences     │
    │  Hunter Verifier     │  Sample Kit Builder  │
    │  GHL Sync            │  Brief → Docx Gen    │
    ├─────────────────────────────────────────────┤
    │  MODEL ROUTER                               │
    │  Anthropic (premium) ↔ OpenRouter (cheap)   │
    │  Cost tracking + budget management          │
    └─────────────────────────────────────────────┘

Environment:
    ANTHROPIC_API_KEY     — Required for premium calls + web search
    OPENROUTER_API_KEY    — Optional, enables 10-50x cost reduction
    HUNTER_API_KEY        — Email verification
    GHL_API_KEY           — CRM sync
    HEYGEN_API_KEY        — Video generation (optional)
"""

import os, sys, json, re, time, argparse, glob
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs"
BRIEFS_DIR = OUTPUT_DIR / "briefs"
INTEL_DIR = OUTPUT_DIR / "free_intel"
ALERTS_DIR = OUTPUT_DIR / "alerts"
VIDEOS_DIR = OUTPUT_DIR / "heygen_scripts"
REPORTS_DIR = OUTPUT_DIR / "daily_reports"
CONFIG_DIR = SCRIPT_DIR / "config"

for d in [OUTPUT_DIR, BRIEFS_DIR, INTEL_DIR, ALERTS_DIR, VIDEOS_DIR, REPORTS_DIR, CONFIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# SYSTEM STATUS
# ═══════════════════════════════════════════════════════════

def check_status():
    """Full system health check."""
    print(f"\n{'═'*60}")
    print(f"  NEXUS BDR SYSTEM STATUS")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═'*60}\n")

    # API Keys
    apis = {
        "ANTHROPIC_API_KEY": ("Claude AI (Premium)", True),
        "OPENROUTER_API_KEY": ("OpenRouter (Cost Opt)", False),
        "HUNTER_API_KEY": ("Hunter.io (Email)", False),
        "GHL_API_KEY": ("GoHighLevel (CRM)", False),
        "HEYGEN_API_KEY": ("HeyGen (Video)", False),
    }

    print("  API CONNECTIONS:")
    for key, (label, required) in apis.items():
        val = os.getenv(key, "")
        if val:
            print(f"  ✅ {label}: {key[:15]}...{val[:8]}...")
        elif required:
            print(f"  ❌ {label}: NOT SET (required)")
        else:
            print(f"  · {label}: not configured (optional)")

    # Agent scripts
    print(f"\n  AGENT FLEET:")
    agents = [
        ("free_intel_sources.py", "Free Intel Harvester"),
        ("model_router.py", "Model Router"),
        ("sales_intel_brief_v4.py", "Sales Intel Brief v4"),
        ("heygen_scripts.py", "HeyGen Script Generator"),
        ("trigger_monitor.py", "Trigger Monitor"),
        ("social_intel_engine_v2.py", "Social Intel Engine v2"),
        ("customer_intel.py", "Customer Intelligence"),
        ("csv_importer_v2.py", "CSV Importer"),
        ("ghl_sync_v2.py", "GHL Sync"),
        ("enrich_pipeline_v2.py", "Enrichment Pipeline"),
    ]

    for script, label in agents:
        path = SCRIPT_DIR / script
        if not path.exists():
            path = OUTPUT_DIR / script
        if path.exists():
            lines = sum(1 for _ in open(path))
            print(f"  ✅ {label}: {script} ({lines}L)")
        else:
            print(f"  · {label}: {script} (not found)")

    # Pipeline data
    print(f"\n  PIPELINE DATA:")
    scored = list(OUTPUT_DIR.glob("scored_apollo_*.json"))
    briefs = list(BRIEFS_DIR.glob("brief_*.json"))
    intel = list(INTEL_DIR.glob("*.json"))
    alerts = list(ALERTS_DIR.glob("*.json"))

    print(f"  · Scored prospect files: {len(scored)}")
    print(f"  · Company briefs: {len(briefs)}")
    print(f"  · Intel reports: {len(intel)}")
    print(f"  · Alert files: {len(alerts)}")

    # Latest brief
    if briefs:
        latest = max(briefs, key=lambda p: p.stat().st_mtime)
        with open(latest) as f:
            data = json.load(f)
        company = data.get("metadata", {}).get("company", "?")
        phases = data.get("phases", {})
        filled = sum(1 for p in phases.values() if isinstance(p, dict) and len(p) > 1)
        print(f"  · Latest brief: {company} ({filled}/6 phases)")

    print(f"\n{'═'*60}\n")


# ═══════════════════════════════════════════════════════════
# PIPELINE VIEW
# ═══════════════════════════════════════════════════════════

def show_pipeline():
    """Show current pipeline status and priorities."""
    print(f"\n{'═'*60}")
    print(f"  NEXUS PIPELINE STATUS")
    print(f"{'═'*60}\n")

    # Load scored data
    scored_files = sorted(OUTPUT_DIR.glob("scored_apollo_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not scored_files:
        print("  No scored pipeline data found.")
        print("  Run: python3 csv_importer_v2.py --file <apollo_export.csv>")
        return

    with open(scored_files[0]) as f:
        data = json.load(f)

    leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))

    # Company-level aggregation
    companies = {}
    for lead in leads:
        co = lead.get("company_name", "Unknown")
        if co not in companies:
            companies[co] = {
                "contacts": 0,
                "avg_score": 0,
                "top_score": 0,
                "top_person": "",
                "domain": lead.get("company_domain", lead.get("domain", "")),
                "emails_verified": 0,
                "scores": [],
            }
        companies[co]["contacts"] += 1
        score = lead.get("nexus_lead_score", 0)
        companies[co]["scores"].append(score)
        if score > companies[co]["top_score"]:
            companies[co]["top_score"] = score
            companies[co]["top_person"] = f"{lead.get('first_name','')} {lead.get('last_name','')}"
        if lead.get("email_verified") or lead.get("hunter_status") == "valid":
            companies[co]["emails_verified"] += 1

    for co, d in companies.items():
        d["avg_score"] = round(sum(d["scores"]) / len(d["scores"]), 1)
        del d["scores"]

    # Sort by avg score
    ranked = sorted(companies.items(), key=lambda x: x[1]["avg_score"], reverse=True)

    # Tier assignment
    hot = [(n, d) for n, d in ranked if d["avg_score"] >= 80]
    warm = [(n, d) for n, d in ranked if 60 <= d["avg_score"] < 80]
    cool = [(n, d) for n, d in ranked if 40 <= d["avg_score"] < 60]
    cold = [(n, d) for n, d in ranked if d["avg_score"] < 40]

    print(f"  TOTAL: {len(leads)} contacts across {len(companies)} companies")
    print(f"  🔥 Hot: {len(hot)} | 🟠 Warm: {len(warm)} | 🔵 Cool: {len(cool)} | ⚪ Cold: {len(cold)}")

    # Check which have briefs
    existing_briefs = {p.stem.split("_")[1] for p in BRIEFS_DIR.glob("brief_*.json")}

    print(f"\n  TOP 15 ACCOUNTS:")
    print(f"  {'Rank':<5} {'Company':<25} {'Score':<7} {'Contacts':<10} {'Emails':<8} {'Brief':<7}")
    print(f"  {'─'*62}")

    for i, (name, d) in enumerate(ranked[:15], 1):
        slug = name[:20].replace(" ", "_").lower()
        has_brief = "✅" if any(slug in str(b) for b in BRIEFS_DIR.glob("brief_*.json")) else "·"
        tier = "🔥" if d["avg_score"] >= 80 else "🟠" if d["avg_score"] >= 60 else "🔵" if d["avg_score"] >= 40 else "⚪"
        print(f"  {tier} {i:<3} {name:<25} {d['avg_score']:<7} {d['contacts']:<10} {d['emails_verified']:<8} {has_brief}")

    # Action recommendations
    print(f"\n  RECOMMENDED ACTIONS:")
    unbriefed_hot = [(n, d) for n, d in hot if not any(n[:15].replace(" ","_").lower() in str(b) for b in BRIEFS_DIR.glob("brief_*.json"))]
    if unbriefed_hot:
        print(f"  1. Run briefs on {len(unbriefed_hot)} hot accounts without intel:")
        for n, d in unbriefed_hot[:5]:
            print(f"     → python3 sales_intel_brief_v4.py --company \"{n}\" --domain \"{d['domain']}\"")

    no_email_hot = [(n, d) for n, d in hot if d["emails_verified"] == 0]
    if no_email_hot:
        print(f"  2. Verify emails for {len(no_email_hot)} hot accounts with 0 verified emails")

    print(f"\n{'═'*60}\n")


# ═══════════════════════════════════════════════════════════
# DAILY BRIEFING
# ═══════════════════════════════════════════════════════════

def daily_briefing():
    """Generate daily intelligence briefing."""
    print(f"\n{'═'*60}")
    print(f"  NEXUS DAILY INTELLIGENCE BRIEFING")
    print(f"  {datetime.utcnow().strftime('%A, %B %d, %Y — %H:%M UTC')}")
    print(f"{'═'*60}\n")

    report = {
        "date": datetime.utcnow().isoformat(),
        "sections": {},
    }

    # 1. Free intel sweep
    print("  ┌─ Phase 1: FREE INTELLIGENCE SWEEP")
    try:
        # Import and run
        sys.path.insert(0, str(SCRIPT_DIR))
        from free_intel_sources import reddit_harvest, news_scan, competitor_scan
        reddit = reddit_harvest(days_back=3)
        news = news_scan(days_back=3)
        competitors = competitor_scan()
        report["sections"]["reddit"] = {"buying_signals": reddit.get("buying_signals", 0), "top_signals": reddit.get("signals", [])[:5]}
        report["sections"]["news"] = {"articles": news.get("total_found", 0)}
        report["sections"]["competitors"] = {"tracked": len(competitors.get("competitors", {}))}
        print(f"  └─ ✅ Sweep complete\n")
    except Exception as e:
        print(f"  └─ ⚠️  Sweep error: {e}\n")
        report["sections"]["sweep_error"] = str(e)

    # 2. Pipeline priorities
    print("  ┌─ Phase 2: PIPELINE PRIORITIES")
    show_pipeline()
    print(f"  └─ ✅ Pipeline reviewed\n")

    # 3. Check for trigger alerts
    print("  ┌─ Phase 3: TRIGGER ALERTS")
    recent_alerts = sorted(ALERTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if recent_alerts:
        latest_alert = recent_alerts[0]
        age = datetime.utcnow() - datetime.utcfromtimestamp(latest_alert.stat().st_mtime)
        print(f"  │  Latest alert: {latest_alert.name} ({age.days}d ago)")
    else:
        print(f"  │  No trigger alerts on file.")
        print(f"  │  Run: python3 trigger_monitor.py --scan-all")
    print(f"  └─ ✅ Alerts reviewed\n")

    # 4. Budget check
    print("  ┌─ Phase 4: CREDIT BUDGET")
    # Count briefs generated to estimate spend
    brief_count = len(list(BRIEFS_DIR.glob("brief_*.json")))
    est_spend = brief_count * 1.0  # ~$1 per brief on Anthropic, ~$0.15 with OpenRouter
    print(f"  │  Briefs generated: {brief_count}")
    print(f"  │  Estimated spend: ${est_spend:.2f} (Anthropic) / ${brief_count * 0.15:.2f} (OpenRouter)")
    print(f"  └─ ✅ Budget reviewed\n")

    # Save report
    path = REPORTS_DIR / f"daily_{datetime.utcnow().strftime('%Y%m%d')}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"  💾 Daily report: {path}")
    print(f"\n{'═'*60}\n")
    return report


# ═══════════════════════════════════════════════════════════
# DEMO MODE — Full showcase for Shareef
# ═══════════════════════════════════════════════════════════

def demo_mode():
    """Run the full demo sequence for client presentation."""
    print(f"\n{'═'*60}")
    print(f"  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗")
    print(f"  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝")
    print(f"  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗")
    print(f"  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║")
    print(f"  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║")
    print(f"  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝")
    print(f"  BDR INTELLIGENCE SYSTEM — DEMO MODE")
    print(f"{'═'*60}\n")

    print("  This demo shows the full Nexus system in action.")
    print("  Each step demonstrates a different capability.\n")

    steps = [
        ("SYSTEM STATUS", "Health check across all agents and APIs", lambda: check_status()),
        ("PIPELINE OVERVIEW", "138 scored contacts, 22 companies, tier distribution", lambda: show_pipeline()),
        ("FREE INTEL SWEEP", "Reddit buying signals, industry news, competitor monitoring", lambda: _demo_sweep()),
        ("COMPANY BRIEF", "6-phase deep research on a target account", lambda: _demo_brief()),
        ("HEYGEN SCRIPTS", "Personalized video scripts from brief data", lambda: _demo_heygen()),
        ("DAILY BRIEFING", "Synthesized action plan for the sales team", lambda: _demo_daily()),
    ]

    interactive = sys.stdin.isatty()

    for i, (name, desc, fn) in enumerate(steps, 1):
        print(f"\n{'─'*60}")
        print(f"  STEP {i}/{len(steps)}: {name}")
        print(f"  {desc}")
        print(f"{'─'*60}")
        if interactive:
            input(f"\n  Press Enter to run step {i}...")
        else:
            print(f"\n  Running step {i}...")
            time.sleep(1)
        try:
            fn()
        except Exception as e:
            print(f"  ⚠️  Step error: {e}")

    print(f"\n{'═'*60}")
    print(f"  DEMO COMPLETE")
    print(f"  This system is ready to operate for TBF/DFT.")
    print(f"  Full AI-powered BDR function — 15 specialized agents.")
    print(f"{'═'*60}\n")


def _demo_sweep():
    """Demo version of free intel sweep — uses cached data if available."""
    cached = sorted(INTEL_DIR.glob("full_sweep_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if cached:
        print(f"\n  Using cached sweep from {cached[0].name}")
        with open(cached[0]) as f:
            data = json.load(f)
        reddit = data.get("reddit", {})
        print(f"  Reddit: {reddit.get('total_terpene_posts', 0)} posts, {reddit.get('buying_signals', 0)} buying signals")
        signals = reddit.get("signals", [])
        for s in signals[:3]:
            print(f"  → [{s.get('signal_strength','?')}] r/{s.get('subreddit','?')}: {s.get('title','?')[:70]}")
    else:
        print(f"\n  No cached data. Running live sweep...")
        try:
            sys.path.insert(0, str(SCRIPT_DIR))
            from free_intel_sources import run_all_scans
            run_all_scans()
        except Exception as e:
            print(f"  ⚠️  {e}")


def _demo_brief():
    """Demo version of brief — shows existing Mellow Fellow brief."""
    briefs = sorted(BRIEFS_DIR.glob("brief_mellow_fellow*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if briefs:
        with open(briefs[0]) as f:
            data = json.load(f)
        p1 = data.get("phases", {}).get("phase_1", {})
        p4 = data.get("phases", {}).get("phase_4", {})
        print(f"\n  Existing brief: Mellow Fellow")
        print(f"  {p1.get('description', 'N/A')[:200]}")
        supplier = p4.get("current_supplier_assessment", p4.get("current_supplier", {}))
        if supplier:
            print(f"  Supplier: {supplier.get('most_likely_supplier', supplier.get('most_likely', '?'))}")
        print(f"\n  To generate new: python3 sales_intel_brief_v4.py --company \"Company Name\"")
    else:
        print(f"\n  No briefs found. Run: python3 sales_intel_brief_v4.py --company \"Mellow Fellow\"")


def _demo_heygen():
    """Demo HeyGen script generation."""
    print(f"\n  HeyGen Video Script Templates:")
    print(f"  1. Cold Intro — 35-45s, product-specific, peer-to-peer")
    print(f"  2. Challenger — 40-50s, industry insight, thought-provoking")
    print(f"  3. Social Proof — 30-40s, case study reference")
    print(f"  4. Follow-up — 25-35s, sample kit offer")
    print(f"\n  Workflow: Brief data → Script variables → HeyGen API → Personalized video")
    print(f"  Shareef records ONE take. HeyGen swaps company/product/person names.")
    print(f"  Scale: 50+ personalized videos from a single recording session.")
    print(f"\n  Run: python3 heygen_scripts.py --brief outputs/briefs/brief_mellow_fellow_*.json")


def _demo_daily():
    """Demo daily briefing."""
    print(f"\n  Daily Briefing generates:")
    print(f"  1. Overnight buying signals from Reddit/forums")
    print(f"  2. Industry news relevant to prospects")
    print(f"  3. Competitor pricing/product changes")
    print(f"  4. Pipeline priorities (who to call today)")
    print(f"  5. Trigger alerts (prospect events requiring immediate action)")
    print(f"  6. Credit budget status")
    print(f"\n  Run: python3 nexus.py daily")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Nexus BDR System — Master Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  sweep              Free intel sweep (Reddit, FDA, news, competitors)
  brief COMPANY      Run Sales Intel Brief on target company
  brief-batch N      Brief top N prospects from pipeline
  video COMPANY      Generate HeyGen scripts from brief data
  triggers           Scan for buying signals across watchlist
  daily              Full daily intelligence briefing
  pipeline           Show pipeline status and priorities
  status             System health check
  costs              Show API spend and budget
  demo               Full demo run (for client presentation)
        """
    )
    parser.add_argument("command", help="Command to run")
    parser.add_argument("target", nargs="?", default="", help="Target company or parameter")
    parser.add_argument("--domain", default="", help="Company domain")
    parser.add_argument("--state", default="", help="Company state")
    parser.add_argument("--top", type=int, default=5, help="Number of top prospects for batch")

    args = parser.parse_args()
    cmd = args.command.lower()

    if cmd == "status":
        check_status()

    elif cmd == "pipeline":
        show_pipeline()

    elif cmd == "sweep":
        sys.path.insert(0, str(SCRIPT_DIR))
        try:
            from free_intel_sources import run_all_scans
            run_all_scans()
        except ImportError as e:
            print(f"  ⚠️  Could not load free_intel_sources: {e}")
        except Exception as e:
            print(f"  ⚠️  Sweep error: {e}")

    elif cmd == "brief":
        if not args.target:
            print("  Usage: python3 nexus.py brief \"Company Name\" --domain example.com")
            return
        sys.path.insert(0, str(SCRIPT_DIR))
        try:
            from sales_intel_brief_v4 import generate_brief
            generate_brief(args.target, args.domain, args.state)
        except ImportError:
            try:
                from sales_intel_brief_v3 import generate_brief
                print("  (Using v3 brief engine — v4 not available)")
                generate_brief(args.target, args.domain, args.state)
            except ImportError as e:
                print(f"  ⚠️  Could not load brief engine: {e}")
        except Exception as e:
            print(f"  ⚠️  Brief error: {e}")

    elif cmd in ("brief-batch", "batch"):
        sys.path.insert(0, str(SCRIPT_DIR))
        from sales_intel_brief_v4 import generate_brief
        # Find latest scored file
        scored = sorted(OUTPUT_DIR.glob("scored_apollo_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not scored:
            print("  No scored pipeline data found.")
            return
        with open(scored[0]) as f:
            data = json.load(f)
        leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
        # Get unique companies sorted by score
        companies = {}
        for l in leads:
            co = l.get("company_name", "?")
            score = l.get("nexus_lead_score", 0)
            if co not in companies or score > companies[co]["score"]:
                companies[co] = {"score": score, "domain": l.get("company_domain", l.get("domain", "")), "state": l.get("state", "")}
        ranked = sorted(companies.items(), key=lambda x: x[1]["score"], reverse=True)[:args.top]
        print(f"\n  Running briefs on top {len(ranked)} companies:")
        for i, (name, info) in enumerate(ranked, 1):
            print(f"  [{i}] {name} (score: {info['score']})")
        for i, (name, info) in enumerate(ranked, 1):
            print(f"\n  ═══ [{i}/{len(ranked)}] {name} ═══")
            generate_brief(name, info["domain"], info["state"])
            if i < len(ranked):
                print("  Cooling down 15s...")
                time.sleep(15)

    elif cmd == "video":
        if not args.target:
            print("  Usage: python3 nexus.py video \"Company Name\"")
            return
        sys.path.insert(0, str(SCRIPT_DIR))
        # Find brief for this company
        slug = args.target[:20].replace(" ", "_").lower()
        briefs = sorted(BRIEFS_DIR.glob(f"brief_{slug}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not briefs:
            print(f"  No brief found for '{args.target}'. Run brief first.")
            return
        from heygen_scripts import generate_scripts
        generate_scripts(str(briefs[0]))

    elif cmd == "triggers":
        sys.path.insert(0, str(SCRIPT_DIR))
        try:
            from trigger_monitor import scan_all
            scan_all()
        except ImportError as e:
            print(f"  ⚠️  Could not load trigger_monitor: {e}")
        except Exception as e:
            print(f"  ⚠️  Trigger scan error: {e}")

    elif cmd == "daily":
        daily_briefing()

    elif cmd == "costs":
        # Show cost tracking
        cost_files = sorted(OUTPUT_DIR.glob("cost_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if cost_files:
            with open(cost_files[0]) as f:
                data = json.load(f)
            print(data.get("summary", "No cost data"))
        else:
            print("  No cost tracking data. Costs are tracked per-brief in brief JSON files.")
            briefs = list(BRIEFS_DIR.glob("brief_*.json"))
            total = 0
            for b in briefs:
                with open(b) as f:
                    d = json.load(f)
                t = d.get("metadata", {}).get("total_seconds", 0)
                total += t
            print(f"  Briefs: {len(briefs)} | Total compute time: {total/60:.1f} min")

    elif cmd == "demo":
        demo_mode()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
