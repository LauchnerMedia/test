#!/usr/bin/env python3
"""
Universal Enrichment Pipeline — Nexus BDR Agent
=================================================
Takes leads from ANY source, enriches them with Claude + web search,
scores them, assigns brand/tier, and imports to GHL with all custom fields.

Usage:
    python3 enrich_pipeline.py --input prospects.json --brand auto --import-ghl
    python3 enrich_pipeline.py --input leads.csv --brand tbf --import-ghl --pipeline-id "YA64..." --stage-id "5c18..."
    python3 enrich_pipeline.py --input single_lead.json --enrich-only

Accepts:
    - JSON from claude_researcher.py (prospects format)
    - JSON from instagram_agent.py (accounts format)
    - CSV with columns: company_name, contact_name, email, phone, website, state
    - Any JSON with at minimum "company_name" field

Environment:
    ANTHROPIC_API_KEY, GHL_API_TOKEN, GHL_LOCATION_ID
"""

import os
import sys
import json
import csv
import re
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"

GHL_API_TOKEN = os.getenv("GHL_API_TOKEN", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
CONFIG_DIR = SKILL_DIR / "config"
OUTPUT_DIR.mkdir(exist_ok=True)


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
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end > start:
            cleaned = response[start:end+1]
        else:
            return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def ghl_request(method, endpoint, data=None, params=None):
    """GHL API request."""
    headers = {
        "Authorization": f"Bearer {GHL_API_TOKEN}",
        "Content-Type": "application/json",
        "Version": GHL_API_VERSION,
    }
    url = f"{GHL_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=30)
        else:
            return {"error": "bad method"}
        if resp.status_code == 429:
            time.sleep(10)
            return ghl_request(method, endpoint, data, params)
        if resp.status_code >= 400:
            return {"error": resp.text[:200], "status": resp.status_code}
        return resp.json() if resp.text else {"success": True}
    except Exception as e:
        return {"error": str(e)}


# ─── LOAD & NORMALIZE ──────────────────────────────────────

def load_leads(input_path):
    """Load leads from any supported format."""
    path = Path(input_path)
    if not path.exists():
        print(f"  ❌ File not found: {input_path}")
        sys.exit(1)

    if path.suffix == ".csv":
        return load_csv(path)
    elif path.suffix == ".json":
        return load_json(path)
    else:
        print(f"  ❌ Unsupported format: {path.suffix}")
        sys.exit(1)


def load_csv(path):
    """Load CSV into normalized lead format."""
    leads = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = {
                "company_name": row.get("company_name", row.get("Company", row.get("company", ""))),
                "contact_name": row.get("contact_name", row.get("Name", row.get("name", ""))),
                "contact_title": row.get("title", row.get("Title", row.get("contact_title", ""))),
                "email": row.get("email", row.get("Email", "")),
                "phone": row.get("phone", row.get("Phone", "")),
                "domain": row.get("domain", row.get("website", row.get("Website", row.get("Domain", "")))),
                "city": row.get("city", row.get("City", "")),
                "state": row.get("state", row.get("State", "")),
                "source": "csv_import",
            }
            if lead["company_name"] or lead["contact_name"]:
                leads.append(lead)
    return leads


def load_json(path):
    """Load JSON into normalized lead format."""
    with open(path) as f:
        data = json.load(f)

    # Handle various JSON structures
    if "leads" in data:
        return data["leads"]
    elif "prospects" in data:
        return data["prospects"]
    elif "accounts" in data:
        # Instagram agent output
        accounts = data["accounts"]
        leads = []
        for a in accounts:
            leads.append({
                "company_name": a.get("company_name", a.get("username", "")),
                "contact_name": a.get("contact_name", ""),
                "contact_title": a.get("contact_title", ""),
                "email": a.get("business_email", a.get("email", "")),
                "phone": a.get("phone", ""),
                "domain": a.get("website", a.get("domain", "")),
                "city": a.get("city", ""),
                "state": a.get("state", a.get("search_state", "")),
                "instagram": a.get("username", a.get("instagram", "")),
                "follower_count": a.get("follower_count", a.get("instagram_followers", 0)),
                "source": a.get("source", "instagram"),
                "personalization_hook": a.get("personalization_hook", a.get("relevance", "")),
                "prospect_fit": a.get("prospect_fit", a.get("terpene_fit", "")),
            })
        return leads
    elif isinstance(data, list):
        return data
    else:
        return [data]


# ─── ENRICH ─────────────────────────────────────────────────

def enrich_lead(lead):
    """Enrich a single lead with Claude + web search."""
    company = lead.get("company_name", "Unknown")
    domain = lead.get("domain", "")
    state = lead.get("state", "")
    contact = lead.get("contact_name", "")

    search_hint = f"{company}"
    if domain:
        search_hint += f" {domain}"
    if state:
        search_hint += f" {state}"

    system_prompt = """You are a B2B sales research analyst for Nexus Agriscience, a botanical terpene supplier.
Enrich this lead with comprehensive business intelligence using web search.
Return ONLY valid JSON — no other text."""

    user_prompt = f"""Research "{company}" ({domain or 'no website known'}) in {state or 'unknown state'}.
Known contact: {contact or 'unknown'}

Search for this company and return comprehensive intelligence:
{{
  "company_name": "{company}",
  "company_domain": "{domain}",
  "company_description": "2-3 sentence description",
  "company_type": "Licensed Operator|MSO|Processor|Manufacturer|Brand|Distributor|Retailer|Lab|Consultant|Hemp Farm|CPG Company",
  "company_size": "1-10|11-50|51-200|201-500|500+",
  "company_founded": "year or null",
  "city": "",
  "state": "",
  "markets_served": ["Adult-Use", "Medical", "Hemp/CBD", etc],
  "multi_state": false,
  "state_count": 1,
  "license_states": ["CA"],
  "extraction_methods": ["BHO", "CO2", etc if applicable],
  "product_types": ["Live Resin", "Distillate", etc if applicable],
  "terpene_usage": "Currently Uses Botanical|Currently Uses Synthetic|Uses Cannabis-Derived Only|No Terpene Reintroduction|Unknown",
  "current_terpene_supplier": "name or null",
  "annual_terpene_volume_est": "<1kg|1-5kg|5-25kg|25-100kg|100kg+",
  "decision_makers": [
    {{"name": "", "title": "", "email": "if found publicly", "linkedin": "if found"}}
  ],
  "instagram_handle": "@handle or null",
  "instagram_followers": 0,
  "website_url": "",
  "linkedin_url": "",
  "recent_news": ["brief headline 1", "brief headline 2"],
  "buying_signals": ["Expanding Production", "Hiring", etc or empty],
  "personalization_hook": "Specific thing to reference in outreach",
  "pain_points": "Known challenges or null",
  "recommended_brand": "TBF|DFT based on company profile",
  "recommended_brand_reason": "why",
  "data_confidence": "Verified|High|Medium|Low"
}}

Use null for fields you genuinely can't find. Never fabricate."""

    print(f"    🔍 Enriching: {company}...", end=" ", flush=True)
    response = call_claude(system_prompt, user_prompt)
    result = parse_json(response)

    if result:
        print("✅")
        # Merge enriched data back into lead
        lead.update({k: v for k, v in result.items() if v is not None})
        lead["enrichment_date"] = datetime.utcnow().isoformat()
        lead["enrichment_source"] = "claude_web_search"
        lead["enriched"] = True
    else:
        print("⚠️  partial")
        lead["enriched"] = False
        # Save raw for debugging
        if response:
            raw_path = OUTPUT_DIR / f"raw_enrich_{company[:20].replace(' ', '_')}_{datetime.utcnow().strftime('%H%M')}.txt"
            raw_path.write_text(response)

    return lead


# ─── SCORE ──────────────────────────────────────────────────

def score_lead(lead):
    """Apply lead scoring formula."""
    score = 0

    # Title match (+25)
    title = (lead.get("contact_title") or lead.get("title") or "").lower()
    c_suite = ["ceo", "cto", "coo", "founder", "owner", "president", "co-founder", "chief"]
    vp_dir = ["vp", "vice president", "director", "head of"]
    manager = ["manager", "lead", "supervisor"]
    if any(t in title for t in c_suite):
        score += 25
        lead["decision_maker_level"] = "C-Suite"
    elif any(t in title for t in vp_dir):
        score += 20
        lead["decision_maker_level"] = "VP"
    elif any(t in title for t in manager):
        score += 15
        lead["decision_maker_level"] = "Manager"
    elif lead.get("decision_maker_level"):
        # Already set by seniority mapping from Apollo
        level = lead["decision_maker_level"]
        level_scores = {"C-Suite": 25, "VP": 20, "Director": 18, "Manager": 15, "Individual": 5}
        score += level_scores.get(level, 5)
    else:
        score += 5
        lead["decision_maker_level"] = "Individual"

    # Company size (+20) — handle Apollo employee count
    size = lead.get("company_size", "")
    if not size:
        emp = lead.get("employees", "")
        if emp:
            try:
                emp_num = int(str(emp).replace(",", "").strip())
                if emp_num <= 10: size = "1-10"
                elif emp_num <= 50: size = "11-50"
                elif emp_num <= 200: size = "51-200"
                elif emp_num <= 500: size = "201-500"
                else: size = "500+"
                lead["company_size"] = size
            except (ValueError, TypeError):
                pass
    size_scores = {"11-50": 20, "51-200": 18, "1-10": 15, "201-500": 12, "500+": 10}
    score += size_scores.get(size, 5)

    # Extraction methods present (+20)
    methods = lead.get("extraction_methods", [])
    if methods:
        score += 20

    # License state tier (+15)
    tier1_states = {"CA", "CO", "OR", "WA", "MI", "OK", "AZ", "NV", "IL", "MA", "NJ", "MO", "MD", "OH"}
    states = lead.get("license_states", [])
    if not states:
        s = lead.get("state", "")
        if s:
            states = [s[:2].upper()]
    if any(s in tier1_states for s in states):
        score += 15
    elif states:
        score += 8

    # Terpene usage (+10)
    usage = lead.get("terpene_usage", "Unknown")
    if usage in ("Currently Uses Botanical", "Currently Uses Synthetic"):
        score += 10
    elif usage == "No Terpene Reintroduction":
        score += 5

    # Buying signals (+10)
    signals = lead.get("buying_signals", [])
    if signals:
        score += min(len(signals) * 3, 10)

    # Penalties
    objections = lead.get("objection_risk", [])
    if "Happy With Current Supplier" in objections:
        score -= 15
    ctype = lead.get("company_type", "")
    if ctype == "Retailer":
        score -= 10

    score = max(0, min(100, score))
    lead["nexus_lead_score"] = score

    # Tier assignment
    if score >= 80:
        lead["icp_tier"] = "Tier 1 Perfect"
        lead["prospect_temperature"] = "Hot"
    elif score >= 60:
        lead["icp_tier"] = "Tier 2 Strong"
        lead["prospect_temperature"] = "Warm"
    elif score >= 40:
        lead["icp_tier"] = "Tier 3 Moderate"
        lead["prospect_temperature"] = "Cool"
    else:
        lead["icp_tier"] = "Tier 4 Low"
        lead["prospect_temperature"] = "Cold"

    return lead


def assign_brand(lead):
    """Auto-assign TBF or DFT based on company profile."""
    # If enrichment already recommended, use that
    rec = lead.get("recommended_brand", "")
    if rec in ("TBF", "DFT"):
        lead["nexus_brand"] = rec
        return lead

    # Auto-assign logic
    size = lead.get("company_size", "")
    ctype = lead.get("company_type", "")
    markets = lead.get("markets_served", [])

    if ctype == "MSO" or size in ("201-500", "500+"):
        lead["nexus_brand"] = "TBF"
    elif any(m in markets for m in ["CPG", "Cosmetics", "Pharma", "Food & Bev"]):
        lead["nexus_brand"] = "TBF"
    elif size in ("1-10", "11-50") and ctype in ("Processor", "Brand"):
        lead["nexus_brand"] = "DFT"
    elif any(m in markets for m in ["Hemp/CBD"]):
        lead["nexus_brand"] = "DFT"
    else:
        lead["nexus_brand"] = "DFT"  # Default to DFT for smaller/unknown

    return lead


# ─── GHL IMPORT ─────────────────────────────────────────────

def load_field_map():
    """Load GHL custom field mapping."""
    map_path = CONFIG_DIR / "ghl-field-map.json"
    if map_path.exists():
        with open(map_path) as f:
            return json.load(f)
    return {}


def build_custom_fields(lead, field_map):
    """Map enriched lead data to GHL custom field keys."""
    customs = []

    # Mapping: our field name → GHL custom field name → value
    mappings = {
        "Nexus Brand": lead.get("nexus_brand"),
        "Company Domain": lead.get("company_domain", lead.get("domain")),
        "Decision Maker Level": lead.get("decision_maker_level"),
        "Lead Source": lead.get("source", "Claude Research"),
        "Lead Source Detail": lead.get("lead_source_detail"),
        "Company Size": lead.get("company_size"),
        "Company Type": lead.get("company_type"),
        "Company Founded": lead.get("company_founded"),
        "Markets Served": lead.get("markets_served"),
        "Multi State Operator": lead.get("multi_state"),
        "State Count": lead.get("state_count"),
        "Extraction Methods": lead.get("extraction_methods"),
        "Product Types": lead.get("product_types"),
        "Terpene Usage": lead.get("terpene_usage"),
        "Current Terpene Supplier": lead.get("current_terpene_supplier"),
        "Annual Terpene Volume": lead.get("annual_terpene_volume_est"),
        "Nexus Lead Score": lead.get("nexus_lead_score"),
        "ICP Tier": lead.get("icp_tier"),
        "Prospect Temperature": lead.get("prospect_temperature"),
        "Buying Signals": lead.get("buying_signals"),
        "Instagram Handle": lead.get("instagram_handle", lead.get("instagram")),
        "Instagram Followers": lead.get("instagram_followers", lead.get("follower_count")),
        "LinkedIn URL": lead.get("linkedin_url"),
        "Personalization Hook": lead.get("personalization_hook"),
        "Recent News": json.dumps(lead.get("recent_news", []))[:500] if lead.get("recent_news") else None,
        "Pain Points": lead.get("pain_points"),
        "Data Confidence": lead.get("data_confidence"),
        "Enrichment Source": lead.get("enrichment_source"),
    }

    for field_name, value in mappings.items():
        if value is None or value == "" or value == []:
            continue
        field_info = field_map.get(field_name)
        if field_info and field_info.get("key"):
            # Convert lists to comma-separated for multi-select
            if isinstance(value, list):
                value = value  # GHL accepts arrays for multi-select
            customs.append({
                "key": field_info["key"],
                "field_value": value,
            })

    return customs


def import_to_ghl(lead, pipeline_id=None, stage_id=None, field_map=None):
    """Import a single enriched lead to GHL."""
    if not field_map:
        field_map = {}

    # Parse contact name
    contact_name = lead.get("contact_name", "")
    if not contact_name:
        dms = lead.get("decision_makers", [])
        if dms:
            contact_name = dms[0].get("name", "")

    parts = contact_name.split() if contact_name else []
    first_name = parts[0] if parts else "Unknown"
    last_name = " ".join(parts[1:]) if len(parts) > 1 else "(Unknown)"

    email = lead.get("email", "")
    if not email:
        dms = lead.get("decision_makers", [])
        if dms:
            email = dms[0].get("email", "")

    phone = lead.get("phone", "")
    company = lead.get("company_name", "")

    # Build payload
    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "locationId": GHL_LOCATION_ID,
        "companyName": company,
        "source": lead.get("source", "nexus-bdr-agent"),
    }

    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone

    city = lead.get("city", "")
    state = lead.get("state", "")
    if city:
        payload["city"] = city
    if state:
        payload["state"] = state

    title = lead.get("contact_title", lead.get("title", ""))
    if not title:
        dms = lead.get("decision_makers", [])
        if dms:
            title = dms[0].get("title", "")

    website = lead.get("company_domain", lead.get("domain", lead.get("website_url", "")))
    if website:
        if not website.startswith("http"):
            website = f"https://{website}"
        payload["website"] = website

    # LinkedIn from Apollo
    linkedin = lead.get("linkedin", lead.get("linkedin_url", ""))
    if linkedin:
        lead["linkedin_url"] = linkedin

    # Tags
    tags = []
    brand = lead.get("nexus_brand", "")
    if brand:
        tags.append(f"brand:{brand.lower()}")
    tier = lead.get("icp_tier", "")
    if tier:
        tags.append(f"quality:{tier.lower().replace(' ', '-')}")
    temp = lead.get("prospect_temperature", "")
    if temp:
        tags.append(f"temp:{temp.lower()}")
    source = lead.get("source", "")
    if source:
        tags.append(f"source:{source.replace('_', '-')}")
    ctype = lead.get("company_type", "")
    if ctype:
        tags.append(f"vertical:{ctype.lower().replace(' ', '-')}")
    tags.append("nexus-bdr-agent")
    payload["tags"] = tags

    # Custom fields
    custom_fields = build_custom_fields(lead, field_map)
    if custom_fields:
        payload["customFields"] = custom_fields

    # Create or upsert
    if email or phone:
        result = ghl_request("POST", "/contacts/upsert", data=payload)
    else:
        result = ghl_request("POST", "/contacts/", data=payload)

    contact = result.get("contact", {})
    contact_id = contact.get("id")

    if contact_id and pipeline_id and stage_id:
        opp_name = f"{company} — {brand}" if brand else company
        ghl_request("POST", "/opportunities/", data={
            "pipelineId": pipeline_id,
            "pipelineStageId": stage_id,
            "locationId": GHL_LOCATION_ID,
            "contactId": contact_id,
            "name": opp_name,
            "status": "open",
            "source": "nexus-bdr-agent",
        })

    return contact_id


