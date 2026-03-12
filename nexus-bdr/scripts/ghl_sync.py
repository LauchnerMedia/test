#!/usr/bin/env python3
"""
GoHighLevel CRM Agent — Nexus BDR Agent
=========================================
Full CRM integration via GHL API V2 with Private Integration Token.
Handles contacts, opportunities/pipeline, conversations (email/SMS),
calendars, and workflow triggers.

Usage:
    python3 ghl_sync.py create-contact --first-name "Jane" --last-name "Smith" --email "jane@co.com" --company "Cookies" --phone "+15551234567"
    python3 ghl_sync.py search-contacts --query "jane@co.com"
    python3 ghl_sync.py tag-contact --contact-id "abc123" --tags "DFT Lead,Hot"
    python3 ghl_sync.py create-opportunity --contact-id "abc123" --pipeline-id "pid" --stage-id "sid" --name "Cookies - TBF"
    python3 ghl_sync.py get-pipelines
    python3 ghl_sync.py pipeline-report --pipeline-id "pid"
    python3 ghl_sync.py send-email --contact-id "abc123" --subject "Quick question" --body "Hey..."
    python3 ghl_sync.py send-sms --contact-id "abc123" --message "Hey, quick follow up..."
    python3 ghl_sync.py get-calendars
    python3 ghl_sync.py bulk-import --input prospects.json --pipeline-id "pid" --stage-id "sid"

Environment:
    GHL_API_TOKEN   — Private Integration Token (required)
    GHL_LOCATION_ID — Sub-account / Location ID (required)
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

# Config
GHL_API_TOKEN = os.getenv("GHL_API_TOKEN", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
ACTIVITY_LOG = OUTPUT_DIR / "activity-log.json"


def log_activity(action, details):
    """Log activity to JSON file."""
    activities = []
    if ACTIVITY_LOG.exists():
        try:
            activities = json.loads(ACTIVITY_LOG.read_text())
        except json.JSONDecodeError:
            activities = []
    activities.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "details": details,
        "agent": "ghl_sync",
    })
    ACTIVITY_LOG.write_text(json.dumps(activities, indent=2))


def ghl_request(method, endpoint, data=None, params=None):
    """Make authenticated GHL API request."""
    if not GHL_API_TOKEN:
        print("  ❌ GHL_API_TOKEN not set. Create a Private Integration at:")
        print("     GHL Settings → Integrations → Private Integrations → Create")
        sys.exit(1)

    url = f"{GHL_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {GHL_API_TOKEN}",
        "Content-Type": "application/json",
        "Version": GHL_API_VERSION,
    }

    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return {"error": f"Unknown method: {method}"}

        # Rate limit handling
        if resp.status_code == 429:
            print("  ⏳ Rate limited. Waiting 10 seconds...")
            time.sleep(10)
            return ghl_request(method, endpoint, data, params)

        if resp.status_code >= 400:
            print(f"  ❌ GHL API error {resp.status_code}: {resp.text[:300]}")
            return {"error": resp.text[:300], "status": resp.status_code}

        return resp.json() if resp.text else {"success": True}

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request error: {e}")
        return {"error": str(e)}


# ─── CONTACTS ──────────────────────────────────────────────

def create_contact(first_name, last_name, email=None, phone=None, company=None,
                   tags=None, source=None, custom_fields=None):
    """Create a new contact in GHL."""
    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "locationId": GHL_LOCATION_ID,
    }
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if company:
        payload["companyName"] = company
    if tags:
        payload["tags"] = tags if isinstance(tags, list) else [t.strip() for t in tags.split(",")]
    if source:
        payload["source"] = source
    if custom_fields:
        payload["customFields"] = custom_fields

    print(f"  📝 Creating contact: {first_name} {last_name} ({email or 'no email'})")
    result = ghl_request("POST", "/contacts/", data=payload)

    if "contact" in result:
        contact_id = result["contact"]["id"]
        print(f"  ✅ Created: {contact_id}")
        log_activity("create_contact", {
            "contact_id": contact_id,
            "name": f"{first_name} {last_name}",
            "email": email,
            "company": company,
        })
        return result["contact"]
    return result


def upsert_contact(first_name, last_name, email=None, phone=None, company=None,
                   tags=None, source=None):
    """Create or update contact (dedup by email/phone)."""
    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "locationId": GHL_LOCATION_ID,
    }
    if email:
        payload["email"] = email
    if phone:
        payload["phone"] = phone
    if company:
        payload["companyName"] = company
    if tags:
        payload["tags"] = tags if isinstance(tags, list) else [t.strip() for t in tags.split(",")]
    if source:
        payload["source"] = source

    print(f"  📝 Upserting contact: {first_name} {last_name}")
    result = ghl_request("POST", "/contacts/upsert", data=payload)

    if "contact" in result:
        contact_id = result["contact"]["id"]
        new = result.get("new", False)
        action = "created" if new else "updated"
        print(f"  ✅ Contact {action}: {contact_id}")
        log_activity("upsert_contact", {
            "contact_id": contact_id,
            "name": f"{first_name} {last_name}",
            "action": action,
        })
        return result["contact"]
    return result


def search_contacts(query=None, email=None, phone=None, limit=20):
    """Search contacts."""
    params = {"locationId": GHL_LOCATION_ID, "limit": limit}
    if query:
        params["query"] = query
    if email:
        params["email"] = email
    if phone:
        params["phone"] = phone

    result = ghl_request("GET", "/contacts/", params=params)
    contacts = result.get("contacts", [])
    print(f"  🔍 Found {len(contacts)} contacts")
    for c in contacts:
        name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
        print(f"     • {name} | {c.get('email', 'N/A')} | {c.get('companyName', 'N/A')} | ID: {c['id']}")
    return contacts


def get_contact(contact_id):
    """Get single contact details."""
    result = ghl_request("GET", f"/contacts/{contact_id}")
    return result.get("contact", result)


def tag_contact(contact_id, tags):
    """Add tags to a contact."""
    tag_list = tags if isinstance(tags, list) else [t.strip() for t in tags.split(",")]
    payload = {"tags": tag_list}
    result = ghl_request("PUT", f"/contacts/{contact_id}", data=payload)
    if "contact" in result:
        print(f"  🏷️  Tagged {contact_id}: {', '.join(tag_list)}")
        log_activity("tag_contact", {"contact_id": contact_id, "tags": tag_list})
    return result


def add_contact_to_workflow(contact_id, workflow_id):
    """Add contact to a workflow."""
    payload = {"eventStartTime": datetime.utcnow().isoformat()}
    result = ghl_request("POST", f"/contacts/{contact_id}/workflow/{workflow_id}", data=payload)
    if result.get("success") or "error" not in result:
        print(f"  🔄 Added {contact_id} to workflow {workflow_id}")
        log_activity("add_to_workflow", {"contact_id": contact_id, "workflow_id": workflow_id})
    return result


# ─── OPPORTUNITIES / PIPELINE ──────────────────────────────

def get_pipelines():
    """List all pipelines and their stages."""
    result = ghl_request("GET", "/opportunities/pipelines", params={"locationId": GHL_LOCATION_ID})
    pipelines = result.get("pipelines", [])
    print(f"  📊 {len(pipelines)} pipeline(s):\n")
    for p in pipelines:
        print(f"  Pipeline: {p['name']} (ID: {p['id']})")
        for stage in p.get("stages", []):
            print(f"     └─ {stage['name']} (ID: {stage['id']})")
        print()
    return pipelines


def create_opportunity(contact_id, pipeline_id, stage_id, name, monetary_value=0, source=None):
    """Create a new opportunity/deal."""
    payload = {
        "pipelineId": pipeline_id,
        "pipelineStageId": stage_id,
        "locationId": GHL_LOCATION_ID,
        "contactId": contact_id,
        "name": name,
        "status": "open",
    }
    if monetary_value:
        payload["monetaryValue"] = monetary_value
    if source:
        payload["source"] = source

    print(f"  💰 Creating opportunity: {name}")
    result = ghl_request("POST", "/opportunities/", data=payload)

    if "opportunity" in result:
        opp_id = result["opportunity"]["id"]
        print(f"  ✅ Created opportunity: {opp_id}")
        log_activity("create_opportunity", {
            "opportunity_id": opp_id,
            "name": name,
            "contact_id": contact_id,
            "pipeline_id": pipeline_id,
            "stage_id": stage_id,
        })
        return result["opportunity"]
    return result


def update_opportunity(opportunity_id, stage_id=None, status=None, monetary_value=None):
    """Update an opportunity (move stage, change status, etc)."""
    payload = {}
    if stage_id:
        payload["pipelineStageId"] = stage_id
    if status:
        payload["status"] = status
    if monetary_value is not None:
        payload["monetaryValue"] = monetary_value

    result = ghl_request("PUT", f"/opportunities/{opportunity_id}", data=payload)
    if "opportunity" in result:
        print(f"  ✅ Updated opportunity: {opportunity_id}")
        log_activity("update_opportunity", {"opportunity_id": opportunity_id, **payload})
    return result


def search_opportunities(pipeline_id, stage_id=None, status="open", limit=20):
    """Search opportunities in a pipeline."""
    params = {
        "locationId": GHL_LOCATION_ID,
        "pipelineId": pipeline_id,
        "limit": limit,
    }
    if stage_id:
        params["pipelineStageId"] = stage_id
    if status:
        params["status"] = status

    result = ghl_request("GET", "/opportunities/search", params=params)
    opps = result.get("opportunities", [])
    print(f"  📊 Found {len(opps)} opportunities")
    for o in opps:
        print(f"     • {o.get('name', '?')} | ${o.get('monetaryValue', 0)} | {o.get('status', '?')} | ID: {o['id']}")
    return opps


def pipeline_report(pipeline_id):
    """Generate pipeline report grouped by stage."""
    pipelines = get_pipelines()
    target = None
    for p in pipelines:
        if p["id"] == pipeline_id:
            target = p
            break

    if not target:
        print(f"  ❌ Pipeline {pipeline_id} not found")
        return

    print(f"\n  {'='*50}")
    print(f"  📊 PIPELINE REPORT: {target['name']}")
    print(f"  {'='*50}\n")

    total_value = 0
    total_opps = 0

    for stage in target.get("stages", []):
        opps = search_opportunities(pipeline_id, stage_id=stage["id"], limit=100)
        stage_value = sum(o.get("monetaryValue", 0) for o in opps)
        total_value += stage_value
        total_opps += len(opps)
        print(f"\n  📌 {stage['name']}: {len(opps)} deals (${stage_value:,.0f})")
        for o in opps:
            print(f"     • {o.get('name', '?')} — ${o.get('monetaryValue', 0):,.0f}")

    print(f"\n  {'─'*50}")
    print(f"  Total: {total_opps} opportunities | ${total_value:,.0f} pipeline value")
    print(f"  {'='*50}\n")


# ─── CONVERSATIONS (EMAIL/SMS) ─────────────────────────────

def send_email(contact_id, subject, body, from_email=None):
    """Send email to a contact via GHL conversations."""
    payload = {
        "type": "Email",
        "contactId": contact_id,
        "subject": subject,
        "html": body,
    }

    result = ghl_request("POST", "/conversations/messages", data=payload)
    if result.get("messageId") or "error" not in result:
        print(f"  📧 Email sent to {contact_id}: {subject}")
        log_activity("send_email", {"contact_id": contact_id, "subject": subject})
    return result


def send_sms(contact_id, message):
    """Send SMS to a contact via GHL conversations."""
    payload = {
        "type": "SMS",
        "contactId": contact_id,
        "message": message,
    }

    result = ghl_request("POST", "/conversations/messages", data=payload)
    if result.get("messageId") or "error" not in result:
        print(f"  📱 SMS sent to {contact_id}")
        log_activity("send_sms", {"contact_id": contact_id, "message_preview": message[:50]})
    return result


# ─── CALENDARS ──────────────────────────────────────────────

def get_calendars():
    """List all calendars."""
    result = ghl_request("GET", "/calendars/", params={"locationId": GHL_LOCATION_ID})
    calendars = result.get("calendars", [])
    print(f"  📅 {len(calendars)} calendar(s):")
    for cal in calendars:
        print(f"     • {cal.get('name', '?')} (ID: {cal['id']})")
    return calendars


def get_calendar_slots(calendar_id, start_date, end_date):
    """Get available appointment slots."""
    params = {
        "calendarId": calendar_id,
        "startDate": start_date,
        "endDate": end_date,
        "timezone": "America/Phoenix",
    }
    result = ghl_request("GET", f"/calendars/{calendar_id}/free-slots", params=params)
    slots = result.get("slots", result.get("availableSlots", []))
    print(f"  📅 {len(slots) if isinstance(slots, list) else 'Multiple'} slot(s) available")
    return slots


def create_appointment(calendar_id, contact_id, start_time, end_time, title="Discovery Call"):
    """Book an appointment."""
    payload = {
        "calendarId": calendar_id,
        "locationId": GHL_LOCATION_ID,
        "contactId": contact_id,
        "startTime": start_time,
        "endTime": end_time,
        "title": title,
        "appointmentStatus": "confirmed",
    }
    result = ghl_request("POST", "/calendars/events/appointments", data=payload)
    if "id" in result or "event" in result:
        print(f"  📅 Appointment booked: {title} at {start_time}")
        log_activity("create_appointment", {
            "contact_id": contact_id,
            "calendar_id": calendar_id,
            "start": start_time,
            "title": title,
        })
    return result


# ─── WORKFLOWS ──────────────────────────────────────────────

def get_workflows():
    """List available workflows."""
    result = ghl_request("GET", "/workflows/", params={"locationId": GHL_LOCATION_ID})
    workflows = result.get("workflows", [])
    print(f"  🔄 {len(workflows)} workflow(s):")
    for w in workflows:
        status = w.get("status", "unknown")
        print(f"     • {w.get('name', '?')} ({status}) — ID: {w['id']}")
    return workflows


# ─── BULK IMPORT ────────────────────────────────────────────

def bulk_import(input_file, pipeline_id=None, stage_id=None, tags=None, source="nexus-bdr-agent"):
    """Import prospects from JSON file into GHL as contacts + opportunities."""
    path = Path(input_file)
    if not path.exists():
        print(f"  ❌ File not found: {input_file}")
        return

    with open(path) as f:
        data = json.load(f)

    # Handle different JSON structures
    if "prospects" in data:
        prospects = data["prospects"]
    elif isinstance(data, list):
        prospects = data
    else:
        prospects = [data]

    print(f"  📦 Importing {len(prospects)} prospects into GHL...\n")

    imported = 0
    errors = 0
    tag_list = tags.split(",") if tags else []

    for p in prospects:
        first_name = p.get("contact_name", "Unknown").split()[0] if p.get("contact_name") else p.get("first_name", "Unknown")
        last_name = " ".join(p.get("contact_name", "").split()[1:]) if p.get("contact_name") else p.get("last_name", "")
        if not last_name:
            last_name = "(Unknown)"

        company = p.get("company_name", p.get("company", ""))
        email = p.get("email", "")
        phone = p.get("phone", "")

        # Build tags
        contact_tags = list(tag_list)
        brand = p.get("brand", "")
        if brand:
            contact_tags.append(brand)
        contact_tags.append(source)

        # Upsert if we have email or phone, otherwise create
        if email or phone:
            contact = upsert_contact(
                first_name=first_name,
                last_name=last_name,
                email=email if email else None,
                phone=phone if phone else None,
                company=company,
                tags=contact_tags,
                source=source,
            )
        else:
            contact = create_contact(
                first_name=first_name,
                last_name=last_name,
                company=company,
                tags=contact_tags,
                source=source,
            )

        if isinstance(contact, dict) and "id" in contact:
            imported += 1
            contact_id = contact["id"]

            # Create opportunity if pipeline specified
            if pipeline_id and stage_id:
                opp_name = f"{company} — {brand}" if brand else company
                create_opportunity(
                    contact_id=contact_id,
                    pipeline_id=pipeline_id,
                    stage_id=stage_id,
                    name=opp_name,
                    source=source,
                )
        else:
            errors += 1
            print(f"  ⚠️  Failed to import: {first_name} {last_name}")

        # Respect rate limits (100 per 10 sec)
        time.sleep(0.15)

    print(f"\n  {'='*50}")
    print(f"  ✅ Import complete: {imported} imported, {errors} errors")
    print(f"  {'='*50}\n")


# ─── CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="GoHighLevel CRM Agent — Nexus BDR")
    subparsers = parser.add_subparsers(dest="command")

    # create-contact
    cc = subparsers.add_parser("create-contact")
    cc.add_argument("--first-name", required=True)
    cc.add_argument("--last-name", required=True)
    cc.add_argument("--email")
    cc.add_argument("--phone")
    cc.add_argument("--company")
    cc.add_argument("--tags")
    cc.add_argument("--source", default="nexus-bdr-agent")

    # search-contacts
    sc = subparsers.add_parser("search-contacts")
    sc.add_argument("--query")
    sc.add_argument("--email")
    sc.add_argument("--phone")

    # tag-contact
    tc = subparsers.add_parser("tag-contact")
    tc.add_argument("--contact-id", required=True)
    tc.add_argument("--tags", required=True)

    # get-pipelines
    subparsers.add_parser("get-pipelines")

    # create-opportunity
    co = subparsers.add_parser("create-opportunity")
    co.add_argument("--contact-id", required=True)
    co.add_argument("--pipeline-id", required=True)
    co.add_argument("--stage-id", required=True)
    co.add_argument("--name", required=True)
    co.add_argument("--value", type=float, default=0)

    # update-opportunity
    uo = subparsers.add_parser("update-opportunity")
    uo.add_argument("--opportunity-id", required=True)
    uo.add_argument("--stage-id")
    uo.add_argument("--status")
    uo.add_argument("--value", type=float)

    # pipeline-report
    pr = subparsers.add_parser("pipeline-report")
    pr.add_argument("--pipeline-id", required=True)

    # send-email
    se = subparsers.add_parser("send-email")
    se.add_argument("--contact-id", required=True)
    se.add_argument("--subject", required=True)
    se.add_argument("--body", required=True)

    # send-sms
    ss = subparsers.add_parser("send-sms")
    ss.add_argument("--contact-id", required=True)
    ss.add_argument("--message", required=True)

    # get-calendars
    subparsers.add_parser("get-calendars")

    # get-workflows
    subparsers.add_parser("get-workflows")

    # bulk-import
    bi = subparsers.add_parser("bulk-import")
    bi.add_argument("--input", required=True)
    bi.add_argument("--pipeline-id")
    bi.add_argument("--stage-id")
    bi.add_argument("--tags")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if not GHL_LOCATION_ID:
        print("  ❌ GHL_LOCATION_ID not set.")
        print("  Find it: GHL → Settings → Business Profile → look for Location ID")
        print("  Or: GHL URL contains it: app.gohighlevel.com/location/{LOCATION_ID}/...")
        sys.exit(1)

    print(f"\n  {'='*50}")
    print(f"  🏢 GHL CRM Agent — {args.command}")
    print(f"  Location: {GHL_LOCATION_ID[:8]}...")
    print(f"  {'='*50}\n")

    if args.command == "create-contact":
        create_contact(args.first_name, args.last_name, args.email, args.phone, args.company, args.tags, args.source)
    elif args.command == "search-contacts":
        search_contacts(args.query, args.email, args.phone)
    elif args.command == "tag-contact":
        tag_contact(args.contact_id, args.tags)
    elif args.command == "get-pipelines":
        get_pipelines()
    elif args.command == "create-opportunity":
        create_opportunity(args.contact_id, args.pipeline_id, args.stage_id, args.name, args.value)
    elif args.command == "update-opportunity":
        update_opportunity(args.opportunity_id, args.stage_id, args.status, args.value)
    elif args.command == "pipeline-report":
        pipeline_report(args.pipeline_id)
    elif args.command == "send-email":
        send_email(args.contact_id, args.subject, args.body)
    elif args.command == "send-sms":
        send_sms(args.contact_id, args.message)
    elif args.command == "get-calendars":
        get_calendars()
    elif args.command == "get-workflows":
        get_workflows()
    elif args.command == "bulk-import":
        bulk_import(args.input, args.pipeline_id, args.stage_id, args.tags)

    print()


if __name__ == "__main__":
    main()
