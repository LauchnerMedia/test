#!/usr/bin/env python3
"""
Company Research Script — Nexus BDR Agent
Gathers web-available intelligence on a prospect company for lead qualification
and outreach personalization.

Usage:
    python3 company_research.py --company "Cookies" --domain "cookiescalifornia.com"
    python3 company_research.py --company "Green Thumb Industries" --domain "gtigrows.com" --output research.json

Uses curl for web fetching (no additional dependencies beyond requests).
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def fetch_page_text(url: str, timeout: int = 10) -> str:
    """Fetch a URL and return text content (stripped of HTML tags, basic)."""
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A",
             "Mozilla/5.0 (compatible; research-bot)", url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        if result.returncode == 0:
            # Very basic HTML stripping
            import re
            text = re.sub(r'<script[^>]*>.*?</script>', '', result.stdout, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]  # Cap at 5000 chars
    except (subprocess.TimeoutExpired, Exception) as e:
        pass
    return ""


def research_company(company_name: str, domain: str) -> dict:
    """Gather available intelligence on a company."""
    print(f"  [Research] Researching {company_name} ({domain})...\n")

    research = {
        "company_name": company_name,
        "domain": domain,
        "researched_at": datetime.utcnow().isoformat(),
        "website_summary": "",
        "about_page": "",
        "careers_signals": [],
        "social_media": {},
        "personalization_hooks": [],
        "estimated_fit": "",
        "notes": "",
    }

    # 1. Homepage
    print(f"  [1/4] Fetching homepage...")
    homepage = fetch_page_text(f"https://{domain}")
    if homepage:
        research["website_summary"] = homepage[:2000]
        print(f"    ✅ Got {len(homepage)} chars")

        # Look for terpene/extraction signals
        signals = []
        keywords = ["terpene", "extract", "concentrate", "formulation", "manufacturing",
                     "infused", "edible", "vape", "cartridge", "distillate", "rosin",
                     "botanical", "flavor", "ingredient", "COA", "lab tested"]
        for kw in keywords:
            if kw.lower() in homepage.lower():
                signals.append(kw)
        if signals:
            research["personalization_hooks"].append(f"Website mentions: {', '.join(signals)}")
    else:
        print(f"    ⚠️  Could not fetch homepage")

    # 2. About page
    print(f"  [2/4] Fetching about page...")
    for about_path in ["/about", "/about-us", "/our-story", "/company"]:
        about = fetch_page_text(f"https://{domain}{about_path}")
        if about and len(about) > 200:
            research["about_page"] = about[:2000]
            print(f"    ✅ Found about page at {about_path}")
            break
    else:
        print(f"    ⚠️  No about page found")

    # 3. Careers page (hiring signals)
    print(f"  [3/4] Checking careers page...")
    for careers_path in ["/careers", "/jobs", "/hiring", "/work-with-us"]:
        careers = fetch_page_text(f"https://{domain}{careers_path}")
        if careers and len(careers) > 200:
            # Look for relevant role keywords
            role_keywords = ["formulation", "extraction", "R&D", "manufacturing",
                             "production", "quality", "scientist", "chemist",
                             "supply chain", "procurement"]
            for rk in role_keywords:
                if rk.lower() in careers.lower():
                    research["careers_signals"].append(rk)
            if research["careers_signals"]:
                research["personalization_hooks"].append(
                    f"Hiring for: {', '.join(research['careers_signals'])} — signals production scaling"
                )
                print(f"    ✅ Found hiring signals: {research['careers_signals']}")
            break
    else:
        print(f"    ⚠️  No careers page found")

    # 4. LinkedIn (basic check)
    print(f"  [4/4] Looking up LinkedIn...")
    research["social_media"]["linkedin_search"] = f"https://www.linkedin.com/company/{domain.split('.')[0]}"

    # Generate fit assessment
    hooks = research["personalization_hooks"]
    if len(hooks) >= 2:
        research["estimated_fit"] = "HIGH — multiple signals of terpene/formulation relevance"
    elif len(hooks) == 1:
        research["estimated_fit"] = "MEDIUM — some relevance signals found"
    else:
        research["estimated_fit"] = "LOW — limited signals, may need manual review"

    print(f"\n  📊 Research Summary for {company_name}:")
    print(f"  Fit: {research['estimated_fit']}")
    if hooks:
        for hook in hooks:
            print(f"  🎯 {hook}")
    print()

    return research


def main():
    parser = argparse.ArgumentParser(description="Company Research — Nexus BDR Agent")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--domain", required=True, help="Company website domain")
    parser.add_argument("--output", default=None, help="Output file path")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  NEXUS BDR AGENT — Company Research")
    print(f"  Company: {args.company}")
    print(f"  Domain: {args.domain}")
    print(f"{'='*60}\n")

    research = research_company(args.company, args.domain)

    # Save
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    company_slug = args.company.lower().replace(" ", "_")[:30]
    output_path = args.output or str(OUTPUT_DIR / f"research_{company_slug}_{timestamp}.json")

    with open(output_path, "w") as f:
        json.dump(research, f, indent=2)

    print(f"  💾 Saved to: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
