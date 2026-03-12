#!/usr/bin/env python3
"""
Deep Sales Intelligence Brief v2 — Nexus BDR Agent
====================================================
Multi-phase research pipeline that builds compounding intelligence.
6 PHASES — each one feeds the next.
"""

import os, sys, json, re, time, argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests"); sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
BRIEFS_DIR = OUTPUT_DIR / "briefs"
REFS_DIR = SKILL_DIR / "references"
for d in [OUTPUT_DIR, BRIEFS_DIR]: d.mkdir(exist_ok=True)

def call_claude(system_prompt, user_prompt, max_tokens=4096):
    headers = {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}
    payload = {"model": MODEL, "max_tokens": max_tokens, "system": system_prompt, "messages": [{"role": "user", "content": user_prompt}], "tools": [{"type": "web_search_20250305", "name": "web_search"}]}
    for attempt in range(3):
        try:
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=300)
            if resp.status_code == 429:
                wait = 30 * (attempt + 1); print(f"    ⏳ Rate limited, waiting {wait}s..."); time.sleep(wait); continue
            if resp.status_code != 200: print(f"    ❌ Error {resp.status_code}: {resp.text[:300]}"); return ""
            return "\n".join(b["text"] for b in resp.json().get("content", []) if b.get("type") == "text")
        except Exception as e: print(f"    ❌ {e}"); return ""
    return ""

def parse_json(response):
    if not response: return None
    m = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
    if m:
        try: return json.loads(m.group(1).strip())
        except: pass
    depth = 0; start = None
    for i, c in enumerate(response):
        if c == '{':
            if depth == 0: start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try: return json.loads(response[start:i+1])
                except: start = None
    return None

def load_ref(filename, default=""):
    path = REFS_DIR / filename
    return path.read_text() if path.exists() else default

PRODUCT_CATALOG = """
TERPENE BELT FARMS (TBF) — Premium B2B Botanical Terpene Supplier
Position: Premium, science-forward, consultative. For serious operators who need consistency at scale.
Products: 50+ strain-specific botanical terpene profiles, custom blending, bulk formulation
Key strains: OG Kush, Blue Dream, Gelato, Wedding Cake, GSC, Zkittlez, Pineapple Express, Sour Diesel, Jack Herer, Granddaddy Purple
Custom blending: Full R&D team, target profile matching, iterative formulation
Bulk pricing tiers: Sample ($15-25/5ml) | Small ($120-180/100ml) | Medium ($80-140/L) | Large ($60-100/L at 10L+)
Certifications: Food-grade, ISO compliant, full COAs with every batch
Key differentiators: Batch-to-batch consistency (< 3% variance), dedicated account management, R&D support, fast custom turnarounds
Target customer: MSOs, large processors, CPG companies, pharma, white-label partners

DUTY FREE TERPENES (DFT) — Rebellious, Anti-Establishment Terpene Brand
Position: Bold, underground, craft-first. "Terps Without Borders." For artisans who don't follow the herd.
Products: 30+ strain profiles emphasizing exotic/hype strains, smaller batch runs
Key strains: Runtz, Biscotti, Gary Payton, Zoap, Jealousy, Cereal Milk, Pink Rozay, Zushi, Grape Gasoline
Smaller MOQs available: As low as 25ml for new customers
Pricing: Sample ($10-20/5ml) | Small ($90-130/100ml) | Medium ($60-100/L) | Large ($45-80/L)
Key differentiators: Hype strain accuracy, small-batch craft focus, fast shipping, no corporate BS
Target customer: Small extractors, craft brands, solo operators, cart fillers, hemp/CBD brands
"""

COMPETITOR_INTEL = """
PRIMARY COMPETITORS:
True Terpenes: Market leader, premium pricing ($100-180/L). Weaknesses: Corporate/slow, custom orders take 4-6 weeks, quality complaints about consistency.
Abstrax Tech: Science/R&D focused, $120-200/L botanical, $300-500/L CDT. Weaknesses: Expensive, complex ordering, slow response.
Floraplex: Budget ($40-80/L), 200+ strains. Weaknesses: Inconsistent quality, synthetic undertones, no custom blending.
Denver Terpenes: Regional CO, $80-120/L. Weaknesses: Limited profiles, small team, can't scale.
Peak Supply Co: DTC, $50-90/L. Weaknesses: Limited B2B infrastructure.
"""

# ─── PHASE FUNCTIONS ───────────────────────────────────────

