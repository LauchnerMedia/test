#!/usr/bin/env python3
"""
Universal CSV/List Importer — Nexus BDR Agent
===============================================
Imports leads from ANY CSV format with smart column mapping.
Auto-detects columns, normalizes data, and outputs standardized JSON
ready for the enrichment pipeline.

Usage:
    python3 csv_importer.py --input leads.csv --preview
    python3 csv_importer.py --input leads.csv --output standardized.json
    python3 csv_importer.py --input leads.csv --enrich --import-ghl
    python3 csv_importer.py --input leads.xlsx --sheet "Sheet1" --output standardized.json

Accepts: .csv, .tsv, .xlsx, .xls
"""

import os
import sys
import json
import csv
import re
import argparse
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


# Column name variations we recognize
COLUMN_MAP = {
    "company_name": [
        "company", "company_name", "company name", "organization", "org",
        "business", "business name", "account", "account name", "firm",
    ],
    "contact_name": [
        "name", "contact_name", "contact name", "full name", "fullname",
        "person", "contact", "person name",
    ],
    "first_name": [
        "first_name", "first name", "firstname", "first", "fname", "given name",
    ],
    "last_name": [
        "last_name", "last name", "lastname", "last", "lname", "surname", "family name",
    ],
    "email": [
        "email", "email_address", "email address", "e-mail", "emailaddress",
        "work email", "business email", "contact email",
    ],
    "phone": [
        "phone", "phone_number", "phone number", "telephone", "tel", "mobile",
        "cell", "work phone", "business phone", "direct phone",
    ],
    "title": [
        "title", "job_title", "job title", "job_role", "role", "position",
        "designation", "function",
    ],
    "domain": [
        "domain", "website", "web", "url", "site", "company_website",
        "company website", "homepage", "company_url",
    ],
    "city": [
        "city", "town", "municipality",
    ],
    "state": [
        "state", "province", "region", "state_code", "state code",
        "state/province",
    ],
    "country": [
        "country", "nation", "country_code",
    ],
    "address": [
        "address", "street", "street_address", "location", "address1",
    ],
    "zip": [
        "zip", "zipcode", "zip_code", "postal", "postal_code", "postcode",
    ],
    "linkedin": [
        "linkedin", "linkedin_url", "linkedin url", "linkedin_profile",
        "li_url", "person linkedin", "person linkedin url",
    ],
    "instagram": [
        "instagram", "ig", "instagram_handle", "ig_handle",
    ],
    "industry": [
        "industry", "sector", "vertical", "category", "business_type",
    ],
    "employees": [
        "employees", "employee_count", "employee count", "company_size",
        "headcount", "num_employees", "size", "# employees",
    ],
    "revenue": [
        "revenue", "annual_revenue", "annual revenue", "estimated_revenue",
    ],
    "source": [
        "source", "lead_source", "lead source", "origin", "channel",
    ],
    "notes": [
        "notes", "description", "comments", "memo", "remarks",
    ],
    "license_number": [
        "license", "license_number", "license number", "license_no",
        "permit", "permit_number",
    ],
    "license_type": [
        "license_type", "license type", "permit_type",
    ],
    "seniority": [
        "seniority", "seniority level",
    ],
    "departments": [
        "departments", "department",
    ],
    "work_phone": [
        "work direct phone", "work phone", "direct phone", "direct dial",
    ],
    "mobile_phone": [
        "mobile phone", "mobile", "cell phone", "cell",
    ],
    "corporate_phone": [
        "corporate phone", "company phone", "office phone",
    ],
    "keywords": [
        "keywords", "tags", "interests",
    ],
    "technologies": [
        "technologies", "tech stack", "tools",
    ],
    "total_funding": [
        "total funding", "total_funding", "funding",
    ],
    "latest_funding": [
        "latest funding", "latest_funding", "last funding round",
    ],
    "latest_funding_amount": [
        "latest funding amount", "latest_funding_amount", "last funding amount",
    ],
    "company_linkedin": [
        "company linkedin url", "company linkedin", "company_linkedin",
    ],
    "facebook": [
        "facebook url", "facebook", "fb_url",
    ],
    "twitter": [
        "twitter url", "twitter", "x_url",
    ],
    "email_status": [
        "email status", "email_status", "verification status",
    ],
    "email_confidence": [
        "email confidence", "email_confidence", "confidence",
    ],
    "apollo_stage": [
        "stage", "apollo_stage", "contact stage",
    ],
    "apollo_lists": [
        "lists", "apollo_lists",
    ],
    "last_contacted": [
        "last contacted", "last_contacted", "last contact date",
    ],
    "email_sent": [
        "email sent", "email_sent", "emails sent",
    ],
    "email_open": [
        "email open", "email_open", "emails opened",
    ],
    "replied": [
        "replied", "reply", "responded",
    ],
    "subsidiary_of": [
        "subsidiary of", "subsidiary_of", "parent company",
    ],
}


