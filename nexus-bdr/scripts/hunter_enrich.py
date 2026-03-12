#!/usr/bin/env python3
"""
Hunter.io Email Enrichment Script — Nexus BDR Agent
Enriches leads with verified email addresses via Hunter.io API.

Usage:
    python3 hunter_enrich.py --input outputs/leads_tbf_20260303_1400.json
    python3 hunter_enrich.py --input leads.json --output enriched.json --min-confidence 80

Environment:
    HUNTER_API_KEY — Your Hunter.io API key (required)
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

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
HUNTER_FINDER_URL = "https://api.hunter.io/v2/email-finder"
HUNTER_VERIFY_URL = "https://api.hunter.io/v2/email-verifier"

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR.parent / "outputs"


def find_email(first_name: str, last_name: str, domain: str) -> dict:
    """Use Hunter email-finder to discover an email address."""
    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": HUNTER_API_KEY,
    }
    try:
        resp = requests.get(HUNTER_FINDER_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "email": data.get("email", ""),
            "confidence": data.get("confidence", 0),
            "type": data.get("type", ""),
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "position": data.get("position", ""),
            "sources_count": len(data.get("sources", [])),
        }
    except requests.exceptions.RequestException as e:
        return {"email": "", "confidence": 0, "error": str(e)}


def verify_email(email: str) -> dict:
    """Verify an existing email address via Hunter."""
    params = {"email": email, "api_key": HUNTER_API_KEY}
    try:
        resp = requests.get(HUNTER_VERIFY_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "status": data.get("status", "unknown"),
            "result": data.get("result", "unknown"),
            "score": data.get("score", 0),
            "disposable": data.get("disposable", False),
            "webmail": data.get("webmail", False),
        }
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}


def enrich_leads(leads: list, min_confidence: int = 70) -> list:
    """Enrich a list of leads with Hunter email data."""
    if not HUNTER_API_KEY:
        print("ERROR: HUNTER_API_KEY environment variable not set.")
        print("Get yours at: https://hunter.io/api-keys")
        sys.exit(1)

    total = len(leads)
    enriched_count = 0
    verified_count = 0
    skipped_count = 0

    for i, lead in enumerate(leads):
        first = lead.get("first_name", "")
        last = lead.get("last_name", "")
        domain = lead.get("company_domain", "")
        existing_email = lead.get("email", "")

        # If Apollo already provided a verified email, just verify it
        if existing_email and lead.get("email_status") == "verified":
            lead["email_verified"] = True
            lead["hunter_email"] = existing_email
            verified_count += 1
            skipped_count += 1
            continue

        # If we have an email but it's not verified, verify it
        if existing_email:
            print(f"  [{i+1}/{total}] Verifying {existing_email}...")
            result = verify_email(existing_email)
            lead["hunter_verification"] = result
            if result.get("score", 0) >= min_confidence:
                lead["email_verified"] = True
                lead["hunter_email"] = existing_email
                verified_count += 1
            else:
                lead["email_verified"] = False
            enriched_count += 1
            time.sleep(0.5)
            continue

        # No email — try to find one via Hunter
        if not domain or not first or not last:
            print(f"  [{i+1}/{total}] Skipping {lead.get('full_name', '?')} — missing name or domain")
            skipped_count += 1
            continue

        print(f"  [{i+1}/{total}] Finding email for {first} {last} @ {domain}...")
        result = find_email(first, last, domain)

        if result.get("email"):
            lead["hunter_email"] = result["email"]
            lead["hunter_confidence"] = result["confidence"]
            lead["email_verified"] = result["confidence"] >= min_confidence
            enriched_count += 1
            if lead["email_verified"]:
                verified_count += 1
        else:
            lead["hunter_email"] = ""
            lead["email_verified"] = False
            lead["hunter_error"] = result.get("error", "No email found")

        time.sleep(0.5)  # Hunter rate limit: ~15 req/sec

    print(f"\n  [Hunter] Enrichment complete:")
    print(f"    Processed: {total}")
    print(f"    Enriched:  {enriched_count}")
    print(f"    Verified:  {verified_count} (confidence >= {min_confidence}%)")
    print(f"    Skipped:   {skipped_count}")

    return leads


def main():
    parser = argparse.ArgumentParser(description="Hunter.io Email Enrichment — Nexus BDR Agent")
    parser.add_argument("--input", required=True, help="Input JSON file from apollo_search.py")
    parser.add_argument("--output", default=None, help="Output file (default: enriched_YYYYMMDD_HHMM.json)")
    parser.add_argument("--min-confidence", type=int, default=70,
                        help="Minimum Hunter confidence score to mark as verified (default: 70)")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  NEXUS BDR AGENT — Hunter.io Email Enrichment")
    print(f"  Input: {args.input}")
    print(f"  Min Confidence: {args.min_confidence}%")
    print(f"{'='*60}\n")

    # Load leads
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    with open(input_path) as f:
        data = json.load(f)

    leads = data.get("leads", [])
    metadata = data.get("metadata", {})
    print(f"  Loaded {len(leads)} leads from {args.input}\n")

    # Enrich
    enriched_leads = enrich_leads(leads, args.min_confidence)

    # Update metadata
    metadata["enriched_at"] = datetime.utcnow().isoformat()
    metadata["enrichment_stats"] = {
        "total": len(enriched_leads),
        "verified_emails": sum(1 for l in enriched_leads if l.get("email_verified")),
        "unverified": sum(1 for l in enriched_leads if not l.get("email_verified")),
        "min_confidence_threshold": args.min_confidence,
    }

    # Save
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    output_path = args.output or str(OUTPUT_DIR / f"enriched_{timestamp}.json")

    with open(output_path, "w") as f:
        json.dump({"metadata": metadata, "leads": enriched_leads}, f, indent=2)

    print(f"\n  [Output] Saved to: {output_path}")

    # Summary
    verified = [l for l in enriched_leads if l.get("email_verified")]
    hot_verified = [l for l in verified if l.get("tier") == "hot"]

    print(f"\n  📊 Enrichment Summary:")
    print(f"  ✅ Verified emails: {len(verified)}/{len(enriched_leads)}")
    print(f"  🔥 Hot leads with verified email: {len(hot_verified)}")
    print(f"\n  Ready for outreach generation via OpenClaw.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