def phase_1_recon(company, domain, state, existing):
    ctx = f"\nEXISTING DATA:\n{json.dumps(existing, indent=2, default=str)[:2000]}\n" if existing else ""
    return call_claude(
        "You are a business intelligence analyst. Search aggressively — at least 5 searches. Return ONLY valid JSON.",
        f'Research "{company}" ({domain or "find their website"}) {f"in {state}" if state else ""}.\n{ctx}\n\nSearch: 1) "{company}" overview 2) "{domain or company} website" 3) "{company} about team leadership" 4) "{company} products menu" 5) "{company} news 2025 2026" 6) "{company} revenue funding employees"\n\nReturn:\n{{"company_name":"{company}","domain":"","verified":true,"description":"3-4 detailed sentences","founded":"","headquarters":"","business_model":"How they make money, customers, channels","company_type":"Licensed Operator|MSO|Processor|Manufacturer|Brand|Distributor|Retailer|Lab|Consultant|Hemp Farm|CPG Company","size_estimate":{{"employees":"","revenue_estimate":"","production_scale":"small craft|mid-size|large|enterprise","evidence":""}},"markets":{{"segments":[],"states_active":[],"multi_state":false,"distribution_channels":[]}},"brand_positioning":"","key_products_overview":[],"recent_news":[{{"headline":"","date":"","significance":""}}],"growth_signals":[],"social_media":{{"instagram":"","linkedin":""}},"initial_terpene_relevance":"HIGH|MEDIUM|LOW","key_questions":["what we still need"]}}'
    )

def phase_2_products(company, domain, p1):
    return call_claude(
        "You are a cannabis production analyst specializing in extraction and formulation. Search aggressively. Return ONLY valid JSON.",
        f'Phase 1 data:\n{json.dumps(p1, indent=2, default=str)[:3000]}\n\nNow go DEEP on products/production for "{company}". Search: 1) "{company} products menu" 2) "{company} extraction processing" 3) "{company} vape cartridge edible" 4) "{company} COA lab results" 5) "{company} terpenes ingredients" 6) "{company} review" Reddit Leafly Weedmaps 7) "{company} new product launch 2025 2026"\n\nReturn:\n{{"product_catalog":[{{"product_name":"","product_type":"","description":"","terpene_relevance":"","estimated_volume":"","flavor_profile":""}}],"production_profile":{{"extraction_methods":[],"extraction_evidence":"","production_facility":"","equipment_mentioned":[],"production_volume_estimate":""}},"terpene_analysis":{{"current_terpene_usage":"","evidence_for_usage":[],"terpene_type_used":"Botanical|Synthetic|Cannabis-Derived|Mix|Unknown","current_supplier_clues":[],"products_needing_terpenes":[],"terpene_volume_model":{{"sku_count_needing_terpenes":0,"terpene_per_unit_ml":0.0,"monthly_units":0,"monthly_terpene_liters":0.0,"assumptions":""}}}},"consumer_feedback":{{"flavor_mentions":"","quality_perception":"","complaints":"","opportunities":""}},"product_match_opportunities":[{{"their_product":"","their_strain":"","our_match":"Specific TBF or DFT profile","match_rationale":"","volume_monthly_ml":0,"talking_point":""}}]}}'
    )

def phase_3_people(company, domain, p1, p2):
    size_info = json.dumps(p1.get("size_estimate", {}), default=str)
    terp_products = json.dumps(p2.get("terpene_analysis", {}).get("products_needing_terpenes", []), default=str)
    return call_claude(
        "You are a B2B sales intelligence analyst specializing in decision maker identification. Return ONLY valid JSON.",
        f'Company: {p1.get("company_name", company)} | Domain: {p1.get("domain", domain)} | Type: {p1.get("company_type", "?")} | Size: {size_info}\nProducts needing terpenes: {terp_products}\n\nFind people who make terpene purchasing decisions. Search: 1) "{company} team leadership about us" 2) "{company}" LinkedIn 3) "{company} CEO founder owner" 4) "{company} head of production extraction formulation" 5) Key people names + LinkedIn profiles 6) "{company}" conference speakers\n\nReturn:\n{{"decision_makers":[{{"name":"","title":"","role_in_purchase":"Final Decision Maker|Champion|Technical Evaluator|Budget Holder|Gatekeeper","seniority":"","linkedin_url":"","email_guess":"","background":"2-3 sentences","communication_style":{{"tone":"Technical|Casual|Formal|Data-driven|Relationship","evidence":"","preferred_approach":""}},"personalization_hooks":[{{"hook":"","source":"","how_to_use":""}}],"potential_objections":[]}}],"email_pattern":{{"detected_pattern":"","confidence":"HIGH|MEDIUM|LOW"}},"organizational_dynamics":{{"decision_process":"","buying_committee":"","budget_authority":""}},"relationship_opportunities":{{"trade_shows":[],"warm_intro_paths":[]}}}}'
    )