# ─── MAIN PIPELINE ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Universal Enrichment Pipeline — Nexus BDR")
    parser.add_argument("--input", required=True, help="Input file (JSON or CSV)")
    parser.add_argument("--brand", default="auto", help="Force brand (tbf/dft) or 'auto' for smart assignment")
    parser.add_argument("--enrich-only", action="store_true", help="Enrich but don't import to GHL")
    parser.add_argument("--import-ghl", action="store_true", help="Import enriched leads to GHL")
    parser.add_argument("--pipeline-id", help="GHL pipeline ID for opportunity creation")
    parser.add_argument("--stage-id", help="GHL pipeline stage ID")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip enrichment, just import existing data")
    parser.add_argument("--max", type=int, default=100, help="Max leads to process")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  🚀 NEXUS BDR — Universal Enrichment Pipeline")
    print(f"  Input: {args.input}")
    print(f"  Brand: {args.brand}")
    print(f"  Enrich: {'skip' if args.skip_enrich else 'yes'}")
    print(f"  Import GHL: {'yes' if args.import_ghl else 'no'}")
    print(f"{'='*60}\n")

    # Load leads
    print("  📂 Loading leads...")
    leads = load_leads(args.input)
    leads = leads[:args.max]
    print(f"     Loaded {len(leads)} leads\n")

    if not leads:
        print("  ❌ No leads found in input file.")
        sys.exit(1)

    # Enrich
    if not args.skip_enrich:
        print(f"  🔬 Enriching {len(leads)} leads...\n")
        enriched = []
        for i, lead in enumerate(leads):
            print(f"  [{i+1}/{len(leads)}]", end="")
            lead = enrich_lead(lead)
            lead = score_lead(lead)
            if args.brand == "auto":
                lead = assign_brand(lead)
            else:
                lead["nexus_brand"] = args.brand.upper()
            enriched.append(lead)

            # Rate limit between enrichments
            if i < len(leads) - 1:
                time.sleep(2)

        leads = enriched
        print(f"\n  ✅ Enrichment complete\n")
    else:
        # Still score and assign brand
        for lead in leads:
            lead = score_lead(lead)
            if args.brand == "auto":
                lead = assign_brand(lead)
            else:
                lead["nexus_brand"] = args.brand.upper()

    # Summary
    scores = [l.get("nexus_lead_score", 0) for l in leads]
    hot = sum(1 for s in scores if s >= 80)
    warm = sum(1 for s in scores if 60 <= s < 80)
    cool = sum(1 for s in scores if 40 <= s < 60)
    cold = sum(1 for s in scores if s < 40)

    print(f"  📊 Scoring Summary:")
    print(f"     🔥 Hot (80-100):  {hot}")
    print(f"     🟡 Warm (60-79):  {warm}")
    print(f"     🔵 Cool (40-59):  {cool}")
    print(f"     ⚪ Cold (0-39):   {cold}")

    tbf = sum(1 for l in leads if l.get("nexus_brand") == "TBF")
    dft = sum(1 for l in leads if l.get("nexus_brand") == "DFT")
    print(f"\n  🏷️  Brand Assignment:")
    print(f"     TBF: {tbf} | DFT: {dft}")

    # Save enriched output
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    output_path = OUTPUT_DIR / f"enriched_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump({
            "metadata": {
                "source": args.input,
                "total": len(leads),
                "enriched_at": datetime.utcnow().isoformat(),
                "hot": hot, "warm": warm, "cool": cool, "cold": cold,
                "tbf": tbf, "dft": dft,
            },
            "leads": leads,
        }, f, indent=2)
    print(f"\n  💾 Enriched data saved: {output_path}")

    # Import to GHL
    if args.import_ghl:
        if not GHL_API_TOKEN or not GHL_LOCATION_ID:
            print("\n  ❌ GHL credentials not set. Skipping import.")
        else:
            print(f"\n  📤 Importing {len(leads)} leads to GHL...\n")
            field_map = load_field_map()
            imported = 0
            errors = 0

            for i, lead in enumerate(leads):
                company = lead.get("company_name", lead.get("contact_name", "?"))
                print(f"  [{i+1}/{len(leads)}] {company}...", end=" ")
                contact_id = import_to_ghl(lead, args.pipeline_id, args.stage_id, field_map)
                if contact_id:
                    print(f"✅ {contact_id[:12]}...")
                    imported += 1
                else:
                    print("⚠️")
                    errors += 1
                time.sleep(0.2)

            print(f"\n  {'='*50}")
            print(f"  ✅ GHL Import: {imported} imported, {errors} errors")
            print(f"  {'='*50}")

    print(f"\n  🎯 Top prospects to outreach first:")
    top = sorted(leads, key=lambda l: l.get("nexus_lead_score", 0), reverse=True)[:5]
    for l in top:
        print(f"     • {l.get('company_name', '?')} — Score: {l.get('nexus_lead_score', 0)} ({l.get('nexus_brand', '?')}) — {l.get('prospect_temperature', '?')}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
