#!/usr/bin/env python3
"""
GHL Custom Properties Setup — Nexus BDR Agent
===============================================
Creates all custom contact and opportunity fields in GoHighLevel
for the comprehensive BDR data model.

Run once to set up, then never again (idempotent — skips existing fields).

Usage:
    python3 ghl_setup_properties.py

Environment:
    GHL_API_TOKEN, GHL_LOCATION_ID
"""

import os
import sys
import json
import time

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

GHL_API_TOKEN = os.getenv("GHL_API_TOKEN", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"


def ghl_request(method, endpoint, data=None, params=None):
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
        else:
            return {"error": f"Unknown method {method}"}

        if resp.status_code == 429:
            print("    ⏳ Rate limited, waiting 10s...")
            time.sleep(10)
            return ghl_request(method, endpoint, data, params)

        if resp.status_code >= 400:
            return {"error": resp.text[:200], "status": resp.status_code}

        return resp.json() if resp.text else {"success": True}
    except Exception as e:
        return {"error": str(e)}


def get_existing_fields():
    """Get all existing custom fields."""
    result = ghl_request("GET", "/locations/{}/customFields".format(GHL_LOCATION_ID))
    fields = result.get("customFields", [])
    return {f["name"]: f for f in fields}


def create_field(name, field_type, options=None, model="contact", position=0):
    """Create a single custom field."""
    payload = {
        "name": name,
        "dataType": field_type,
        "model": model,
        "position": position,
    }

    # Map our types to GHL types
    type_map = {
        "text": "TEXT",
        "number": "NUMERICAL",
        "dropdown": "SINGLE_OPTIONS",
        "multi-select": "MULTIPLE_OPTIONS",
        "checkbox": "CHECKBOX",
        "date": "DATE",
        "textarea": "LARGE_TEXT",
    }

    ghl_type = type_map.get(field_type, "TEXT")
    payload["dataType"] = ghl_type

    if options and ghl_type in ("SINGLE_OPTIONS", "MULTIPLE_OPTIONS"):
        payload["options"] = options

    return ghl_request("POST", f"/locations/{GHL_LOCATION_ID}/customFields", data=payload)


def main():
    if not GHL_API_TOKEN or not GHL_LOCATION_ID:
        print("❌ Set GHL_API_TOKEN and GHL_LOCATION_ID first.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  🔧 NEXUS BDR — GHL Custom Properties Setup")
    print(f"  Location: {GHL_LOCATION_ID}")
    print(f"{'='*60}\n")

    # Get existing fields to avoid duplicates
    print("  📋 Checking existing custom fields...")
    existing = get_existing_fields()
    print(f"     Found {len(existing)} existing fields\n")

    # Define all custom fields
    fields = [
        # ─── Identity & Company ───
        ("Nexus Brand", "dropdown", ["TBF", "DFT", "Both"]),
        ("Company Domain", "text", None),
        ("Decision Maker Level", "dropdown", ["C-Suite", "VP", "Director", "Manager", "Individual"]),
        ("Lead Source", "dropdown", ["Claude Research", "Instagram", "Trade Show", "Referral", "Inbound", "Apollo", "CSV Import", "Website", "LinkedIn", "State License DB", "Google Maps"]),
        ("Lead Source Detail", "text", None),

        # ─── Company Intelligence ───
        ("Company Size", "dropdown", ["1-10", "11-50", "51-200", "201-500", "500+"]),
        ("Company Revenue Est", "number", None),
        ("Company Founded", "text", None),
        ("Company Type", "dropdown", ["Licensed Operator", "MSO", "Processor", "Manufacturer", "Brand", "Distributor", "Retailer", "Lab", "Consultant", "Hemp Farm", "CPG Company"]),
        ("License Type", "multi-select", ["Type 6 Mfg", "Type 7 Mfg Volatile", "Processing", "Cultivation", "Distribution", "Retail", "Testing", "Microbusiness"]),
        ("License State", "multi-select", ["CA", "CO", "OR", "WA", "MI", "OK", "AZ", "NV", "ME", "MT", "IL", "MA", "NJ", "NY", "MO", "MD", "OH", "VA", "NM", "CT", "VT", "RI", "DE", "MN"]),
        ("License Number", "text", None),
        ("Markets Served", "multi-select", ["Adult-Use", "Medical", "Hemp/CBD", "CPG", "Cosmetics", "Pharma", "Food & Bev", "Pet", "Aromatherapy", "Wellness"]),
        ("Multi State Operator", "checkbox", None),
        ("State Count", "number", None),

        # ─── Product & Technical ───
        ("Extraction Methods", "multi-select", ["BHO", "CO2", "Ethanol", "Rosin/Solventless", "Distillation", "Ice Water Hash", "PHO", "Steam Distillation", "Cold Press"]),
        ("Product Types", "multi-select", ["Live Resin", "Distillate", "Shatter", "Wax", "Vape Carts", "Edibles", "Topicals", "Tinctures", "RSO", "Diamonds", "Sauce", "Rosin", "Flower", "Pre-Rolls", "Beverages"]),
        ("Terpene Usage", "dropdown", ["Currently Uses Botanical", "Currently Uses Synthetic", "Uses Cannabis-Derived Only", "No Terpene Reintroduction", "Unknown"]),
        ("Current Terpene Supplier", "text", None),
        ("Annual Terpene Volume", "dropdown", ["<1kg", "1-5kg", "5-25kg", "25-100kg", "100kg+"]),
        ("Equipment Brands", "text", None),
        ("Production Capacity", "text", None),

        # ─── Scoring & Qualification ───
        ("Nexus Lead Score", "number", None),
        ("ICP Tier", "dropdown", ["Tier 1 Perfect", "Tier 2 Strong", "Tier 3 Moderate", "Tier 4 Low"]),
        ("Prospect Temperature", "dropdown", ["Hot", "Warm", "Cool", "Cold"]),
        ("Buying Signals", "multi-select", ["Expanding Production", "New Facility", "Hiring Extractors", "Launched New Product", "Raised Funding", "Scaling Multi-State", "Posted About Terpenes", "Requested Sample", "Trade Show Upcoming"]),
        ("Objection Risk", "multi-select", ["Price Sensitive", "Happy With Current Supplier", "Prefers CDT Only", "No Budget Authority", "Regulatory Concerns", "Too Small", "Not Ready"]),
        ("Estimated Deal Value", "number", None),
        ("Sales Ready", "checkbox", None),

        # ─── Social & Digital ───
        ("Instagram Handle", "text", None),
        ("Instagram Followers", "number", None),
        ("Instagram Engagement", "dropdown", ["High", "Medium", "Low"]),
        ("LinkedIn URL", "text", None),
        ("Website Traffic Est", "dropdown", ["<1K", "1K-10K", "10K-100K", "100K+"]),
        ("Social Activity Level", "dropdown", ["Very Active", "Active", "Occasional", "Dormant"]),
        ("Content Themes", "text", None),

        # ─── Engagement Tracking ───
        ("First Outreach Date", "date", None),
        ("Outreach Channel", "dropdown", ["Email", "SMS", "LinkedIn DM", "Instagram DM", "Phone", "In-Person", "WhatsApp"]),
        ("Outreach Sequence", "text", None),
        ("Sequence Step", "number", None),
        ("Last Touch Date", "date", None),
        ("Total Touches", "number", None),
        ("Response Status", "dropdown", ["No Response", "Positive Reply", "Negative Reply", "Meeting Booked", "Sample Requested", "Bounced", "Unsubscribed", "Wrong Person", "Auto-Reply"]),
        ("Sample Sent", "checkbox", None),
        ("Sample Date", "date", None),
        ("Sample Products", "text", None),
        ("Meeting Date", "date", None),
        ("Meeting Notes", "textarea", None),

        # ─── Personalization ───
        ("Personalization Hook", "textarea", None),
        ("Recent News", "textarea", None),
        ("Mutual Connections", "text", None),
        ("Trade Shows", "text", None),
        ("Pain Points", "textarea", None),

        # ─── BDR Metadata ───
        ("Enrichment Date", "date", None),
        ("Enrichment Source", "text", None),
        ("Data Confidence", "dropdown", ["Verified", "High", "Medium", "Low"]),
        ("Needs Enrichment", "checkbox", None),
        ("Do Not Contact", "checkbox", None),
    ]

    created = 0
    skipped = 0
    errors = 0

    for i, (name, ftype, options) in enumerate(fields):
        if name in existing:
            print(f"  ⏭️  {name} — already exists")
            skipped += 1
            continue

        print(f"  📝 Creating: {name} ({ftype})...", end=" ")
        result = create_field(name, ftype, options, position=i)

        if "error" in result:
            print(f"❌ {result['error'][:80]}")
            errors += 1
        else:
            print("✅")
            created += 1

        time.sleep(0.15)  # Rate limit

    print(f"\n{'='*60}")
    print(f"  ✅ Created: {created}")
    print(f"  ⏭️  Skipped (existing): {skipped}")
    print(f"  ❌ Errors: {errors}")
    print(f"  📊 Total custom fields: {created + skipped + len(existing)}")
    print(f"{'='*60}\n")

    # Save field mapping for use by other scripts
    print("  📋 Fetching updated field list for mapping...")
    updated_fields = get_existing_fields()
    field_map = {}
    for name, field in updated_fields.items():
        field_map[name] = {
            "id": field.get("id"),
            "key": field.get("fieldKey", field.get("key", "")),
            "dataType": field.get("dataType"),
        }

    from pathlib import Path
    map_path = Path(__file__).parent.parent / "config" / "ghl-field-map.json"
    map_path.parent.mkdir(exist_ok=True)
    with open(map_path, "w") as f:
        json.dump(field_map, f, indent=2)
    print(f"  💾 Field mapping saved to: {map_path}")


if __name__ == "__main__":
    main()
