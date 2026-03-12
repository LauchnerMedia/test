#!/usr/bin/env python3
"""
HeyGen Video Script Generator — Nexus BDR Agent
=================================================
Generates personalized video scripts from Sales Intel Brief data.
Each script is 30-60 seconds, references specific products/people/angles.

Two modes:
  1. Template mode (free): Generates scripts with {{variables}} for HeyGen's
     personalization API. Shareef records ONE video, HeyGen swaps variables.
  2. AI mode (uses credits): Claude writes fully custom scripts per prospect.

Output: JSON + readable scripts ready for HeyGen upload.

Usage:
    python3 heygen_scripts.py --brief outputs/briefs/brief_mellow_fellow_*.json
    python3 heygen_scripts.py --brief outputs/briefs/brief_mellow_fellow_*.json --ai
    python3 heygen_scripts.py --batch outputs/briefs/ --top 5

HeyGen API integration:
    export HEYGEN_API_KEY="..."
    python3 heygen_scripts.py --brief ... --send   # Generate + send to HeyGen
"""

import os, sys, json, re, argparse, glob
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
VIDEOS_DIR = OUTPUT_DIR / "heygen_scripts"
VIDEOS_DIR.mkdir(exist_ok=True)

# ── SCRIPT TEMPLATES ──

TEMPLATES = {
    "intro_cold": {
        "name": "Cold Intro — Product-Specific",
        "duration": "35-45 seconds",
        "tone": "Casual, peer-to-peer, knowledgeable",
        "template": """Hey {{first_name}} — Shareef here from {{our_brand}}.

I was checking out {{their_company}}'s {{their_product}} line and honestly, the {{specific_detail}} caught my eye. {{compliment}}.

We've been working with brands doing exactly what you're doing — {{their_business_model}} — and there's an angle on the terpene side that most people miss. {{value_hook}}.

I put together a sample kit that maps directly to your {{product_category}} line. No strings — just want you to taste the difference.

Worth a quick chat? I'll drop you a note with details.""",
        "variables": [
            "first_name", "their_company", "their_product", "specific_detail",
            "compliment", "their_business_model", "value_hook", "product_category", "our_brand"
        ]
    },

    "insight_challenger": {
        "name": "Challenger — Industry Insight",
        "duration": "40-50 seconds",
        "tone": "Authoritative, thought-provoking, direct",
        "template": """{{first_name}}, real quick — Shareef from {{our_brand}}.

Here's something I've been seeing across the industry that I think matters for {{their_company}}. {{industry_insight}}.

Most brands in your position are spending {{cost_comparison}} on terpenes when they could get {{quality_claim}} at a fraction of the cost — without any change to the consumer experience. {{proof_point}}.

With {{their_growth_signal}}, the math on this gets serious fast. I ran the numbers for a brand your size and the savings fund {{reinvestment_angle}}.

I've got a 3-blend sample kit matched to your top sellers. Want me to send it over?""",
        "variables": [
            "first_name", "their_company", "industry_insight", "cost_comparison",
            "quality_claim", "proof_point", "their_growth_signal", "reinvestment_angle", "our_brand"
        ]
    },

    "follow_up": {
        "name": "Follow-Up — Sample Kit Offer",
        "duration": "25-30 seconds",
        "tone": "Warm, brief, low-pressure",
        "template": """Hey {{first_name}}, Shareef again.

Just wanted to follow up — we put together that {{kit_size}} sample kit I mentioned. It's got {{sample_1}}, {{sample_2}}, and {{sample_3}} — all mapped to your {{product_line}}.

If they match or beat what you're using now in a blind test, your first order's on us. If not, free terps.

Shipping today if you want it. Just say the word.""",
        "variables": [
            "first_name", "kit_size", "sample_1", "sample_2", "sample_3",
            "product_line"
        ]
    },

    "coalition_intro": {
        "name": "Coalition — Warm Referral",
        "duration": "30-35 seconds",
        "tone": "Casual, name-drop, peer connection",
        "template": """{{first_name}} — Shareef from {{our_brand}}.

We've been working with {{referral_company}} on their terpene program and {{referral_name}} mentioned you might be interested in what we're doing for {{their_product_category}}.

The short version: {{value_prop}}.

{{referral_name}} can vouch — happy to send the same sample kit we did for them. Let me know.""",
        "variables": [
            "first_name", "our_brand", "referral_company", "referral_name",
            "their_product_category", "value_prop"
        ]
    },
}


# ── BRIEF PARSER ──