def detect_columns(headers):
    """Map CSV headers to our standard field names."""
    mapping = {}
    headers_lower = [h.strip().lower() for h in headers]

    for our_field, variations in COLUMN_MAP.items():
        for i, header in enumerate(headers_lower):
            if header in variations:
                mapping[headers[i]] = our_field
                break

    # Report unmapped columns
    unmapped = [h for h in headers if h not in mapping]
    return mapping, unmapped


def load_csv(path, encoding="utf-8-sig"):
    """Load CSV with auto-encoding detection."""
    encodings = [encoding, "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(path, newline='', encoding=enc) as f:
                # Detect delimiter
                sample = f.read(4096)
                f.seek(0)
                if '\t' in sample and sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                else:
                    delimiter = ','
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
                headers = reader.fieldnames or []
                return headers, rows
        except UnicodeDecodeError:
            continue
    print(f"  ❌ Could not decode file with any known encoding")
    sys.exit(1)


def load_excel(path, sheet=None):
    """Load Excel file."""
    try:
        import openpyxl
    except ImportError:
        print("  📦 Installing openpyxl...")
        os.system("pip install openpyxl --break-system-packages -q")
        import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb[sheet] if sheet else wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(h or f"col_{i}") for i, h in enumerate(rows[0])]
    data = []
    for row in rows[1:]:
        data.append(dict(zip(headers, [str(c) if c is not None else "" for c in row])))
    return headers, data


def normalize_lead(row, column_mapping):
    """Normalize a row into standard lead format."""
    lead = {}

    # Map columns
    for orig_col, our_field in column_mapping.items():
        val = row.get(orig_col, "").strip()
        if val:
            lead[our_field] = val

    # Handle first/last name → contact_name
    if "first_name" in lead or "last_name" in lead:
        first = lead.pop("first_name", "")
        last = lead.pop("last_name", "")
        lead["contact_name"] = f"{first} {last}".strip()

    # Best phone: work > mobile > corporate > generic
    if not lead.get("phone"):
        for phone_field in ["work_phone", "mobile_phone", "corporate_phone"]:
            if lead.get(phone_field):
                lead["phone"] = lead[phone_field]
                break
    # Clean up extra phone fields but keep them
    for pf in ["work_phone", "mobile_phone", "corporate_phone"]:
        phone_val = lead.get(pf, "")
        if phone_val:
            lead[pf] = re.sub(r'[^\d+\-() ]', '', phone_val)

    # Clean domain
    domain = lead.get("domain", "")
    if domain:
        domain = domain.replace("http://", "").replace("https://", "").replace("www.", "").strip("/")
        lead["domain"] = domain

    # Clean phone
    phone = lead.get("phone", "")
    if phone:
        lead["phone"] = re.sub(r'[^\d+\-() ]', '', phone)

    # Clean email
    email = lead.get("email", "")
    if email:
        lead["email"] = email.lower().strip()

    # Map seniority to decision_maker_level
    seniority = lead.get("seniority", "").lower()
    if seniority:
        seniority_map = {
            "c_suite": "C-Suite", "owner": "C-Suite", "founder": "C-Suite",
            "vp": "VP", "vice_president": "VP",
            "director": "Director",
            "manager": "Manager",
            "senior": "Manager",
            "entry": "Individual", "intern": "Individual",
        }
        lead["decision_maker_level"] = seniority_map.get(seniority, "Individual")

    # Normalize state codes
    state = lead.get("state", "")
    if len(state) > 2:
        state_codes = {
            "california": "CA", "colorado": "CO", "oregon": "OR", "washington": "WA",
            "michigan": "MI", "oklahoma": "OK", "arizona": "AZ", "nevada": "NV",
            "illinois": "IL", "massachusetts": "MA", "new jersey": "NJ", "new york": "NY",
            "missouri": "MO", "maryland": "MD", "ohio": "OH", "maine": "ME",
            "montana": "MT", "virginia": "VA", "new mexico": "NM", "connecticut": "CT",
            "vermont": "VT", "rhode island": "RI", "delaware": "DE", "minnesota": "MN",
            "florida": "FL", "texas": "TX", "pennsylvania": "PA",
        }
        lead["state"] = state_codes.get(state.lower(), state[:2].upper())

    # Add metadata
    lead["source"] = lead.get("source", "csv_import")
    lead["imported_at"] = datetime.utcnow().isoformat()

    return lead


def deduplicate(leads):
    """Remove duplicates by email or company+name combo."""
    seen_emails = set()
    seen_company_names = set()
    unique = []

    for lead in leads:
        email = lead.get("email", "").lower()
        company = lead.get("company_name", "").lower()
        name = lead.get("contact_name", "").lower()
        combo = f"{company}|{name}"

        if email and email in seen_emails:
            continue
        if combo and combo in seen_company_names and combo != "|":
            continue

        if email:
            seen_emails.add(email)
        if combo != "|":
            seen_company_names.add(combo)
        unique.append(lead)

    return unique


