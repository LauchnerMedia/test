#!/usr/bin/env python3
"""
Deep Sales Intelligence Brief v4 — Nexus BDR Agent
=====================================================
6-phase compounding research pipeline. Cost-optimized:
  - Phases 1-4: Anthropic + web_search (research requires live data)
  - Phase 5: OpenRouter/DeepSeek (financial modeling from existing data)  
  - Phase 6: Anthropic WITHOUT web_search (synthesis — saves 40% on this phase)
  - Adaptive rate limiting (15s between phases, 30s on rate limit)
  - Robust JSON parsing with multiple fallback strategies
  - Auto-generates Word doc brief from JSON output

Cost per brief:
  v2 (all Anthropic + search): ~$1.00-1.50
  v4 (optimized routing):      ~$0.40-0.60

Usage:
    python3 sales_intel_brief_v4.py --company "Mellow Fellow" --domain "mellowfellow.fun" --state "FL"
    python3 sales_intel_brief_v4.py --batch ../outputs/scored_apollo_*.json --top 5

Requires: ANTHROPIC_API_KEY (required) + OPENROUTER_API_KEY (optional, saves ~40%)
"""

import os, sys, json, re, time, argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests"); sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent if (SCRIPT_DIR.parent / "outputs").exists() else SCRIPT_DIR
OUTPUT_DIR = SKILL_DIR / "outputs"
BRIEFS_DIR = OUTPUT_DIR / "briefs"
for d in [OUTPUT_DIR, BRIEFS_DIR]: d.mkdir(exist_ok=True)

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Track costs
costs = {"calls": [], "total_input_tokens": 0, "total_output_tokens": 0, "total_cost_est": 0}

def call_anthropic(system_prompt, user_prompt, max_tokens=4096, use_search=True):
    """Call Anthropic API, optionally with web search."""
    headers = {"Content-Type": "application/json", "x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"}
    payload = {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if use_search:
        payload["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    for attempt in range(3):
        try:
            start = time.time()
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=300)
            dur = time.time() - start

            if resp.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f"    ⏳ Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code != 200:
                print(f"    ❌ Anthropic {resp.status_code}: {resp.text[:200]}")
                return "", 0, 0

            data = resp.json()
            text = "\n".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
            usage = data.get("usage", {})
            in_tok = usage.get("input_tokens", 0)
            out_tok = usage.get("output_tokens", 0)
            # Anthropic pricing: $3/1M input, $15/1M output
            cost = (in_tok * 3.0 + out_tok * 15.0) / 1_000_000

            costs["calls"].append({"provider": "anthropic", "search": use_search, "in": in_tok, "out": out_tok, "cost": cost, "dur": round(dur, 1)})
            costs["total_input_tokens"] += in_tok
            costs["total_output_tokens"] += out_tok
            costs["total_cost_est"] += cost

            label = "Claude+Search" if use_search else "Claude"
            print(f"    ✓ {label} | {in_tok+out_tok:,} tok | ${cost:.4f} | {dur:.0f}s")
            return text, in_tok, out_tok

        except Exception as e:
            print(f"    ❌ {str(e)[:100]}")
            if attempt < 2:
                time.sleep(10)

    return "", 0, 0


def call_openrouter(system_prompt, user_prompt, max_tokens=4096, model="deepseek/deepseek-chat-v3-0324"):
    """Call OpenRouter for cheap inference (no web search)."""
    if not OPENROUTER_KEY:
        # Fallback to Anthropic without search
        return call_anthropic(system_prompt, user_prompt, max_tokens, use_search=False)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://nexus-bdr.local",
        "X-Title": "Nexus BDR Agent",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }

    for attempt in range(3):
        try:
            start = time.time()
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
            dur = time.time() - start

            if resp.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"    ⏳ OpenRouter rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code != 200:
                print(f"    ⚠️  OpenRouter {resp.status_code}: {resp.text[:200]}")
                # Fallback to Anthropic
                print(f"    ↪ Falling back to Anthropic...")
                return call_anthropic(system_prompt, user_prompt, max_tokens, use_search=False)

            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", 0)
            out_tok = usage.get("completion_tokens", 0)
            # DeepSeek pricing: ~$0.14/1M input, ~$0.28/1M output
            cost = (in_tok * 0.14 + out_tok * 0.28) / 1_000_000

            label = model.split("/")[-1][:20]
            costs["calls"].append({"provider": "openrouter", "model": model, "in": in_tok, "out": out_tok, "cost": cost, "dur": round(dur, 1)})
            costs["total_input_tokens"] += in_tok
            costs["total_output_tokens"] += out_tok
            costs["total_cost_est"] += cost

            print(f"    ✓ {label} | {in_tok+out_tok:,} tok | ${cost:.6f} | {dur:.0f}s")
            return text, in_tok, out_tok

        except Exception as e:
            print(f"    ❌ OpenRouter: {str(e)[:100]}")
            if attempt == 2:
                print(f"    ↪ Falling back to Anthropic...")
                return call_anthropic(system_prompt, user_prompt, max_tokens, use_search=False)
            time.sleep(10)

    return "", 0, 0


