#!/usr/bin/env python3
"""
Deep Sales Intelligence Brief v3 — Nexus BDR Agent
=====================================================
6-phase compounding research pipeline with:
  - OpenRouter model routing (10-50x cheaper)
  - Corrected CDT pricing ($5,000-8,000/L)
  - Better rate limit handling (adaptive delays)
  - Improved JSON parsing with fallbacks
  - Cost tracking per phase

Usage:
    python3 sales_intel_brief_v3.py --company "Mellow Fellow" --domain "mellowfellow.fun" --state "FL"
    python3 sales_intel_brief_v3.py --batch outputs/scored_apollo_*.json --top 5

Requires: ANTHROPIC_API_KEY and/or OPENROUTER_API_KEY
"""

import os, sys, json, re, time, argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests"); sys.exit(1)

# Add parent to path for model_router import
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from model_router import routed_call, parse_json_response, tracker, check_available_providers
except ImportError:
    print("  ⚠️  model_router.py not found in scripts/. Using Anthropic direct.")
    # Inline fallback
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    def routed_call(phase, sys_p, user_p, max_tokens=None, tools=None, retries=2):
        headers = {"Content-Type":"application/json","x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01"}
        payload = {"model":"claude-sonnet-4-5-20250929","max_tokens":max_tokens or 4096,"system":sys_p,"messages":[{"role":"user","content":user_p}]}
        if tools: payload["tools"] = tools
        for attempt in range(retries+1):
            try:
                r = requests.post("https://api.anthropic.com/v1/messages",headers=headers,json=payload,timeout=300)
                if r.status_code == 429:
                    wait = 20*(attempt+1); print(f"    ⏳ Rate limited, waiting {wait}s..."); time.sleep(wait); continue
                if r.status_code != 200: print(f"    ❌ {r.status_code}: {r.text[:200]}"); return ""
                return "\n".join(b["text"] for b in r.json().get("content",[]) if b.get("type")=="text")
            except Exception as e: print(f"    ❌ {e}"); return ""
        return ""
    def parse_json_response(text):
        if not text: return None
        m = re.search(r'```json\s*\n?(.*?)\n?```', text, re.DOTALL)
        if m:
            try: return json.loads(m.group(1).strip())
            except: pass
        depth=0;start=None
        for i,c in enumerate(text):
            if c=='{':
                if depth==0:start=i
                depth+=1
            elif c=='}':
                depth-=1
                if depth==0 and start is not None:
                    try: return json.loads(text[start:i+1])
                    except: start=None
        return None
    class DummyTracker:
        def summary(self): return ""
        def save(self,p): pass
    tracker = DummyTracker()
    def check_available_providers(): return True

OUTPUT_DIR = SKILL_DIR / "outputs"
BRIEFS_DIR = OUTPUT_DIR / "briefs"
REFS_DIR = SKILL_DIR / "references"
for d in [OUTPUT_DIR, BRIEFS_DIR]: d.mkdir(exist_ok=True)

# ── CORRECTED PRODUCT & PRICING DATA ──

PRODUCT_CATALOG = """
TERPENE BELT FARMS (TBF) — Premium B2B Cannabis Essential Oil Supplier
Position: Premium, science-forward, enterprise. Largest cannabis extraction facility in the US.
Products: Steam-distilled cannabis essential oils, strain-specific profiles, custom blending
Process: Fresh Never Frozen® — harvest to oil in 60 minutes, preserving 98% volatile terpenes
Scale: 260 acres, 10 tons/hour processing, 200,000 lbs/day harvest capacity
Key strains: OG Kush, Blue Dream, Gelato, Wedding Cake, GSC, Zkittlez, Pineapple Express, Sour Diesel
Custom blending: Full R&D team, target profile matching, iterative formulation
Pricing: Enterprise volume deals negotiated per client. Competitive with top-tier CDT suppliers.
Certifications: Food-grade, ISO compliant, full COAs with every batch, Farm Bill compliant
Key differentiators: Batch-to-batch consistency (< 3% variance), vertically integrated soil-to-oil, dedicated account management
Target customer: MSOs, large processors, CPG companies, national brands, white-label partners

DUTY FREE TERPENES (DFT) — Rebellious, Anti-Establishment Botanical Terpene Brand
Position: Bold, underground, craft-first. "Terps Without Borders." For brands that don't follow the herd.
Products: 30+ strain-specific botanical terpene profiles emphasizing exotic/hype strains
Key strains: Runtz, Biscotti, Gary Payton, Zoap, Jealousy, Cereal Milk, Pink Rozay, Zushi
MOQs: As low as 25ml for sampling. Volume pricing from 100ml+.
Pricing: $45-80/L depending on volume and complexity
Key differentiators: Hype strain accuracy, small-batch craft focus, fast shipping, no corporate BS
Target customer: Small-mid extractors, craft brands, cart fillers, hemp/CBD brands, emerging operators
"""