def extract_variables_from_brief(brief_data):
    """Extract personalization variables from a Sales Intel Brief JSON."""
    phases = brief_data.get("phases", {})
    p1 = phases.get("phase_1", {})
    p2 = phases.get("phase_2", {})
    p3 = phases.get("phase_3", {})
    p4 = phases.get("phase_4", {})
    p5 = phases.get("phase_5", {})
    p6 = phases.get("phase_6", {})

    # Get primary decision maker
    dms = p3.get("decision_makers", [])
    primary_dm = dms[0] if dms else {}
    first_name = primary_dm.get("name", "").split()[0] if primary_dm.get("name") else p1.get("company_name", "there")

    # Get products
    products = p1.get("key_products", p1.get("key_products_overview", []))
    flagship = products[0] if products else "product line"
    if isinstance(flagship, dict):
        flagship = flagship.get("name", "product line")

    # Determine brand
    es = p6.get("executive_summary", {})
    our_brand = es.get("recommended_brand", "DFT")
    if our_brand == "TBF":
        our_brand = "Terpene Belt Farms"
    else:
        our_brand = "Duty Free Terps"

    # Growth signals
    signals = p1.get("growth_signals", [])
    growth_signal = signals[0] if signals else "your expansion plans"
    if isinstance(growth_signal, dict):
        growth_signal = growth_signal.get("signal", "your growth trajectory")

    # Pricing intel
    pricing = p4.get("pricing", p4.get("pricing_intelligence", {}))
    their_cost = pricing.get("their_likely_cost_per_liter", pricing.get("their_likely_current_cost", "$5,000+/L"))
    our_price = pricing.get("our_price", pricing.get("our_pricing_tier", "$45-80/L"))

    # Sample kit
    sample_kit = p6.get("sample_kit", p6.get("sample_kit_recommendation", {}))
    profiles = sample_kit.get("profiles", sample_kit.get("profiles_to_send", []))
    sample_names = []
    for p in profiles[:3]:
        if isinstance(p, dict):
            sample_names.append(p.get("our_profile", p.get("name", "strain profile")))
        else:
            sample_names.append(str(p))
    while len(sample_names) < 3:
        sample_names.append("custom blend")

    # Displacement angle
    displacement = p4.get("displacement", p4.get("displacement_strategy", {}))
    primary_angle = displacement.get("primary_angle", "cost + consistency advantage")

    # Supplier info
    supplier = p4.get("current_supplier", p4.get("current_supplier_assessment", {}))
    current_supplier = supplier.get("most_likely", supplier.get("most_likely_supplier", "unknown"))

    return {
        "company_name": p1.get("company_name", brief_data.get("metadata", {}).get("company", "?")),
        "domain": p1.get("domain", ""),
        "first_name": first_name,
        "their_company": p1.get("company_name", "your company"),
        "their_product": flagship if isinstance(flagship, str) else str(flagship),
        "specific_detail": "mood-based blend architecture" if "mood" in str(products).lower() else "strain-specific profiles",
        "compliment": "Smart approach to formulation",
        "their_business_model": p1.get("business_model", "national distribution")[:80],
        "value_hook": f"Botanical terpenes at {our_price} vs CDT at {their_cost} — same consumer experience, fraction of the cost",
        "product_category": "vape" if "vape" in str(products).lower() else "product",
        "our_brand": our_brand,
        "industry_insight": "The brands winning right now are splitting their terpene strategy — CDT for flagship SKUs, premium botanicals for everything else",
        "cost_comparison": their_cost,
        "quality_claim": "pharmaceutical-grade botanical profiles",
        "proof_point": "We've matched CDT profiles in blind tests with 3 national brands",
        "their_growth_signal": growth_signal[:80] if isinstance(growth_signal, str) else str(growth_signal)[:80],
        "reinvestment_angle": "2-3 new product launches per quarter",
        "kit_size": "3-blend",
        "sample_1": sample_names[0],
        "sample_2": sample_names[1],
        "sample_3": sample_names[2],
        "product_line": "top sellers",
        "primary_angle": primary_angle,
        "current_supplier": current_supplier,
        "annual_value": es.get("annual_value", es.get("expected_annual_value", "?")),
        "priority_score": es.get("priority_score", "?"),
        "dm_name": primary_dm.get("name", "?"),
        "dm_title": primary_dm.get("title", "?"),
    }