def main():
    parser = argparse.ArgumentParser(description="Universal CSV Importer — Nexus BDR")
    parser.add_argument("--input", required=True, help="CSV, TSV, or XLSX file")
    parser.add_argument("--output", help="Output JSON path (default: auto-generated)")
    parser.add_argument("--preview", action="store_true", help="Preview column mapping and first 5 rows")
    parser.add_argument("--sheet", help="Excel sheet name (for xlsx)")
    parser.add_argument("--enrich", action="store_true", help="Auto-run enrichment pipeline after import")
    parser.add_argument("--import-ghl", action="store_true", help="Auto-import to GHL after enrichment")
    parser.add_argument("--source-label", default="csv_import", help="Source label for tracking")

    args = parser.parse_args()
    input_path = Path(args.input)

    print(f"\n{'='*60}")
    print(f"  📥 NEXUS BDR — Universal List Importer")
    print(f"  Input: {input_path.name}")
    print(f"{'='*60}\n")

    # Load file
    if input_path.suffix in (".xlsx", ".xls"):
        headers, rows = load_excel(input_path, args.sheet)
    else:
        headers, rows = load_csv(input_path)

    print(f"  📊 Loaded: {len(rows)} rows, {len(headers)} columns\n")

    # Detect columns
    column_mapping, unmapped = detect_columns(headers)

    print(f"  🔄 Column Mapping:")
    for orig, mapped in column_mapping.items():
        print(f"     ✅ '{orig}' → {mapped}")
    if unmapped:
        print(f"\n  ⚠️  Unmapped columns (will be ignored):")
        for col in unmapped:
            print(f"     ❓ '{col}'")

    if args.preview:
        print(f"\n  👁️  Preview (first 5 rows):\n")
        for i, row in enumerate(rows[:5]):
            lead = normalize_lead(row, column_mapping)
            print(f"  [{i+1}] {lead.get('company_name', '?')} | {lead.get('contact_name', '?')} | {lead.get('email', '?')} | {lead.get('state', '?')}")
        print(f"\n  Total rows: {len(rows)}")
        print(f"  Run without --preview to import.\n")
        return

    # Normalize all leads
    leads = []
    for row in rows:
        lead = normalize_lead(row, column_mapping)
        lead["source"] = args.source_label
        if lead.get("company_name") or lead.get("contact_name") or lead.get("email"):
            leads.append(lead)

    print(f"\n  ✅ Normalized: {len(leads)} valid leads")

    # Dedup
    before = len(leads)
    leads = deduplicate(leads)
    dupes = before - len(leads)
    if dupes:
        print(f"  🔄 Deduped: removed {dupes} duplicates → {len(leads)} unique")

    # Stats
    with_email = sum(1 for l in leads if l.get("email"))
    with_phone = sum(1 for l in leads if l.get("phone"))
    with_domain = sum(1 for l in leads if l.get("domain"))
    states = {}
    for l in leads:
        s = l.get("state", "Unknown")
        states[s] = states.get(s, 0) + 1

    print(f"\n  📊 Data Quality:")
    print(f"     📧 With email: {with_email}/{len(leads)} ({100*with_email//len(leads) if leads else 0}%)")
    print(f"     📱 With phone: {with_phone}/{len(leads)} ({100*with_phone//len(leads) if leads else 0}%)")
    print(f"     🌐 With website: {with_domain}/{len(leads)} ({100*with_domain//len(leads) if leads else 0}%)")
    print(f"\n  🗺️  By State:")
    for state, count in sorted(states.items(), key=lambda x: -x[1]):
        print(f"     {state}: {count}")

    # Save
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    output_path = Path(args.output) if args.output else OUTPUT_DIR / f"imported_{input_path.stem}_{timestamp}.json"

    output_data = {
        "metadata": {
            "source_file": str(input_path),
            "total_leads": len(leads),
            "with_email": with_email,
            "with_phone": with_phone,
            "with_domain": with_domain,
            "imported_at": datetime.utcnow().isoformat(),
            "source_label": args.source_label,
        },
        "leads": leads,
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n  💾 Saved: {output_path}")

    # Auto-enrich
    if args.enrich:
        print(f"\n  🔬 Starting enrichment pipeline...\n")
        enrich_cmd = f"python3 {SCRIPT_DIR}/enrich_pipeline.py --input \"{output_path}\""
        if args.import_ghl:
            enrich_cmd += " --import-ghl"
        os.system(enrich_cmd)

    print(f"\n{'='*60}")
    print(f"  ✅ Import complete: {len(leads)} leads ready")
    print(f"  📂 File: {output_path}")
    print(f"\n  Next steps:")
    print(f"  1. Enrich: python3 scripts/enrich_pipeline.py --input \"{output_path}\" --brand auto --import-ghl")
    print(f"  2. Monitor: python3 scripts/trigger_monitor.py --build-watchlist && python3 scripts/trigger_monitor.py --scan-all")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