COMPETITOR_INTEL = """
PRIMARY COMPETITORS & PRICING:
True Terpenes: Market leader botanical, $80-150/L botanical, $2,000-4,000/L CDT. Slow custom (4-6 weeks). Quality complaints.
Abstrax Tech: Science/R&D focused, $120-200/L botanical, $3,000-6,000/L CDT. Expensive, complex ordering.
Floraplex: Budget botanical $40-80/L, 200+ strains. Inconsistent quality, synthetic undertones.
Denver Terpenes: Regional CO, $60-120/L. Limited profiles, can't scale.
Peak Supply Co: DTC, $50-90/L. Limited B2B infrastructure.

CDT MARKET PRICING (Cannabis Derived Terpenes):
Premium single-source CDT: $5,000-8,000/L (live resin / fresh frozen extraction)
Mid-grade CDT blends: $2,000-4,000/L
Budget CDT (trim-run / mixed source): $800-2,000/L
Self-extraction cost (if vertically integrated): $1,500-3,000/L (amortized equipment, labor, biomass, facility)

KEY INSIGHT: Botanical terpenes at $45-80/L vs CDT at $2,000-8,000/L represents a 25-100x cost difference.
For products where consumers cannot distinguish CDT vs botanical (edibles, beverages, topicals, wellness),
botanical terpenes deliver equivalent consumer experience at dramatically lower COGS.
"""

# ── PHASE FUNCTIONS ──

def phase_1_recon(company, domain, state, existing):
    ctx = f"\nEXISTING DATA:\n{json.dumps(existing, indent=2, default=str)[:2000]}\n" if existing else ""
    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    return routed_call("phase_1_recon",
        "You are a business intelligence analyst specializing in the cannabis/hemp industry. Search aggressively — at least 5 different searches. Return ONLY valid JSON, no markdown.",
        f'Research "{company}" ({domain or "find their website"}) {f"in {state}" if state else ""}.\n{ctx}\n\nSearch: 1) "{company}" overview 2) "{domain or company}" website 3) "{company} about team leadership" 4) "{company} products" 5) "{company} news 2025 2026" 6) "{company} revenue funding"\n\nReturn JSON:\n{{"company_name":"{company}","domain":"","verified":true,"description":"3-4 detailed sentences","founded":"","headquarters":"","business_model":"How they make money","company_type":"Licensed Operator|MSO|Processor|Manufacturer|Brand|Distributor|Retailer|Lab|Hemp Farm|CPG","size_estimate":{{"employees":"","revenue_estimate":"","production_scale":"small|mid-size|large|enterprise","evidence":""}},"markets":{{"segments":[],"states_active":[],"multi_state":false,"distribution_channels":[]}},"brand_positioning":"","key_products":[],"recent_news":[{{"headline":"","date":"","significance":""}}],"growth_signals":[],"social_media":{{"instagram":"","linkedin":""}},"terpene_relevance":"HIGH|MEDIUM|LOW","key_questions":[]}}',
        tools=tools
    )

def phase_2_products(company, domain, p1):
    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    return routed_call("phase_2_products",
        "You are a cannabis production analyst specializing in extraction and formulation. Search aggressively. Return ONLY valid JSON, no markdown.",
        f'Phase 1 data:\n{json.dumps(p1, indent=2, default=str)[:3000]}\n\nGo DEEP on products for "{company}". Search their product pages, reviews, COAs.\n\nReturn JSON:\n{{"product_catalog":[{{"name":"","type":"","terpene_relevance":"HIGH|MED|LOW","estimated_volume":"","flavor_profile":""}}],"production_profile":{{"extraction_methods":[],"facility":"","capacity":""}},"terpene_analysis":{{"current_usage":"","terpene_type":"Botanical|CDT|Synthetic|Mix|Unknown","supplier_clues":[],"products_needing_terpenes":[],"volume_estimate_liters_monthly":0}},"consumer_feedback":{{"flavor_mentions":"","quality_issues":"","opportunities":""}},"product_matches":[{{"their_product":"","our_match":"TBF or DFT profile","rationale":"","talking_point":""}}]}}',
        tools=tools
    )

