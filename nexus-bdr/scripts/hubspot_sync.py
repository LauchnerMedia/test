#!/usr/bin/env python3
"""
HubSpot CRM Sync Script — Nexus BDR Agent
Creates/updates contacts and deals in HubSpot from BDR pipeline data.

Usage:
    python3 hubspot_sync.py create-contact --first-name "Jane" --last-name "Smith" --email "jane@cookies.com" --company "Cookies" --title "VP Manufacturing" --source "apollo_outbound" --lead-score 85 --brand "tbf"
    python3 hubspot_sync.py create-deal --contact-email "jane@cookies.com" --deal-name "Cookies - TBF Supply" --stage "introductory_meeting"
    python3 hubspot_sync.py update-deal --deal-id 12345 --stage "campaign_assessment"
    python3 hubspot_sync.py check-contact --email "jane@cookies.com"
    python3 hubspot_sync.py pipeline-report

Environment:
    HUBSPOT_API_KEY — Your HubSpot private app access token (required)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests")
    sys.exit(1)

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY", "")
HUBSPOT_BASE = "https://api.hubapi.com"

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR.parent / "outputs"
ACTIVITY_LOG = OUTPUT_DIR / "activity-log.json"

# HubSpot deal stage mapping (customize these IDs for your portal)
STAGE_MAP = {
    "introductory_meeting": "3136620276",
    "campaign_assessment": "3136620277",
    "strategy_proposal": "3136620278",
    "strategy_presentation": "3136620279",
    "objection_handling": "3136620280",
    "finalizing_terms": "3136620281",
    "closed_won": "3136621242",
    "closed_lost": "3136621243",
}


def headers():
    return {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json",
    }


def log_activity(action: str, details: dict):
    """Append activity to the activity log."""
    ACTIVITY_LOG.parent.mkdir(exist_ok=True)
    log = []
    if ACTIVITY_LOG.exists():
        try:
            with open(ACTIVITY_LOG) as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []

    log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "details": details,
    })

    with open(ACTIVITY_LOG, "w") as f:
        json.dump(log, f, indent=2)


def check_contact(email: str) -> dict | None:
    """Check if a contact exists in HubSpot by email."""
    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email,
            }]
        }],
        "properties": ["email", "firstname", "lastname", "company", "jobtitle", "hs_lead_status"],
        "limit": 1,
    }
    resp = requests.post(url, headers=headers(), json=payload, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def create_contact(first_name: str, last_name: str, email: str,
                   company: str = "", title: str = "", source: str = "",
                   lead_score: int = 0, brand: str = "") -> dict:
    """Create a new contact in HubSpot."""
    # Check for duplicate first
    existing = check_contact(email)
    if existing:
        print(f"  ⚠️  Contact already exists: {email} (ID: {existing['id']})")
        log_activity("contact_duplicate_found", {"email": email, "hubspot_id": existing["id"]})
        return existing

    url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts"
    properties = {
        "email": email,
        "firstname": first_name,
        "lastname": last_name,
        "company": company,
        "jobtitle": title,
        "hs_lead_status": "NEW",
    }

    # Add custom properties if your HubSpot portal has them
    # properties["lead_source"] = source
    # properties["lead_score_custom"] = str(lead_score)
    # properties["brand_interest"] = brand

    resp = requests.post(url, headers=headers(), json={"properties": properties}, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    print(f"  ✅ Contact created: {first_name} {last_name} ({email}) — ID: {result['id']}")
    log_activity("contact_created", {
        "hubspot_id": result["id"],
        "email": email,
        "company": company,
        "source": source,
        "brand": brand,
        "lead_score": lead_score,
    })
    return result


def create_deal(contact_email: str, deal_name: str, stage: str = "introductory_meeting",
                pipeline: str = "default", amount: str = "") -> dict:
    """Create a deal and associate it with a contact."""
    stage_id = STAGE_MAP.get(stage, stage)

    # Find contact
    contact = check_contact(contact_email)
    if not contact:
        print(f"  ⚠️  Contact not found for {contact_email}. Create contact first.")
        return {}

    url = f"{HUBSPOT_BASE}/crm/v3/objects/deals"
    properties = {
        "dealname": deal_name,
        "dealstage": stage_id,
        "pipeline": pipeline,
    }
    if amount:
        properties["amount"] = amount

    associations = [{
        "to": {"id": contact["id"]},
        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 3}]
    }]

    resp = requests.post(url, headers=headers(),
                         json={"properties": properties, "associations": associations},
                         timeout=15)
    resp.raise_for_status()
    result = resp.json()

    print(f"  ✅ Deal created: {deal_name} — Stage: {stage} — ID: {result['id']}")
    log_activity("deal_created", {
        "hubspot_id": result["id"],
        "deal_name": deal_name,
        "stage": stage,
        "contact_email": contact_email,
    })
    return result


def update_deal(deal_id: str, stage: str = None, amount: str = None) -> dict:
    """Update an existing deal's stage or amount."""
    url = f"{HUBSPOT_BASE}/crm/v3/objects/deals/{deal_id}"
    properties = {}
    if stage:
        properties["dealstage"] = STAGE_MAP.get(stage, stage)
    if amount:
        properties["amount"] = amount

    if not properties:
        print("  ⚠️  Nothing to update. Provide --stage or --amount.")
        return {}

    resp = requests.patch(url, headers=headers(), json={"properties": properties}, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    print(f"  ✅ Deal {deal_id} updated: {properties}")
    log_activity("deal_updated", {"hubspot_id": deal_id, "updates": properties})
    return result


def pipeline_report() -> dict:
    """Pull and display current pipeline status."""
    url = f"{HUBSPOT_BASE}/crm/v3/objects/deals/search"
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "dealstage",
                "operator": "NOT_IN",
                "values": [STAGE_MAP["closed_won"], STAGE_MAP["closed_lost"]],
            }]
        }],
        "properties": ["dealname", "dealstage", "amount", "closedate", "hubspot_owner_id"],
        "sorts": [{"propertyName": "dealstage", "direction": "ASCENDING"}],
        "limit": 100,
    }

    resp = requests.post(url, headers=headers(), json=payload, timeout=15)
    resp.raise_for_status()
    deals = resp.json().get("results", [])

    # Reverse map stage IDs to names
    stage_names = {v: k for k, v in STAGE_MAP.items()}

    print(f"\n  📊 Pipeline Report — {len(deals)} active deals\n")

    # Group by stage
    by_stage = {}
    total_value = 0
    for deal in deals:
        props = deal.get("properties", {})
        stage_id = props.get("dealstage", "")
        stage_name = stage_names.get(stage_id, stage_id)
        by_stage.setdefault(stage_name, []).append({
            "id": deal["id"],
            "name": props.get("dealname", ""),
            "amount": props.get("amount", "0"),
        })
        try:
            total_value += float(props.get("amount", 0) or 0)
        except ValueError:
            pass

    for stage_name in ["introductory_meeting", "campaign_assessment", "strategy_proposal",
                       "strategy_presentation", "objection_handling", "finalizing_terms"]:
        deals_in_stage = by_stage.get(stage_name, [])
        if deals_in_stage:
            print(f"  📍 {stage_name.replace('_', ' ').title()} ({len(deals_in_stage)})")
            for d in deals_in_stage:
                amt = f"${float(d['amount']):,.0f}" if d['amount'] and d['amount'] != "0" else "TBD"
                print(f"     • {d['name']} — {amt}")
            print()

    print(f"  💰 Total pipeline value: ${total_value:,.0f}")
    print()

    log_activity("pipeline_report", {"total_deals": len(deals), "total_value": total_value})
    return {"deals": deals, "total_value": total_value}