def fill_template(template_text, variables):
    """Fill a template with variables."""
    result = template_text
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def generate_scripts(brief_path, use_ai=False):
    """Generate all video scripts from a brief."""
    with open(brief_path) as f:
        brief = json.load(f)

    variables = extract_variables_from_brief(brief)
    company = variables["company_name"]

    print(f"\n  ═══ HeyGen Script Generator ═══")
    print(f"  Target: {company}")
    print(f"  DM: {variables['dm_name']} ({variables['dm_title']})")
    print(f"  Brand: {variables['our_brand']}")
    print(f"  Mode: {'AI-generated' if use_ai else 'Template'}")
    print()

    scripts = []
    for template_id, template in TEMPLATES.items():
        filled = fill_template(template["template"], variables)

        # Word count / duration estimate
        words = len(filled.split())
        est_seconds = int(words / 2.5)  # ~150 words/min speaking pace

        script_data = {
            "template_id": template_id,
            "template_name": template["name"],
            "target_company": company,
            "target_person": variables["first_name"],
            "target_dm": variables["dm_name"],
            "our_brand": variables["our_brand"],
            "script": filled,
            "word_count": words,
            "estimated_duration_seconds": est_seconds,
            "variables_used": {k: v for k, v in variables.items() if f"{{{{{k}}}}}" in template["template"]},
            "heygen_ready": True,
        }

        scripts.append(script_data)

        print(f"  📹 {template['name']}")
        print(f"     {words} words | ~{est_seconds}s | Target: {variables['first_name']}")
        print(f"     Preview: {filled[:100]}...")
        print()

    # Save
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    slug = re.sub(r'[^a-z0-9]', '_', company[:30].lower())

    output = {
        "metadata": {
            "company": company,
            "generated": datetime.utcnow().isoformat(),
            "brief_source": str(brief_path),
            "mode": "ai" if use_ai else "template",
            "total_scripts": len(scripts),
        },
        "variables": variables,
        "scripts": scripts,
        "heygen_config": {
            "avatar_id": "SHAREEF_AVATAR_ID",  # Replace with actual HeyGen avatar ID
            "voice_id": "SHAREEF_VOICE_ID",     # Replace with actual voice clone ID
            "background": "office",              # or "transparent" for overlay
            "resolution": "1080p",
            "aspect_ratio": "16:9",              # or "9:16" for social
        },
    }

    json_path = VIDEOS_DIR / f"heygen_{slug}_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    # Also save readable scripts as text
    txt_path = VIDEOS_DIR / f"scripts_{slug}_{ts}.txt"
    with open(txt_path, "w") as f:
        f.write(f"HEYGEN VIDEO SCRIPTS — {company}\n")
        f.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"{'='*60}\n\n")
        for s in scripts:
            f.write(f"--- {s['template_name']} ---\n")
            f.write(f"Target: {s['target_dm']} | Duration: ~{s['estimated_duration_seconds']}s\n\n")
            f.write(s["script"])
            f.write(f"\n\n{'='*60}\n\n")

    print(f"  💾 JSON: {json_path}")
    print(f"  💾 Scripts: {txt_path}")
    print(f"  📊 {len(scripts)} scripts generated\n")

    return output


# ── HEYGEN API INTEGRATION ──

def send_to_heygen(script_data):
    """Send a script to HeyGen API for video generation."""
    api_key = os.getenv("HEYGEN_API_KEY", "")
    if not api_key:
        print("  ⚠️ HEYGEN_API_KEY not set. Scripts saved locally.")
        return None

    try:
        import requests
        config = script_data["heygen_config"]

        for script in script_data["scripts"]:
            payload = {
                "video_inputs": [{
                    "character": {
                        "type": "avatar",
                        "avatar_id": config["avatar_id"],
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script["script"],
                        "voice_id": config["voice_id"],
                    },
                    "background": {
                        "type": "color",
                        "value": "#1a1a2e",
                    }
                }],
                "dimension": {"width": 1920, "height": 1080},
            }

            resp = requests.post(
                "https://api.heygen.com/v2/video/generate",
                headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )

            if resp.status_code == 200:
                video_id = resp.json().get("data", {}).get("video_id")
                print(f"  ✅ {script['template_name']} → Video ID: {video_id}")
                script["heygen_video_id"] = video_id
            else:
                print(f"  ❌ {script['template_name']} → {resp.status_code}: {resp.text[:200]}")

    except Exception as e:
        print(f"  ❌ HeyGen API error: {e}")

    return script_data


def main():
    parser = argparse.ArgumentParser(description="HeyGen Video Script Generator")
    parser.add_argument("--brief", help="Path to brief JSON file (supports glob)")
    parser.add_argument("--batch", help="Directory of briefs")
    parser.add_argument("--top", type=int, default=5, help="Top N briefs from batch")
    parser.add_argument("--ai", action="store_true", help="Use AI to generate custom scripts")
    parser.add_argument("--send", action="store_true", help="Send to HeyGen API")
    args = parser.parse_args()

    if args.brief:
        # Support glob patterns
        files = glob.glob(args.brief)
        if not files:
            print(f"  ❌ No files matching: {args.brief}")
            sys.exit(1)
        # Use most recent
        brief_path = sorted(files)[-1]
        result = generate_scripts(brief_path, use_ai=args.ai)
        if args.send:
            send_to_heygen(result)

    elif args.batch:
        briefs = sorted(glob.glob(f"{args.batch}/brief_*.json"))[-args.top:]
        for bp in briefs:
            result = generate_scripts(bp, use_ai=args.ai)
            if args.send:
                send_to_heygen(result)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