def phase_3_people(company, domain, p1, p2):
    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    return routed_call("phase_3_people",
        "You are a B2B sales intelligence analyst. Find decision makers for terpene purchasing. Return ONLY valid JSON.",
        f'Company: {p1.get("company_name", company)} | Domain: {p1.get("domain", domain)} | Type: {p1.get("company_type", "?")}\n\nFind people who make terpene/ingredient purchasing decisions.\n\nReturn JSON:\n{{"decision_makers":[{{"name":"","title":"","role_in_purchase":"Decision Maker|Champion|Evaluator|Gatekeeper","seniority":"","linkedin_url":"","email_guess":"","background":"","personalization_hooks":[],"objections":[]}}],"email_pattern":{{"pattern":"","confidence":"HIGH|MED|LOW"}},"org_dynamics":{{"decision_process":"","buying_committee":"","budget_authority":""}},"relationship_paths":{{"trade_shows":[],"warm_intros":[]}}}}',
        tools=tools
    )

def phase_4_competitive(company, domain, p1, p2, p3):
    clues = json.dumps(p2.get("terpene_analysis", {}).get("supplier_clues", []), default=str) if p2 else "[]"
    usage = p2.get("terpene_analysis", {}).get("current_usage", "Unknown") if p2 else "Unknown"
    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    return routed_call("phase_4_competitive",
        f"You are a competitive intelligence analyst for a terpene supplier.\n\n{COMPETITOR_INTEL}\n\nReturn ONLY valid JSON.",
        f'Target: {p1.get("company_name", company)} ({p1.get("domain", domain)})\nTerpene usage: {usage}\nSupplier clues: {clues}\n\nSearch for their terpene sourcing, COAs, supplier mentions.\n\nReturn JSON:\n{{"current_supplier":{{"most_likely":"","evidence":[],"satisfaction":{{"positive":[],"negative":[]}},"switching_barriers":[],"switching_triggers":[]}},"displacement":{{"primary_angle":"","supporting_angles":[],"sample_strategy":"","risk_reversal":"","timeline":""}},"pricing":{{"their_likely_cost_per_liter":"","our_price":"","cost_reduction_pct":"","value_justification":""}}}}',
        tools=tools
    )

def phase_5_financial(company, p1, p2, p4):
    vol = json.dumps(p2.get("terpene_analysis", {}).get("volume_estimate_liters_monthly", 0), default=str) if p2 else "0"
    pricing = json.dumps(p4.get("pricing", {}), default=str) if p4 else "{}"
    size = json.dumps(p1.get("size_estimate", {}), default=str) if p1 else "{}"
    matches = json.dumps((p2.get("product_matches", []) if p2 else [])[:5], default=str)
    return routed_call("phase_5_financial",
        f"You are a B2B sales financial analyst. Build precise bottom-up deal models. Show your math.\n\nPricing reference:\n{PRODUCT_CATALOG}\n\nCDT pricing:\n{COMPETITOR_INTEL}\n\nCRITICAL: CDT costs $2,000-8,000/L. Botanical costs $45-80/L. The savings are MASSIVE.\n\nReturn ONLY valid JSON.",
        f'Build deal model for: {p1.get("company_name", company) if p1 else company}\nSize: {size}\nVolume estimate: {vol} L/mo\nProduct matches: {matches}\nPricing intel: {pricing}\nGrowth signals: {json.dumps(p1.get("growth_signals", []) if p1 else [], default=str)}\n\nReturn JSON:\n{{"deal_model":{{"conservative":{{"desc":"Start small","initial_liters":0,"initial_value":"$","monthly_value":"$","annual_value":"$","assumptions":[]}},"likely":{{"desc":"Convert key lines","initial_liters":0,"initial_value":"$","monthly_value":"$","annual_value":"$","assumptions":[]}},"upside":{{"desc":"Full partnership","initial_liters":0,"initial_value":"$","monthly_value":"$","annual_value":"$","assumptions":[]}},"weighted_annual":"$"}},"sales_cycle":{{"days_to_close":0,"stages":[{{"stage":"","days":0,"actions":""}}],"accelerators":[]}},"expansion_path":{{"year_1":"","year_2":"","year_3":"","ltv_3yr":"$"}}}}',
        max_tokens=4096
    )