def parse_json(text):
    """Robust JSON extraction with multiple strategies."""
    if not text:
        return None

    # Strategy 1: ```json blocks
    m = re.search(r'```json\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except:
            pass

    # Strategy 2: Find the largest valid JSON object
    best = None
    best_len = 0
    depth = 0
    start = None
    for i, c in enumerate(text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                candidate = text[start:i+1]
                try:
                    parsed = json.loads(candidate)
                    if len(candidate) > best_len:
                        best = parsed
                        best_len = len(candidate)
                except:
                    pass
                start = None

    if best:
        return best

    # Strategy 3: Try to fix common JSON issues
    # Find anything between first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace >= 0 and last_brace > first_brace:
        candidate = text[first_brace:last_brace+1]
        # Fix trailing commas
        candidate = re.sub(r',\s*}', '}', candidate)
        candidate = re.sub(r',\s*]', ']', candidate)
        try:
            return json.loads(candidate)
        except:
            pass

    return None


# ── PRODUCT & PRICING DATA (CORRECTED) ──

PRODUCT_CATALOG = """
TERPENE BELT FARMS (TBF) — Premium B2B Cannabis Essential Oil Supplier
Position: Premium, science-forward, enterprise. Largest cannabis extraction facility in the US.
Products: Steam-distilled cannabis essential oils, strain-specific profiles, custom blending
Process: Fresh Never Frozen® — harvest to oil in 60 minutes, preserving 98% volatile terpenes
Scale: 260 acres, 10 tons/hour processing, 200,000 lbs/day harvest capacity
Key strains: OG Kush, Blue Dream, Gelato, Wedding Cake, GSC, Zkittlez, Pineapple Express, Sour Diesel
Custom blending: Full R&D team, target profile matching, iterative formulation
Certifications: Food-grade, ISO compliant, full COAs with every batch, Farm Bill compliant
Key differentiators: Batch consistency < 3% variance, vertically integrated soil-to-oil
Target customer: MSOs, large processors, CPG companies, national brands

DUTY FREE TERPENES (DFT) — Rebellious, Anti-Establishment Botanical Terpene Brand
Position: Bold, underground, craft-first. "Terps Without Borders."
Products: 30+ strain-specific botanical terpene profiles, exotic/hype strains
Key strains: Runtz, Biscotti, Gary Payton, Zoap, Jealousy, Cereal Milk, Pink Rozay, Zushi
MOQs: As low as 25ml for sampling. Volume pricing from 100ml+.
Pricing: $45-80/L depending on volume and complexity
Key differentiators: Hype strain accuracy, small-batch craft, fast shipping, no corporate BS
Target customer: Small-mid extractors, craft brands, cart fillers, hemp/CBD brands
"""

COMPETITOR_INTEL = """
PRIMARY COMPETITORS & PRICING:
True Terpenes: Market leader botanical, $80-150/L botanical, $2,000-4,000/L CDT. Slow custom (4-6 weeks).
Abstrax Tech: Science/R&D focused, $120-200/L botanical, $3,000-6,000/L CDT. Expensive, complex ordering.
Floraplex: Budget botanical $40-80/L, 200+ strains. Inconsistent quality, synthetic undertones.
Denver Terpenes: Regional CO, $60-120/L. Limited profiles, can't scale.
Peak Supply Co: DTC, $50-90/L. Limited B2B infrastructure.

CDT MARKET PRICING (Cannabis Derived Terpenes):
Premium single-source CDT: $5,000-8,000/L (live resin / fresh frozen extraction)
Mid-grade CDT blends: $2,000-4,000/L
Budget CDT (trim-run / mixed source): $800-2,000/L
Self-extraction cost (vertically integrated): $1,500-3,000/L (amortized equipment, labor, biomass)

KEY INSIGHT: Botanical at $45-80/L vs CDT at $2,000-8,000/L = 25-100x cost difference.
For non-flagship products (edibles, beverages, topicals, wellness), consumers cannot distinguish.
"""

# ── PHASE FUNCTIONS ──
# Phases 1-4: Anthropic + web_search (need live research)
# Phase 5: OpenRouter/DeepSeek (financial modeling from gathered data, no search needed)
# Phase 6: Anthropic WITHOUT search (synthesis from phases 1-5, no new research needed)

def phase_1_recon(company, domain, state, existing):
    ctx = f"\nEXISTING DATA:\n{json.dumps(existing, indent=2, default=str)[:2000]}\n" if existing else ""
    text, _, _ = call_anthropic(
        "You are a business intelligence analyst specializing in cannabis/hemp. Search aggressively — at least 5 searches. Return ONLY valid JSON, no markdown.",
        f'Research "{company}" ({domain or "find their website"}) {f"in {state}" if state else ""}.\n{ctx}\n\nSearch: 1) "{company}" overview 2) "{domain or company}" website 3) "{company} about team leadership" 4) "{company} products" 5) "{company} news 2025 2026"\n\nReturn JSON:\n{{"company_name":"{company}","domain":"","verified":true,"description":"3-4 detailed sentences","founded":"","headquarters":"","business_model":"","company_type":"","size_estimate":{{"employees":"","revenue_estimate":"","production_scale":"","evidence":""}},"markets":{{"segments":[],"states_active":[],"multi_state":false,"distribution_channels":[]}},"brand_positioning":"","key_products":[],"recent_news":[{{"headline":"","date":"","significance":""}}],"growth_signals":[],"social_media":{{"instagram":"","linkedin":""}},"terpene_relevance":"HIGH|MEDIUM|LOW","key_questions":[]}}',
        use_search=True
    )
    return parse_json(text) or {}

def phase_2_products(company, domain, p1):
    text, _, _ = call_anthropic(
        "You are a cannabis production analyst. Search aggressively. Return ONLY valid JSON.",
        f'Phase 1:\n{json.dumps(p1, indent=2, default=str)[:3000]}\n\nSearch products for "{company}". Check their website, reviews, COAs.\n\nReturn JSON:\n{{"product_catalog":[{{"name":"","type":"","terpene_relevance":"HIGH|MED|LOW"}}],"production_profile":{{"extraction_methods":[],"facility":"","capacity":""}},"terpene_analysis":{{"current_usage":"","terpene_type":"Botanical|CDT|Synthetic|Mix|Unknown","supplier_clues":[],"products_needing_terpenes":[],"volume_estimate_liters_monthly":0}},"consumer_feedback":{{"flavor_mentions":"","quality_issues":"","opportunities":""}},"product_matches":[{{"their_product":"","our_match":"TBF or DFT profile","rationale":""}}]}}',
        use_search=True
    )
    return parse_json(text) or {}

def phase_3_people(company, domain, p1, p2):
    text, _, _ = call_anthropic(
        "You are a B2B sales intelligence analyst. Find decision makers. Return ONLY valid JSON.",
        f'Company: {p1.get("company_name", company)} | Domain: {p1.get("domain", domain)} | Type: {p1.get("company_type", "?")}\n\nSearch for leadership and purchasing decision makers.\n\nReturn JSON:\n{{"decision_makers":[{{"name":"","title":"","role_in_purchase":"","seniority":"","linkedin_url":"","email_guess":"","personalization_hooks":[]}}],"email_pattern":{{"pattern":"","confidence":"HIGH|MED|LOW"}},"org_dynamics":{{"decision_process":"","buying_committee":""}}}}',
        use_search=True
    )
    return parse_json(text) or {}

def phase_4_competitive(company, domain, p1, p2):
    clues = json.dumps(p2.get("terpene_analysis", {}).get("supplier_clues", []), default=str) if p2 else "[]"
    usage = p2.get("terpene_analysis", {}).get("current_usage", "Unknown") if p2 else "Unknown"
    text, _, _ = call_anthropic(
        f"You are a competitive intelligence analyst.\n\n{COMPETITOR_INTEL}\n\nReturn ONLY valid JSON.",
        f'Target: {p1.get("company_name", company)} ({p1.get("domain", domain)})\nTerpene usage: {usage}\nSupplier clues: {clues}\n\nSearch for their terpene sourcing.\n\nReturn JSON:\n{{"current_supplier":{{"most_likely":"","evidence":[],"satisfaction":{{"positive":[],"negative":[]}},"switching_barriers":[],"switching_triggers":[]}},"displacement":{{"primary_angle":"","supporting_angles":[],"sample_strategy":"","risk_reversal":""}},"pricing":{{"their_likely_cost_per_liter":"","our_price":"","savings":"","value_justification":""}}}}',
        use_search=True
    )
    return parse_json(text) or {}

def phase_5_financial(company, p1, p2, p4):
    """Financial modeling — NO web search needed. Uses OpenRouter for cost savings."""
    vol = json.dumps(p2.get("terpene_analysis", {}).get("volume_estimate_liters_monthly", 0), default=str) if p2 else "0"
    pricing = json.dumps(p4.get("pricing", {}), default=str) if p4 else "{}"
    size = json.dumps(p1.get("size_estimate", {}), default=str) if p1 else "{}"
    matches = json.dumps((p2.get("product_matches", []) if p2 else [])[:5], default=str)

    text, _, _ = call_openrouter(
        f"You are a B2B sales financial analyst. Build precise deal models.\n\nPricing:\n{PRODUCT_CATALOG}\n\nCDT pricing:\n{COMPETITOR_INTEL}\n\nCRITICAL: CDT = $2,000-8,000/L. Botanical = $45-80/L. Savings are 25-100x.\n\nReturn ONLY valid JSON, no markdown, no explanation.",
        f'Build deal model for: {p1.get("company_name", company) if p1 else company}\nSize: {size}\nVolume: {vol} L/mo\nMatches: {matches}\nPricing: {pricing}\nGrowth: {json.dumps(p1.get("growth_signals", []) if p1 else [], default=str)}\n\nReturn JSON:\n{{"deal_model":{{"conservative":{{"desc":"","initial_liters":0,"initial_value":"$","monthly_value":"$","annual_value":"$"}},"likely":{{"desc":"","initial_liters":0,"initial_value":"$","monthly_value":"$","annual_value":"$"}},"upside":{{"desc":"","initial_liters":0,"initial_value":"$","monthly_value":"$","annual_value":"$"}},"weighted_annual":"$"}},"sales_cycle":{{"days_to_close":0,"stages":[],"accelerators":[]}},"expansion_path":{{"year_1":"","year_2":"","year_3":"","ltv_3yr":"$"}}}}',
        max_tokens=4096
    )
    return parse_json(text) or {}

def phase_6_synthesis(company, phases):
    """Strategy synthesis — Anthropic WITHOUT web search. Pure synthesis from data."""
    text, _, _ = call_anthropic(
        f"You are the world's best B2B terpene sales strategist. Synthesize research into a battle plan.\n\nRULES:\n1. Every email references specific details — product names, people, news.\n2. CDT = $2,000-8,000/L. Botanical = $45-80/L. 25-100x difference.\n3. Position as formulation partner, not supplier.\n\nProducts:\n{PRODUCT_CATALOG}\n\nReturn ONLY valid JSON.",
        f'RESEARCH:\nP1: {json.dumps(phases.get("phase_1",{}), indent=1, default=str)[:2500]}\nP2: {json.dumps(phases.get("phase_2",{}), indent=1, default=str)[:2500]}\nP3: {json.dumps(phases.get("phase_3",{}), indent=1, default=str)[:2000]}\nP4: {json.dumps(phases.get("phase_4",{}), indent=1, default=str)[:2000]}\nP5: {json.dumps(phases.get("phase_5",{}), indent=1, default=str)[:1500]}\n\nSynthesize:\n{{"executive_summary":{{"one_liner":"","recommended_brand":"TBF|DFT","priority_score":0,"confidence":"HIGH|MEDIUM|LOW","annual_value":"$","key_insight":""}},"objections":[{{"objection":"","response":"","proof":""}}],"outreach_sequence":[{{"touch":1,"day":0,"channel":"Email","target":"","subject":"","body":"FULL email <150 words","why":""}},{{"touch":2,"day":3,"channel":"LinkedIn","target":"","message":"","why":""}},{{"touch":3,"day":7,"channel":"Email","target":"","subject":"","body":"Different angle","why":""}},{{"touch":4,"day":12,"channel":"Email","target":"","subject":"","body":"Sample offer","why":""}},{{"touch":5,"day":18,"channel":"Email","target":"","subject":"","body":"2-3 sentences final","why":""}}],"sample_kit":{{"profiles":[],"kit_size":"","note":""}},"action_plan":{{"today":[],"this_week":[],"next_30_days":[]}}}}',
        max_tokens=6000,
        use_search=False  # KEY: No search needed for synthesis
    )
    return parse_json(text) or {}


# ── MAIN PIPELINE ──

def generate_brief(company, domain="", state="", brand="auto", existing_data=None):
    print(f"\n  {'━'*60}")
    print(f"  🧠 DEEP SALES INTELLIGENCE BRIEF v4")
    print(f"  Target: {company}")
    print(f"  {'━'*60}")
    routing = "Anthropic+Search (P1-4) → "
    routing += "OpenRouter/DeepSeek (P5) → " if OPENROUTER_KEY else "Anthropic (P5) → "
    routing += "Anthropic no-search (P6)"
    print(f"  Routing: {routing}\n")

    all_phases = {}
    timings = {}

    phases_config = [
        ("phase_1", "COMPANY RECON", "Anthropic+Search", lambda: phase_1_recon(company, domain, state, existing_data)),
        ("phase_2", "PRODUCT & PRODUCTION", "Anthropic+Search", lambda: phase_2_products(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}))),
        ("phase_3", "PEOPLE & RELATIONSHIPS", "Anthropic+Search", lambda: phase_3_people(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}), all_phases.get("phase_2",{}))),
        ("phase_4", "COMPETITIVE & SUPPLIER", "Anthropic+Search", lambda: phase_4_competitive(company, all_phases.get("phase_1",{}).get("domain", domain), all_phases.get("phase_1",{}), all_phases.get("phase_2",{}))),
        ("phase_5", "FINANCIAL MODEL", "OpenRouter" if OPENROUTER_KEY else "Anthropic", lambda: phase_5_financial(company, all_phases.get("phase_1",{}), all_phases.get("phase_2",{}), all_phases.get("phase_4",{}))),
        ("phase_6", "STRATEGY & OUTREACH", "Anthropic (no search)", lambda: phase_6_synthesis(company, all_phases)),
    ]

    for i, (phase_key, label, provider, fn) in enumerate(phases_config):
        prefix = "  ┌─" if i == 0 else "  ├─" if i < len(phases_config)-1 else "  └─"
        print(f"{prefix} Phase {i+1}: {label} [{provider}]")

        start = time.time()
        result = fn()
        elapsed = time.time() - start
        timings[phase_key] = elapsed

        all_phases[phase_key] = result

        if result and len(result) > 1:
            # Show key info
            if phase_key == "phase_1":
                desc = result.get("description", "")[:100]
                print(f"  │  {desc}...")
                print(f"  │  Type: {result.get('company_type', '?')} | Relevance: {result.get('terpene_relevance', '?')}")
            elif phase_key == "phase_2":
                prods = len(result.get("product_catalog", []))
                vol = result.get("terpene_analysis", {}).get("volume_estimate_liters_monthly", "?")
                print(f"  │  Products: {prods} | Est volume: {vol}L/mo")
            elif phase_key == "phase_3":
                dms = len(result.get("decision_makers", []))
                print(f"  │  Decision makers: {dms}")
            elif phase_key == "phase_4":
                supplier = result.get("current_supplier", {}).get("most_likely", "?")
                print(f"  │  Current supplier: {supplier}")
            elif phase_key == "phase_5":
                annual = result.get("deal_model", {}).get("weighted_annual", "?")
                print(f"  │  Weighted annual: {annual}")
            elif phase_key == "phase_6":
                es = result.get("executive_summary", {})
                print(f"  │  Score: {es.get('priority_score', '?')}/100 | {es.get('recommended_brand', '?')} | {es.get('confidence', '?')}")
        else:
            print(f"  │  ⚠️  Limited data returned")

        print(f"  │  ✅ Complete ({elapsed:.0f}s)")
        print(f"  │")

        # Adaptive delay between phases
        if i < len(phases_config) - 1:
            delay = 15  # Base delay
            if elapsed < 5:  # If phase was very fast (likely rate limited/failed), wait longer
                delay = 25
            time.sleep(delay)

    total = sum(timings.values())
    print(f"\n  ⏱️  Total: {total:.0f}s ({total/60:.1f} min)")

    # Cost summary
    print(f"\n  💰 Cost Summary:")
    print(f"  │  Total: ${costs['total_cost_est']:.4f}")
    print(f"  │  Tokens: {costs['total_input_tokens']+costs['total_output_tokens']:,}")
    anthropic_calls = sum(1 for c in costs["calls"] if c["provider"] == "anthropic")
    or_calls = sum(1 for c in costs["calls"] if c["provider"] == "openrouter")
    print(f"  │  Calls: {anthropic_calls} Anthropic + {or_calls} OpenRouter")

    # Save
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    slug = re.sub(r'[^a-z0-9]', '_', company[:30].lower())
    json_path = BRIEFS_DIR / f"brief_{slug}_{ts}.json"

    brief_data = {
        "metadata": {
            "company": company,
            "domain": domain,
            "generated_at": datetime.utcnow().isoformat(),
            "version": "v4",
            "total_seconds": total,
            "timings": timings,
            "cost": {
                "total": round(costs["total_cost_est"], 4),
                "tokens": costs["total_input_tokens"] + costs["total_output_tokens"],
                "calls": costs["calls"],
            }
        },
        "phases": all_phases,
    }

    with open(json_path, "w") as f:
        json.dump(brief_data, f, indent=2, default=str)

    # Display summary
    p6 = all_phases.get("phase_6", {})
    es = p6.get("executive_summary", {})
    print(f"\n  {'━'*60}")
    print(f"  💡 {es.get('one_liner', 'N/A')}")
    print(f"  🏷️  {es.get('recommended_brand','?')} | Score: {es.get('priority_score','?')}/100 | {es.get('confidence','?')}")
    print(f"  💰 {es.get('annual_value','?')}")
    print(f"  🔑 {es.get('key_insight','N/A')[:150]}")

    seq = p6.get("outreach_sequence", [])
    if seq:
        t1 = seq[0]
        print(f"\n  📧 Touch 1 → {t1.get('target','?')}")
        print(f"  Subject: {t1.get('subject','?')}")
        body = t1.get("body", "")
        if body:
            print(f"  {body[:300]}...")

    print(f"\n  💾 {json_path}")
    print(f"\n  {'━'*60}\n")

    return all_phases


