#!/usr/bin/env python3
"""
Apollo.io Lead Discovery Script — Nexus BDR Agent
Searches Apollo's people database using ICP profile parameters.

Usage:
    python3 apollo_search.py --icp tbf_cannabis_manufacturers --max-leads 50
    python3 apollo_search.py --icp dft_extract_artists --output leads.json
    python3 apollo_search.py --titles "CEO" "Founder" --keywords "cannabis extraction" --max-leads 25

Environment:
    APOLLO_API_KEY — Your Apollo.io API key (required)
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests")
    sys.exit(1)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = SCRIPT_DIR.parent / "config"
OUTPUT_DIR = SCRIPT_DIR.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_icp_profile(profile_name: str) -> dict:
    """Load ICP profile from config/icp-profiles.json."""
    config_path = CONFIG_DIR / "icp-profiles.json"
    if not config_path.exists():
        print(f"ERROR: ICP config not found at {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    profiles = config.get("icp_profiles", {})
    if profile_name not in profiles:
        available = ", ".join(profiles.keys())
        print(f"ERROR: ICP profile '{profile_name}' not found. Available: {available}")
        sys.exit(1)

    return profiles[profile_name]


def search_apollo(icp_profile: dict, max_leads: int = 100) -> list:
    """Execute Apollo people search using ICP parameters."""
    if not APOLLO_API_KEY:
        print("ERROR: APOLLO_API_KEY environment variable not set.")
        print("Get yours at: https://app.apollo.io → Settings → API Keys")
        sys.exit(1)

    params = icp_profile.get("apollo_params", {})
    per_page = min(params.get("per_page", 25), 100)
    max_pages = params.get("max_pages", 4)
    max_pages = min(max_pages, (max_leads + per_page - 1) // per_page)

    all_leads = []

    for page in range(1, max_pages + 1):
        if len(all_leads) >= max_leads:
            break

        print(f"  [Apollo] Searching page {page}/{max_pages}...")

        # Combine keywords and industries into one keyword search
        keywords = params.get("keywords", [])
        industries = params.get("industries", [])
        all_keywords = keywords + industries

        payload = {
            "page": page,
            "per_page": per_page,
        }

        # Only include non-empty arrays
        titles = params.get("person_titles", [])
        if titles:
            payload["person_titles"] = titles

        locations = params.get("locations", [])
        if locations:
            payload["person_locations"] = locations

        employee_ranges = params.get("employee_ranges", [])
        if employee_ranges:
            payload["organization_num_employees_ranges"] = employee_ranges

        if all_keywords:
            payload["q_keywords"] = " ".join(all_keywords)

        # Debug: show what we're sending
        debug_payload = {k: v for k, v in payload.items()}
        print(f"  [Apollo] Payload: {json.dumps(debug_payload, indent=2)}")

        try:
            headers = {
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": APOLLO_API_KEY,
            }
            resp = requests.post(APOLLO_SEARCH_URL, json=payload, headers=headers, timeout=30)

            # If we get an error, print the response body for debugging
            if resp.status_code != 200:
                print(f"  [Apollo] Status: {resp.status_code}")
                print(f"  [Apollo] Response: {resp.text[:500]}")

            resp.raise_for_status()
            data = resp.json()

            people = data.get("people", [])
            if not people:
                print(f"  [Apollo] No results on page {page}. Stopping.")
                break

            for person in people:
                org = person.get("organization", {}) or {}
                lead = {
                    "source": "apollo",
                    "apollo_id": person.get("id", ""),
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "full_name": person.get("name", ""),
                    "title": person.get("title", ""),
                    "email": person.get("email", ""),
                    "email_status": person.get("email_status", ""),
                    "phone": person.get("phone_numbers", [{}])[0].get("raw_number", "") if person.get("phone_numbers") else "",
                    "linkedin_url": person.get("linkedin_url", ""),
                    "city": person.get("city", ""),
                    "state": person.get("state", ""),
                    "country": person.get("country", ""),
                    "company_name": org.get("name", ""),
                    "company_domain": org.get("primary_domain", ""),
                    "company_website": org.get("website_url", ""),
                    "company_industry": org.get("industry", ""),
                    "company_size": org.get("estimated_num_employees", 0),
                    "company_linkedin": org.get("linkedin_url", ""),
                    "company_description": (org.get("short_description", "") or "")[:300],
                    "company_keywords": org.get("keywords", []),
                    "discovered_at": datetime.utcnow().isoformat(),
                    "icp_profile": icp_profile.get("description", ""),
                    "brand": icp_profile.get("brand", ""),
                    "lead_score": 0,  # Will be calculated in scoring step
                    "email_verified": False,
                    "hunter_email": "",
                    "status": "new",
                }
                all_leads.append(lead)

            print(f"  [Apollo] Found {len(people)} leads on page {page}.")
            time.sleep(1)  # Rate limit: ~100 req/min

        except requests.exceptions.RequestException as e:
            print(f"  [Apollo] Error on page {page}: {e}")
            break

    # Deduplicate by email or full_name + company
    seen = set()
    unique_leads = []
    for lead in all_leads[:max_leads]:
        key = lead["email"] or f"{lead['full_name']}|{lead['company_name']}"
        if key and key not in seen:
            seen.add(key)
            unique_leads.append(lead)

    print(f"  [Apollo] Total unique leads: {len(unique_leads)}")
    return unique_leads


def score_lead(lead: dict, icp_profile: dict) -> int:
    """Basic scoring based on ICP profile criteria. Returns 0-100."""
    score = 0
    adjustments = icp_profile.get("scoring_adjustments", {})

    # Title scoring (25 points max)
    title = (lead.get("title", "") or "").lower()
    title_boosts = [t.lower() for t in adjustments.get("title_boost", [])]
    if any(boost in title for boost in title_boosts):
        score += 25
    elif any(level in title for level in ["manager", "lead", "senior"]):
        score += 15
    elif title:
        score += 5

    # Company size scoring (20 points max)
    size = lead.get("company_size", 0) or 0
    ideal_range = adjustments.get("size_ideal_range", [10, 500])
    if ideal_range[0] <= size <= ideal_range[1]:
        score += 20
    elif size > 0:
        score += 8

    # Industry/keyword scoring (20 points max)
    must_have = [k.lower() for k in adjustments.get("must_have_keywords", [])]
    nice_to_have = [k.lower() for k in adjustments.get("nice_to_have_keywords", [])]
    company_text = f"{lead.get('company_industry', '')} {lead.get('company_description', '')} {' '.join(lead.get('company_keywords', []))}".lower()

    must_matches = sum(1 for k in must_have if k in company_text)
    nice_matches = sum(1 for k in nice_to_have if k in company_text)

    if must_matches > 0:
        score += min(20, 10 + (must_matches * 5))
    if nice_matches > 0:
        score += min(10, nice_matches * 3)

    # Geography scoring (15 points max)
    state = lead.get("state", "")
    target_locations = [loc.lower() for loc in icp_profile.get("apollo_params", {}).get("locations", [])]
    if state.lower() in target_locations or "united states" in target_locations:
        score += 15
    elif lead.get("country", "").lower() == "united states":
        score += 8

    # Email availability (10 points max)
    if lead.get("email") and lead.get("email_status") == "verified":
        score += 10
    elif lead.get("email"):
        score += 5

    return min(100, score)


def main():
    parser = argparse.ArgumentParser(description="Apollo.io Lead Discovery — Nexus BDR Agent")
    parser.add_argument("--icp", default="tbf_cannabis_manufacturers",
                        help="ICP profile name from config/icp-profiles.json")
    parser.add_argument("--max-leads", type=int, default=100,
                        help="Maximum number of leads to return (default: 100)")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: outputs/leads_YYYYMMDD_HHMM.json)")
    parser.add_argument("--titles", nargs="+", help="Override ICP person titles")
    parser.add_argument("--keywords", nargs="+", help="Override ICP keywords")
    parser.add_argument("--locations", nargs="+", help="Override ICP locations")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  NEXUS BDR AGENT — Apollo Lead Discovery")
    print(f"  ICP Profile: {args.icp}")
    print(f"  Max Leads: {args.max_leads}")
    print(f"{'='*60}\n")

    # Load ICP profile
    icp_profile = load_icp_profile(args.icp)
    print(f"  Brand: {icp_profile['brand']}")
    print(f"  Target: {icp_profile['description']}\n")

    # Apply CLI overrides
    if args.titles:
        icp_profile["apollo_params"]["person_titles"] = args.titles
    if args.keywords:
        icp_profile["apollo_params"]["keywords"] = args.keywords
    if args.locations:
        icp_profile["apollo_params"]["locations"] = args.locations

    # Search Apollo
    leads = search_apollo(icp_profile, args.max_leads)

    # Score leads
    print("\n  [Scoring] Scoring leads against ICP criteria...")
    for lead in leads:
        lead["lead_score"] = score_lead(lead, icp_profile)

    # Sort by score descending
    leads.sort(key=lambda x: x["lead_score"], reverse=True)

    # Assign tiers
    for lead in leads:
        s = lead["lead_score"]
        if s >= 80:
            lead["tier"] = "hot"
        elif s >= 60:
            lead["tier"] = "warm"
        elif s >= 40:
            lead["tier"] = "cool"
        else:
            lead["tier"] = "cold"

    # Output
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    output_path = args.output or str(OUTPUT_DIR / f"leads_{args.icp}_{timestamp}.json")

    with open(output_path, "w") as f:
        json.dump({
            "metadata": {
                "icp_profile": args.icp,
                "brand": icp_profile["brand"],
                "total_leads": len(leads),
                "generated_at": datetime.utcnow().isoformat(),
                "tiers": {
                    "hot": sum(1 for l in leads if l["tier"] == "hot"),
                    "warm": sum(1 for l in leads if l["tier"] == "warm"),
                    "cool": sum(1 for l in leads if l["tier"] == "cool"),
                    "cold": sum(1 for l in leads if l["tier"] == "cold"),
                }
            },
            "leads": leads
        }, f, indent=2)

    print(f"\n  [Output] Saved {len(leads)} leads to: {output_path}")

    # Print summary table
    hot = [l for l in leads if l["tier"] == "hot"]
    warm = [l for l in leads if l["tier"] == "warm"]
    print(f"\n  📊 Results Summary:")
    print(f"  🔥 Hot (80-100):  {len(hot)}")
    print(f"  🟡 Warm (60-79):  {len(warm)}")
    print(f"  🔵 Cool (40-59):  {sum(1 for l in leads if l['tier'] == 'cool')}")
    print(f"  ⚪ Cold (0-39):   {sum(1 for l in leads if l['tier'] == 'cold')}")

    if hot:
        print(f"\n  🔥 Top Hot Leads:")
        for i, lead in enumerate(hot[:10], 1):
            print(f"  {i}. {lead['full_name']} — {lead['title']} @ {lead['company_name']} (Score: {lead['lead_score']})")

    print(f"\n{'='*60}")
    print(f"  Next steps: Run hunter_enrich.py to verify emails")
    print(f"  Then: Generate outreach sequences via OpenClaw")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