def phase_6_synthesis(company, phases):
    return routed_call("phase_6_synthesis",
        f"You are the world's best B2B terpene sales strategist. Synthesize 5 phases of research into a battle plan.\n\nCRITICAL RULES:\n1. Every email MUST reference specific details from the research — actual product names, actual people.\n2. Generic emails are unacceptable.\n3. CDT costs $2,000-8,000/L. Our botanical costs $45-80/L. This is a 25-100x cost difference.\n4. Position as formulation partner, not commodity supplier.\n\nProduct knowledge:\n{PRODUCT_CATALOG}\n\nReturn ONLY valid JSON.",
        f'RESEARCH DATA:\nPhase 1: {json.dumps(phases.get("phase_1",{}), indent=1, default=str)[:2500]}\nPhase 2: {json.dumps(phases.get("phase_2",{}), indent=1, default=str)[:2500]}\nPhase 3: {json.dumps(phases.get("phase_3",{}), indent=1, default=str)[:2000]}\nPhase 4: {json.dumps(phases.get("phase_4",{}), indent=1, default=str)[:2000]}\nPhase 5: {json.dumps(phases.get("phase_5",{}), indent=1, default=str)[:1500]}\n\nSynthesize:\n{{"executive_summary":{{"one_liner":"","recommended_brand":"TBF|DFT","priority_score":0,"confidence":"HIGH|MEDIUM|LOW","annual_value":"$","key_insight":""}},"objections":[{{"objection":"","response":"","proof":""}}],"outreach_sequence":[{{"touch":1,"day":0,"channel":"Email","target":"Name","subject":"","body":"FULL email <150 words referencing their actual products","why":""}}],"sample_kit":{{"profiles":[],"kit_size":"","note":"","follow_up":""}},"action_plan":{{"today":[],"this_week":[],"next_30_days":[],"milestones":[{{"milestone":"","target":"","measure":""}}]}}}}',
        max_tokens=6000
    )

# ── MAIN PIPELINE ──