def bulk_import(input_file: str, brand: str = "tbf"):
    """Bulk import leads from a discovery JSON file into HubSpot as contacts."""
    with open(input_file) as f:
        data = json.load(f)

    leads = data.get("leads", [])
    # Only import verified, warm+ leads
    importable = [l for l in leads if l.get("email_verified") and l.get("lead_score", 0) >= 60]

    print(f"\n  Importing {len(importable)} qualified leads (of {len(leads)} total)...")

    created = 0
    existing = 0
    errors = 0

    for lead in importable:
        email = lead.get("hunter_email") or lead.get("email", "")
        if not email:
            continue
        try:
            result = create_contact(
                first_name=lead.get("first_name", ""),
                last_name=lead.get("last_name", ""),
                email=email,
                company=lead.get("company_name", ""),
                title=lead.get("title", ""),
                source="apollo_outbound",
                lead_score=lead.get("lead_score", 0),
                brand=brand,
            )
            if result.get("id"):
                created += 1
        except Exception as e:
            print(f"  ❌ Error importing {email}: {e}")
            errors += 1

        import time
        time.sleep(0.15)  # HubSpot rate limit: ~100 req/10sec

    print(f"\n  ✅ Import complete: {created} created, {existing} already existed, {errors} errors")


def main():
    if not HUBSPOT_API_KEY:
        print("ERROR: HUBSPOT_API_KEY environment variable not set.")
        print("Create a private app at: HubSpot → Settings → Integrations → Private Apps")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="HubSpot CRM Sync — Nexus BDR Agent")
    subparsers = parser.add_subparsers(dest="command")

    # create-contact
    cc = subparsers.add_parser("create-contact")
    cc.add_argument("--first-name", required=True)
    cc.add_argument("--last-name", required=True)
    cc.add_argument("--email", required=True)
    cc.add_argument("--company", default="")
    cc.add_argument("--title", default="")
    cc.add_argument("--source", default="apollo_outbound")
    cc.add_argument("--lead-score", type=int, default=0)
    cc.add_argument("--brand", default="tbf")

    # create-deal
    cd = subparsers.add_parser("create-deal")
    cd.add_argument("--contact-email", required=True)
    cd.add_argument("--deal-name", required=True)
    cd.add_argument("--stage", default="introductory_meeting")
    cd.add_argument("--pipeline", default="default")
    cd.add_argument("--amount", default="")

    # update-deal
    ud = subparsers.add_parser("update-deal")
    ud.add_argument("--deal-id", required=True)
    ud.add_argument("--stage", default=None)
    ud.add_argument("--amount", default=None)

    # check-contact
    chk = subparsers.add_parser("check-contact")
    chk.add_argument("--email", required=True)

    # pipeline-report
    subparsers.add_parser("pipeline-report")

    # bulk-import
    bi = subparsers.add_parser("bulk-import")
    bi.add_argument("--input", required=True)
    bi.add_argument("--brand", default="tbf")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  NEXUS BDR AGENT — HubSpot CRM Sync")
    print(f"  Command: {args.command}")
    print(f"{'='*60}\n")

    if args.command == "create-contact":
        create_contact(args.first_name, args.last_name, args.email,
                       args.company, args.title, args.source,
                       args.lead_score, args.brand)
    elif args.command == "create-deal":
        create_deal(args.contact_email, args.deal_name, args.stage,
                    args.pipeline, args.amount)
    elif args.command == "update-deal":
        update_deal(args.deal_id, args.stage, args.amount)
    elif args.command == "check-contact":
        contact = check_contact(args.email)
        if contact:
            print(f"  Found: {json.dumps(contact.get('properties', {}), indent=2)}")
        else:
            print(f"  No contact found for {args.email}")
    elif args.command == "pipeline-report":
        pipeline_report()
    elif args.command == "bulk-import":
        bulk_import(args.input, args.brand)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