def phase_4_competitive(company, domain, p1, p2, p3):
    clues = json.dumps(p2.get("terpene_analysis", {}).get("current_supplier_clues", []), default=str)
    usage = p2.get("terpene_analysis", {}).get("current_terpene_usage", "Unknown")
    return call_claude(
        f"You are a competitive intelligence analyst for a botanical terpene company.\n\n{COMPETITOR_INTEL}\n\nReturn ONLY valid JSON.",
        f'Target: {p1.get("company_name", company)} ({p1.get("domain", domain)})\nTerpene usage: {usage}\nSupplier clues: {clues}\n\nSearch: 1) "{company} terpenes" 2) "{company}" + "True Terpenes" or "Abstrax" or "Floraplex" 3) "{company} COA" 4) "{company}" Instagram tagged suppliers 5) "{company} supplier vendor partner" 6) Reddit forums "{company} terpenes"\n\nReturn:\n{{"current_supplier_assessment":{{"most_likely_supplier":"","evidence":[],"relationship_strength":"","satisfaction_signals":{{"positive":[],"negative":[]}},"switching_barriers":[],"switching_triggers":[]}},"displacement_strategy":{{"primary_angle":"","supporting_angles":[],"sample_strategy":"","risk_reversal":"","timeline":""}},"pricing_intelligence":{{"their_likely_current_cost":"","our_pricing_tier":"","advantage_or_gap":"","value_justification":""}}}}'
    )

def phase_5_financial(company, p1, p2, p4):
    vol = json.dumps(p2.get("terpene_analysis", {}).get("terpene_volume_model", {}), default=str)
    pricing = json.dumps(p4.get("pricing_intelligence", {}), default=str)
    size = json.dumps(p1.get("size_estimate", {}), default=str)
    matches = json.dumps(p2.get("product_match_opportunities", [])[:5], default=str)
    return call_claude(
        f"You are a B2B sales financial analyst. Build precise bottom-up deal models. Show your math.\n\nOur pricing:\n{PRODUCT_CATALOG}\n\nReturn ONLY valid JSON.",
        f'Build deal model for: {p1.get("company_name", company)}\nSize: {size}\nVolume model: {vol}\nProduct matches: {matches}\nPricing intel: {pricing}\nGrowth signals: {json.dumps(p1.get("growth_signals", []), default=str)}\n\nReturn:\n{{"deal_model":{{"scenario_conservative":{{"description":"Start with 1-2 SKUs","initial_order_liters":0.0,"initial_order_value":"$","monthly_run_rate_value":"$","annual_value":"$","assumptions":[]}},"scenario_likely":{{"description":"Convert main lines","initial_order_liters":0.0,"initial_order_value":"$","monthly_run_rate_value":"$","annual_value":"$","assumptions":[]}},"scenario_upside":{{"description":"Full conversion + custom","initial_order_liters":0.0,"initial_order_value":"$","monthly_run_rate_value":"$","annual_value":"$","assumptions":[]}},"weighted_expected_value":"$"}},"sales_cycle":{{"estimated_days_to_close":0,"stage_breakdown":[{{"stage":"","days":0,"actions":""}}],"acceleration_levers":[]}},"budget_timing":{{"likely_budget_cycle":"","reorder_frequency":"","optimal_approach_window":""}},"expansion_roadmap":{{"year_1":"","year_2":"","year_3":"","lifetime_value_3yr":"$"}}}}'
    )