def generate_brief(company, domain="", state="", brand="auto", existing_data=None):
    print(f"\n  {'━'*60}")
    print(f"  🧠 DEEP SALES INTELLIGENCE BRIEF v3")
    print(f"  Target: {company}")
    print(f"  {'━'*60}")
    print(f"  6-phase compounding research | OpenRouter cost optimization\n")

    all_phases = {}
    timings = {}

    phases_config = [
        ("phase_1", "COMPANY RECON", lambda: phase_1_recon(company, domain, state, existing_data)),
        ("phase_2", "PRODUCT & PRODUCTION", lambda: phase_2_products(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}))),
        ("phase_3", "PEOPLE & RELATIONSHIPS", lambda: phase_3_people(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}), all_phases.get("phase_2",{}))),
        ("phase_4", "COMPETITIVE & SUPPLIER", lambda: phase_4_competitive(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}), all_phases.get("phase_2",{}), all_phases.get("phase_3",{}))),
        ("phase_5", "FINANCIAL MODEL", lambda: phase_5_financial(company, all_phases.get("phase_1",{}), all_phases.get("phase_2",{}), all_phases.get("phase_4",{}))),
        ("phase_6", "STRATEGY & OUTREACH", lambda: phase_6_synthesis(company, all_phases)),
    ]

    for i, (phase_key, label, fn) in enumerate(phases_config):
        print(f"  {'┌' if i==0 else '├'}─ Phase {i+1}: {label}")

        start = time.time()
        raw = fn()
        elapsed = time.time() - start
        timings[phase_key] = elapsed

        parsed = parse_json_response(raw) if raw else None
        if parsed:
            all_phases[phase_key] = parsed
            print(f"  │  ✅ Complete ({elapsed:.0f}s)")
            # Phase-specific summaries
            if phase_key == "phase_1":
                desc = parsed.get("description", "")[:80]
                print(f"  │  {desc}...")
                print(f"  │  Type: {parsed.get('company_type','?')} | Relevance: {parsed.get('terpene_relevance','?')}")
            elif phase_key == "phase_2":
                n_products = len(parsed.get("product_catalog", []))
                vol = parsed.get("terpene_analysis", {}).get("volume_estimate_liters_monthly", "?")
                print(f"  │  Products: {n_products} | Est volume: {vol}L/mo")
            elif phase_key == "phase_3":
                n_dm = len(parsed.get("decision_makers", []))
                print(f"  │  Decision makers: {n_dm}")
            elif phase_key == "phase_4":
                supplier = parsed.get("current_supplier", {}).get("most_likely", "?")
                print(f"  │  Likely supplier: {supplier}")
            elif phase_key == "phase_5":
                annual = parsed.get("deal_model", {}).get("weighted_annual", "?")
                print(f"  │  Weighted annual: {annual}")
            elif phase_key == "phase_6":
                es = parsed.get("executive_summary", {})
                print(f"  │  Score: {es.get('priority_score','?')}/100 | Brand: {es.get('recommended_brand','?')}")
        else:
            all_phases[phase_key] = {}
            print(f"  │  ⚠️  Parse failed ({elapsed:.0f}s) — continuing with limited data")

        print(f"  │")
        if i < len(phases_config) - 1:
            # Adaptive delay: longer between phases if we hit rate limits
            delay = 5 if elapsed < 60 else 10 if elapsed < 120 else 15
            time.sleep(delay)

    total = sum(timings.values())
    print(f"\n  ⏱️  Total: {total:.0f}s ({total/60:.1f} min)")
    print(tracker.summary() if hasattr(tracker, 'summary') and callable(tracker.summary) else "")

    # Save
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    slug = re.sub(r'[^a-z0-9]', '_', company[:30].lower())

    json_path = BRIEFS_DIR / f"brief_{slug}_{ts}.json"
    with open(json_path, "w") as f:
        json.dump({
            "metadata": {
                "company": company,
                "domain": domain,
                "version": "v3",
                "generated_at": datetime.utcnow().isoformat(),
                "total_seconds": total,
                "timings": timings,
            },
            "phases": all_phases
        }, f, indent=2, default=str)

    # Display summary
    p6 = all_phases.get("phase_6", {})
    es = p6.get("executive_summary", {})
    print(f"\n  {'━'*60}")
    print(f"  💡 {es.get('one_liner', 'N/A')}")
    print(f"  🏷️  {es.get('recommended_brand','?')} | Score: {es.get('priority_score','?')}/100 | Close: {es.get('confidence','?')}")
    print(f"  💰 {es.get('annual_value','?')}")
    print(f"  🔑 {es.get('key_insight','N/A')[:150]}")

    seq = p6.get("outreach_sequence", [])
    if seq:
        t1 = seq[0]
        print(f"\n  📧 Touch 1 → {t1.get('target','?')}")
        print(f"  Subject: {t1.get('subject','?')}")
        body = t1.get("body", "")
        if body: print(f"  {body[:300]}...")

    plan = p6.get("action_plan", {})
    today = plan.get("today", [])
    if today:
        print(f"\n  ⚡ TODAY:")
        for a in today[:3]: print(f"  → {a}")

    print(f"\n  💾 {json_path}")

    # Save cost tracking
    if hasattr(tracker, 'save'):
        cost_path = BRIEFS_DIR / f"costs_{slug}_{ts}.json"
        tracker.save(str(cost_path))
        print(f"  📊 {cost_path}")

    print(f"\n  {'━'*60}\n")
    return all_phases


def main():
    parser = argparse.ArgumentParser(description="Deep Sales Intelligence Brief v3")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--domain", default="")
    parser.add_argument("--state", default="")
    parser.add_argument("--brand", default="auto")
    parser.add_argument("--batch", help="Batch from scored JSON")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    if not check_available_providers():
        sys.exit(1)

    if args.batch:
        with open(args.batch) as f: data = json.load(f)
        leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
        leads = sorted(leads, key=lambda l: l.get("nexus_lead_score", 0), reverse=True)[:args.top]
        for i, lead in enumerate(leads):
            print(f"\n  ═══ [{i+1}/{len(leads)}] {lead.get('company_name','?')} ═══")
            generate_brief(lead.get("company_name","?"), lead.get("company_domain", lead.get("domain","")), lead.get("state",""), args.brand, lead)
            if i < len(leads)-1: time.sleep(15)  # longer delay between briefs
    elif args.company:
        generate_brief(args.company, args.domain, args.state, args.brand)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