def main():
    parser = argparse.ArgumentParser(description="Sales Intel Brief v4 — Cost Optimized")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--domain", default="")
    parser.add_argument("--state", default="")
    parser.add_argument("--brand", default="auto")
    parser.add_argument("--batch", help="Batch from scored JSON file")
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    if not ANTHROPIC_KEY:
        print("  ❌ Set ANTHROPIC_API_KEY")
        sys.exit(1)

    if OPENROUTER_KEY:
        print(f"  ✅ OpenRouter enabled — Phase 5 on DeepSeek V3")
    else:
        print(f"  ℹ️  No OpenRouter key — all phases on Anthropic")

    if args.batch:
        with open(args.batch) as f:
            data = json.load(f)
        leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
        # Unique companies by highest score
        companies = {}
        for l in leads:
            co = l.get("company_name", "?")
            score = l.get("nexus_lead_score", 0)
            if co not in companies or score > companies[co]["score"]:
                companies[co] = {"score": score, "domain": l.get("company_domain", l.get("domain", "")), "state": l.get("state", ""), "data": l}
        ranked = sorted(companies.items(), key=lambda x: x[1]["score"], reverse=True)[:args.top]

        for i, (name, info) in enumerate(ranked):
            print(f"\n  ═══ [{i+1}/{len(ranked)}] {name} (score: {info['score']}) ═══")
            generate_brief(name, info["domain"], info["state"], args.brand, info["data"])
            if i < len(ranked) - 1:
                print("  ⏳ Cooling down 30s between briefs...")
                time.sleep(30)

    elif args.company:
        generate_brief(args.company, args.domain, args.state, args.brand)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