def phase_6_synthesis(company, phases):
    return call_claude(
        f"You are the world's best B2B terpene sales strategist. Synthesize 5 phases of deep research into a battle plan. CRITICAL: Every email MUST reference specific details from the research — actual product names, actual people, actual news. Generic emails are unacceptable.\n\nProduct knowledge:\n{PRODUCT_CATALOG}\n\nReturn ONLY valid JSON.",
        f'PHASE 1 RECON:\n{json.dumps(phases.get("phase_1",{}), indent=2, default=str)[:2000]}\n\nPHASE 2 PRODUCTS:\n{json.dumps(phases.get("phase_2",{}), indent=2, default=str)[:2500]}\n\nPHASE 3 PEOPLE:\n{json.dumps(phases.get("phase_3",{}), indent=2, default=str)[:2000]}\n\nPHASE 4 COMPETITIVE:\n{json.dumps(phases.get("phase_4",{}), indent=2, default=str)[:2000]}\n\nPHASE 5 FINANCIAL:\n{json.dumps(phases.get("phase_5",{}), indent=2, default=str)[:1500]}\n\nSynthesize into:\n{{"executive_summary":{{"one_liner":"","recommended_brand":"TBF|DFT","priority_score":0,"confidence_in_close":"HIGH|MEDIUM|LOW","expected_annual_value":"$","key_insight":""}},"objection_playbook":[{{"objection":"exact words","probability":"","context":"why they\'d say this","response_script":"exact words back","proof_point":"","pivot_to":""}}],"outreach_sequence":[{{"touch_number":1,"day":0,"channel":"Email","target_person":"Name — Title","strategic_approach":"","subject_line":"References something specific","email_body":"FULL email under 150 words. Must reference: their actual product names, a specific challenge from research, a specific TBF/DFT match. No generic openers. Start with VALUE. Every sentence earns the next.","why_this_works":""}},{{"touch_number":2,"day":3,"channel":"LinkedIn","target_person":"","connection_note":"Short, personal","why_this_works":""}},{{"touch_number":3,"day":7,"channel":"Email","target_person":"","strategic_approach":"Challenger — present insight they haven\'t considered","subject_line":"","email_body":"Different angle. Challenge their current approach.","why_this_works":""}},{{"touch_number":4,"day":12,"channel":"Email","target_person":"","strategic_approach":"Social proof + sample offer","subject_line":"","email_body":"Offer specific sample kit matched to their products.","why_this_works":""}},{{"touch_number":5,"day":18,"channel":"Email","strategic_approach":"Pattern interrupt","subject_line":"","email_body":"2-3 sentences max. Share industry insight.","why_this_works":""}}],"sample_kit_recommendation":{{"profiles_to_send":[{{"our_profile":"","maps_to_their_product":"","why":""}}],"kit_size":"","custom_note":"handwritten feel","follow_up_timing":""}},"risk_and_contingency":{{"deal_killers":[],"mitigation":[{{"risk":"","strategy":"","contingency":""}}],"disqualification_criteria":"","fallback_strategy":""}},"action_plan":{{"today":[],"this_week":[],"next_30_days":[],"success_milestones":[{{"milestone":"","target_date":"","measure":""}}]}}}}',
        max_tokens=6000
    )

# ─── MAIN PIPELINE ─────────────────────────────────────────

def generate_brief(company, domain="", state="", brand="auto", existing_data=None):
    print(f"\n  {'━'*60}")
    print(f"  🧠 DEEP SALES INTELLIGENCE BRIEF v2")
    print(f"  Target: {company}")
    print(f"  {'━'*60}")
    print(f"  6-phase compounding research pipeline\n")

    all_phases = {}
    timings = {}

    phases_config = [
        ("phase_1", "COMPANY RECON", "Broad intelligence gathering", lambda: phase_1_recon(company, domain, state, existing_data)),
        ("phase_2", "PRODUCT & PRODUCTION", "Products, extraction, terpene usage", lambda: phase_2_products(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}))),
        ("phase_3", "PEOPLE & RELATIONSHIPS", "Decision makers, org dynamics", lambda: phase_3_people(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}), all_phases.get("phase_2",{}))),
        ("phase_4", "COMPETITIVE & SUPPLIER INTEL", "Current suppliers, displacement", lambda: phase_4_competitive(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}), all_phases.get("phase_2",{}), all_phases.get("phase_3",{}))),
        ("phase_5", "FINANCIAL MODELING", "Bottom-up deal model", lambda: phase_5_financial(company, all_phases.get("phase_1",{}), all_phases.get("phase_2",{}), all_phases.get("phase_4",{}))),
        ("phase_6", "STRATEGY & OUTREACH", "Battle plan synthesis", lambda: phase_6_synthesis(company, all_phases)),
    ]

    for i, (key, title, desc, fn) in enumerate(phases_config):
        connector = "┌" if i == 0 else "└" if i == len(phases_config)-1 else "├"
        t0 = time.time()
        print(f"  {connector}─ Phase {i+1}: {title}")
        print(f"  │  {desc}...")
        raw = fn()
        parsed = parse_json(raw)
        if not parsed:
            print(f"  │  ⚠️  Parse failed, continuing with limited data")
            parsed = {}
            if raw:
                (BRIEFS_DIR / f"raw_p{i+1}_{company[:15].replace(' ','_')}.txt").write_text(raw)
        all_phases[key] = parsed
        timings[key] = time.time() - t0
        print(f"  │  ✅ Complete ({timings[key]:.0f}s)")

        # Phase-specific status output
        if key == "phase_1":
            print(f"  │  {parsed.get('description','N/A')[:100]}...")
            print(f"  │  Type: {parsed.get('company_type','?')} | Relevance: {parsed.get('initial_terpene_relevance','?')}")
        elif key == "phase_2":
            prods = parsed.get("product_catalog", [])
            vol = parsed.get("terpene_analysis",{}).get("terpene_volume_model",{})
            print(f"  │  Products: {len(prods)} | Terpene vol: {vol.get('monthly_terpene_liters','?')}L/mo")
        elif key == "phase_3":
            dms = parsed.get("decision_makers", [])
            print(f"  │  Decision makers: {len(dms)}")
            for dm in dms[:2]: print(f"  │    • {dm.get('name','?')} — {dm.get('title','?')}")
        elif key == "phase_4":
            s = parsed.get("current_supplier_assessment",{})
            print(f"  │  Likely supplier: {s.get('most_likely_supplier','?')}")
        elif key == "phase_5":
            likely = parsed.get("deal_model",{}).get("scenario_likely",{})
            print(f"  │  Likely annual: {likely.get('annual_value','?')}")
        elif key == "phase_6":
            es = parsed.get("executive_summary",{})
            print(f"  │  Score: {es.get('priority_score','?')}/100 | Brand: {es.get('recommended_brand','?')}")

        print(f"  │")
        if i < len(phases_config) - 1: time.sleep(2)

    total = sum(timings.values())
    print(f"\n  ⏱️  Total: {total:.0f}s ({total/60:.1f} min)")

    # Save
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    slug = company[:30].replace(" ", "_").lower()

    json_path = BRIEFS_DIR / f"brief_{slug}_{ts}.json"
    with open(json_path, "w") as f:
        json.dump({"metadata": {"company": company, "generated_at": datetime.utcnow().isoformat(), "total_seconds": total, "timings": timings}, "phases": all_phases}, f, indent=2)

    # Quick summary display
    p6 = all_phases.get("phase_6", {})
    es = p6.get("executive_summary", {})
    print(f"\n  {'━'*60}")
    print(f"  💡 {es.get('one_liner', 'N/A')}")
    print(f"  🏷️  {es.get('recommended_brand','?')} | Score: {es.get('priority_score','?')}/100 | Close: {es.get('confidence_in_close','?')}")
    print(f"  💰 {es.get('expected_annual_value','?')}")
    print(f"  🔑 {es.get('key_insight','N/A')[:150]}")

    seq = p6.get("outreach_sequence", [])
    if seq:
        t1 = seq[0]
        print(f"\n  📧 First touch → {t1.get('target_person','?')}")
        print(f"  Subject: {t1.get('subject_line','?')}")
        body = t1.get("email_body", "")
        if body: print(f"  {body[:300]}...")

    plan = p6.get("action_plan", {})
    today = plan.get("today", [])
    if today:
        print(f"\n  ⚡ TODAY:")
        for a in today[:3]: print(f"  → {a}")

    print(f"\n  💾 {json_path}")
    print(f"\n  {'━'*60}\n")
    return all_phases

def main():
    parser = argparse.ArgumentParser(description="Deep Sales Intelligence Brief v2")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--domain", default="")
    parser.add_argument("--state", default="")
    parser.add_argument("--brand", default="auto")
    parser.add_argument("--from-lead", help="Generate from enriched file")
    parser.add_argument("--lead-index", type=int, default=0)
    parser.add_argument("--batch", help="Batch for top N")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY: print("  ❌ Set ANTHROPIC_API_KEY"); sys.exit(1)

    if args.batch:
        with open(args.batch) as f: data = json.load(f)
        leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
        leads = sorted(leads, key=lambda l: l.get("nexus_lead_score", 0), reverse=True)[:args.top]
        for i, lead in enumerate(leads):
            print(f"\n  ═══ [{i+1}/{len(leads)}] {lead.get('company_name','?')} ═══")
            generate_brief(lead.get("company_name","?"), lead.get("company_domain", lead.get("domain","")), lead.get("state",""), args.brand, lead)
            if i < len(leads)-1: time.sleep(10)
    elif args.from_lead:
        with open(args.from_lead) as f: data = json.load(f)
        leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
        lead = leads[args.lead_index]
        generate_brief(lead.get("company_name","?"), lead.get("company_domain", lead.get("domain","")), lead.get("state",""), args.brand, lead)
    elif args.company:
        generate_brief(args.company, args.domain, args.state, args.brand)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
