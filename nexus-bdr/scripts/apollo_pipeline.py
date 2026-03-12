#!/usr/bin/env python3
"""
Apollo Pipeline Commander — Nexus BDR Agent
=============================================
Takes the 138 Apollo contacts, scores them locally using Apollo data,
verifies emails with Hunter, and imports everything to GHL with
custom fields, tags, and pipeline stages. NO Claude API needed.

Also generates a GHL Workflow Blueprint — step-by-step instructions
for building the automation workflows in GHL UI.

PIPELINE:
  1. Load imported Apollo JSON
  2. Enhanced local scoring (uses title, seniority, employees, industry, state, keywords)
  3. Smart brand assignment (TBF/DFT based on company profile)
  4. Hunter email verification (optional, uses free tier)
  5. GHL import with all 53 custom fields + tags + opportunities
  6. Generate GHL workflow blueprint document

Usage:
    python3 apollo_pipeline.py --input "outputs/imported_apollo-contacts-export_20260304_0025.json"
    python3 apollo_pipeline.py --input "outputs/imported_*.json" --verify-emails
    python3 apollo_pipeline.py --input "outputs/imported_*.json" --verify-emails --import-ghl
    python3 apollo_pipeline.py --blueprint-only (generate workflow blueprint without importing)

Environment:
    GHL_API_TOKEN, GHL_LOCATION_ID
    HUNTER_API_KEY (optional, for email verification)
"""

import os, sys, json, re, time, argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests"); sys.exit(1)

GHL_API_TOKEN = os.getenv("GHL_API_TOKEN", "")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID", "")
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
CONFIG_DIR = SKILL_DIR / "config"
REFS_DIR = SKILL_DIR / "references"

for d in [OUTPUT_DIR, CONFIG_DIR]:
    d.mkdir(exist_ok=True)

# ─── CANNABIS INDUSTRY KEYWORDS ────────────────────────────
# Used for smart scoring — if Apollo keywords contain these, we
# know the company is terpene-relevant

EXTRACTION_KEYWORDS = [
    "extraction", "distillation", "bho", "co2", "ethanol", "rosin",
    "concentrate", "hash", "solventless", "hydrocarbon", "short path",
    "wiped film", "fractional distillation", "winterization",
]

PRODUCT_KEYWORDS = [
    "vape", "cartridge", "cart", "disposable", "edible", "gummy",
    "tincture", "topical", "pre-roll", "flower", "concentrate",
    "live resin", "distillate", "wax", "shatter", "budder", "sauce",
    "diamond", "rosin", "badder", "crumble", "rso", "capsule",
    "beverage", "infused", "chocolates", "mints",
]

TERPENE_KEYWORDS = [
    "terpene", "terp", "flavor", "botanical", "cdt",
    "cannabis derived", "strain profile", "formulation",
]

CANNABIS_INDUSTRY_KEYWORDS = [
    "cannabis", "marijuana", "hemp", "cbd", "thc", "dispensary",
    "cultivation", "grow", "processor", "manufacturer", "licensed",
]

TIER1_STATES = {"CA", "CO", "OR", "WA", "MI", "OK", "AZ", "NV", "IL", "MA", "NJ", "MO", "MD", "OH", "FL", "NY", "PA", "CT", "VA", "NM"}
TIER2_STATES = {"ME", "VT", "MT", "RI", "DE", "NH", "MN", "WI", "HI", "AK", "SD", "ND"}


# ─── GHL API ──────────────────────────────────────────────

def ghl_request(method, endpoint, data=None, params=None):
    url = f"{GHL_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {GHL_API_TOKEN}",
        "Version": GHL_API_VERSION,
        "Content-Type": "application/json",
    }
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=15)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=15)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=15)
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


def load_field_map():
    path = CONFIG_DIR / "ghl-field-map.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


# ─── HUNTER API ────────────────────────────────────────────

def hunter_verify_email(email):
    """Verify a single email with Hunter. Returns status."""
    if not HUNTER_API_KEY or not email:
        return None
    try:
        resp = requests.get("https://api.hunter.io/v2/email-verifier", params={
            "email": email,
            "api_key": HUNTER_API_KEY,
        }, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {
                "status": data.get("status", "unknown"),  # valid, invalid, accept_all, webmail, disposable, unknown
                "score": data.get("score", 0),
                "disposable": data.get("disposable", False),
                "webmail": data.get("webmail", False),
                "mx_records": data.get("mx_records", False),
            }
        elif resp.status_code == 429:
            print("      ⏳ Hunter rate limit...")
            time.sleep(2)
            return hunter_verify_email(email)
        elif resp.status_code == 402:
            print("      ⚠️ Hunter credits exhausted")
            return None
        return None
    except Exception as e:
        print(f"      ⚠️ Hunter error: {e}")
        return None


def hunter_find_email(domain, first_name, last_name):
    """Find email using Hunter Email Finder."""
    if not HUNTER_API_KEY or not domain:
        return None
    try:
        resp = requests.get("https://api.hunter.io/v2/email-finder", params={
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": HUNTER_API_KEY,
        }, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {
                "email": data.get("email", ""),
                "confidence": data.get("confidence", 0),
                "type": data.get("type", ""),
                "sources": len(data.get("sources", [])),
            }
        elif resp.status_code == 402:
            print("      ⚠️ Hunter credits exhausted")
        return None
    except:
        return None


def hunter_domain_search(domain):
    """Search Hunter for all emails at a domain."""
    if not HUNTER_API_KEY or not domain:
        return None
    try:
        resp = requests.get("https://api.hunter.io/v2/domain-search", params={
            "domain": domain,
            "api_key": HUNTER_API_KEY,
        }, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {
                "pattern": data.get("pattern", ""),
                "total_emails": data.get("total", 0),
                "emails": [
                    {
                        "email": e.get("value", ""),
                        "type": e.get("type", ""),
                        "confidence": e.get("confidence", 0),
                        "first_name": e.get("first_name", ""),
                        "last_name": e.get("last_name", ""),
                        "position": e.get("position", ""),
                    }
                    for e in data.get("emails", [])[:10]
                ],
            }
        return None
    except:
        return None


# ─── ENHANCED LOCAL SCORING ────────────────────────────────

def score_lead(lead):
    """Score a lead 0-100 using all available Apollo data. No API needed."""
    score = 0
    reasons = []

    # ── TITLE / SENIORITY (+0-25) ──
    title = (lead.get("title") or lead.get("contact_title") or "").lower()
    seniority = (lead.get("seniority") or "").lower()
    dm_level = lead.get("decision_maker_level", "")

    c_suite = ["ceo", "cto", "coo", "founder", "owner", "president", "co-founder", "chief", "partner"]
    vp_level = ["vp", "vice president", "svp", "evp"]
    director = ["director", "head of"]
    manager = ["manager", "lead", "supervisor", "coordinator"]

    if any(t in title for t in c_suite) or seniority in ("c_suite", "owner", "founder"):
        score += 25; dm_level = "C-Suite"; reasons.append("C-Suite +25")
    elif any(t in title for t in vp_level) or seniority == "vp":
        score += 20; dm_level = "VP"; reasons.append("VP +20")
    elif any(t in title for t in director) or seniority == "director":
        score += 18; dm_level = "Director"; reasons.append("Director +18")
    elif any(t in title for t in manager) or seniority == "manager":
        score += 15; dm_level = "Manager"; reasons.append("Manager +15")
    else:
        score += 5; dm_level = dm_level or "Individual"; reasons.append("Individual +5")
    lead["decision_maker_level"] = dm_level

    # ── TITLE RELEVANCE BONUS (+0-10) ──
    # Titles directly related to terpene purchasing get a bonus
    terp_titles = ["extraction", "formulation", "production", "manufacturing", "operations",
                   "procurement", "purchasing", "supply chain", "lab", "r&d", "quality",
                   "product development", "processing"]
    if any(t in title for t in terp_titles):
        score += 10; reasons.append("Terpene-relevant title +10")

    # ── COMPANY SIZE (+0-20) ──
    employees = lead.get("employees", "")
    size = lead.get("company_size", "")
    if not size and employees:
        try:
            emp_num = int(str(employees).replace(",", "").strip())
            if emp_num <= 10: size = "1-10"
            elif emp_num <= 50: size = "11-50"
            elif emp_num <= 200: size = "51-200"
            elif emp_num <= 500: size = "201-500"
            else: size = "500+"
            lead["company_size"] = size
        except (ValueError, TypeError):
            pass

    size_scores = {"11-50": 20, "51-200": 18, "1-10": 15, "201-500": 12, "500+": 10}
    s = size_scores.get(size, 5)
    score += s
    if size: reasons.append(f"Size {size} +{s}")

    # ── STATE (+0-15) ──
    state = (lead.get("state") or "")[:2].upper()
    if state in TIER1_STATES:
        score += 15; reasons.append(f"Tier 1 state {state} +15")
    elif state in TIER2_STATES:
        score += 10; reasons.append(f"Tier 2 state {state} +10")
    elif state:
        score += 5; reasons.append(f"Other state {state} +5")

    # ── INDUSTRY RELEVANCE (+0-15) ──
    industry = (lead.get("industry") or "").lower()
    keywords_raw = (lead.get("keywords") or "").lower()
    combined_text = f"{industry} {keywords_raw} {title}"

    # Cannabis/hemp industry
    cannabis_match = sum(1 for kw in CANNABIS_INDUSTRY_KEYWORDS if kw in combined_text)
    if cannabis_match >= 2:
        score += 15; reasons.append(f"Strong cannabis industry match +15")
    elif cannabis_match == 1:
        score += 10; reasons.append(f"Cannabis industry signal +10")

    # Extraction/production keywords
    extraction_match = sum(1 for kw in EXTRACTION_KEYWORDS if kw in combined_text)
    if extraction_match >= 1:
        score += 10; reasons.append(f"Extraction keywords +10")
        lead["extraction_methods"] = [kw for kw in EXTRACTION_KEYWORDS if kw in combined_text]

    # Product keywords
    product_match = sum(1 for kw in PRODUCT_KEYWORDS if kw in combined_text)
    if product_match >= 2:
        score += 8; reasons.append(f"Multiple product keywords +8")
        lead["product_types"] = [kw for kw in PRODUCT_KEYWORDS if kw in combined_text]
    elif product_match == 1:
        score += 4; reasons.append(f"Product keyword +4")

    # Direct terpene mention
    terpene_match = sum(1 for kw in TERPENE_KEYWORDS if kw in combined_text)
    if terpene_match >= 1:
        score += 15; reasons.append(f"Terpene keyword match +15")

    # ── EMAIL QUALITY (+0-5) ──
    email = lead.get("email", "")
    email_status = (lead.get("email_status") or "").lower()
    if email and email_status == "valid":
        score += 5; reasons.append("Verified email +5")
    elif email:
        score += 2; reasons.append("Has email +2")

    # ── ENGAGEMENT HISTORY FROM APOLLO (+0-5) ──
    replied = lead.get("replied", "")
    email_open = lead.get("email_open", "")
    if replied and str(replied) not in ("0", "", "False"):
        score += 5; reasons.append("Previous reply +5")
    elif email_open and str(email_open) not in ("0", "", "False"):
        score += 3; reasons.append("Previous open +3")

    # ── REVENUE SIGNAL (+0-5) ──
    revenue = (lead.get("revenue") or "").replace("$", "").replace(",", "").strip()
    if revenue:
        try:
            rev_num = float(revenue)
            if rev_num >= 1000000:
                score += 5; reasons.append(f"Revenue ${rev_num:,.0f} +5")
            elif rev_num >= 100000:
                score += 3; reasons.append(f"Revenue ${rev_num:,.0f} +3")
        except:
            pass

    # ── FUNDING SIGNAL (+0-5) ──
    funding = lead.get("total_funding", "")
    if funding and funding not in ("", "0", "$0"):
        score += 5; reasons.append(f"Has funding +5")

    # ── LINKEDIN PRESENCE (+0-3) ──
    linkedin = lead.get("linkedin", lead.get("linkedin_url", ""))
    if linkedin:
        score += 3; reasons.append("Has LinkedIn +3")
        lead["linkedin_url"] = linkedin

    # ── CAP & CLASSIFY ──
    score = max(0, min(100, score))
    lead["nexus_lead_score"] = score
    lead["score_reasons"] = reasons

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
    """Assign TBF or DFT based on company signals."""
    size = lead.get("company_size", "")
    employees = lead.get("employees", "")
    industry = (lead.get("industry") or "").lower()
    keywords = (lead.get("keywords") or "").lower()
    revenue = lead.get("revenue", "")
    title = (lead.get("title") or "").lower()

    # TBF indicators: bigger companies, CPG, pharma, MSOs
    tbf_signals = 0
    if size in ("201-500", "500+"):
        tbf_signals += 2
    elif size == "51-200":
        tbf_signals += 1
    if any(kw in industry for kw in ["pharmaceutical", "cpg", "cosmetic", "food", "beverage"]):
        tbf_signals += 2
    if any(kw in keywords for kw in ["multi-state", "mso", "enterprise", "corporate", "national"]):
        tbf_signals += 2
    if revenue:
        try:
            rev = float(str(revenue).replace("$", "").replace(",", ""))
            if rev >= 10000000:
                tbf_signals += 2
            elif rev >= 1000000:
                tbf_signals += 1
        except:
            pass

    # DFT indicators: smaller, craft, hemp, solo operators
    dft_signals = 0
    if size in ("1-10", "11-50"):
        dft_signals += 1
    if any(kw in industry for kw in ["hemp", "cbd", "alternative medicine"]):
        dft_signals += 2
    if any(kw in keywords for kw in ["craft", "small batch", "artisan", "boutique", "independent", "hemp", "cbd"]):
        dft_signals += 2
    if any(kw in title for kw in ["founder", "owner", "solo"]):
        dft_signals += 1

    if tbf_signals > dft_signals:
        lead["nexus_brand"] = "TBF"
    else:
        lead["nexus_brand"] = "DFT"

    lead["brand_reason"] = f"TBF signals: {tbf_signals}, DFT signals: {dft_signals}"
    return lead


# ─── GHL IMPORT ────────────────────────────────────────────

def build_custom_fields(lead, field_map):
    """Map all lead data to GHL custom fields."""
    mappings = {
        "Nexus Brand": lead.get("nexus_brand"),
        "Company Domain": lead.get("domain"),
        "Decision Maker Level": lead.get("decision_maker_level"),
        "Lead Source": lead.get("source", "Apollo Export"),
        "Lead Source Detail": lead.get("apollo_lists", lead.get("lead_source_detail")),
        "Company Size": lead.get("company_size"),
        "Company Type": lead.get("company_type"),
        "Nexus Lead Score": lead.get("nexus_lead_score"),
        "ICP Tier": lead.get("icp_tier"),
        "Prospect Temperature": lead.get("prospect_temperature"),
        "LinkedIn URL": lead.get("linkedin_url"),
        "Extraction Methods": lead.get("extraction_methods"),
        "Product Types": lead.get("product_types"),
        "Company Revenue Est": lead.get("revenue"),
        "Data Confidence": lead.get("email_verification", {}).get("status", "unverified") if isinstance(lead.get("email_verification"), dict) else "unverified",
        "Enrichment Source": "Apollo + Hunter" if lead.get("email_verification") else "Apollo",
        "Enrichment Date": datetime.utcnow().strftime("%Y-%m-%d"),
    }

    # Apollo engagement data → enrichment fields
    if lead.get("keywords"):
        mappings["Content Themes"] = lead["keywords"][:500] if isinstance(lead["keywords"], str) else ", ".join(lead["keywords"])[:500]

    if lead.get("technologies"):
        mappings["Equipment Brands"] = lead["technologies"][:500] if isinstance(lead["technologies"], str) else ", ".join(lead["technologies"])[:500]

    customs = []
    for field_name, value in mappings.items():
        if value is None or value == "" or value == []:
            continue
        field_info = field_map.get(field_name)
        if field_info and field_info.get("key"):
            if isinstance(value, list):
                value = value
            customs.append({"key": field_info["key"], "field_value": value})

    return customs


def import_to_ghl(lead, pipeline_id=None, stage_id=None, field_map=None):
    """Import a single lead to GHL with all enrichment data."""
    contact_name = lead.get("contact_name", "")
    parts = contact_name.split() if contact_name else []
    first_name = parts[0] if parts else "Unknown"
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    email = lead.get("email", "")
    phone = lead.get("phone", lead.get("work_phone", lead.get("mobile_phone", "")))
    company = lead.get("company_name", "")

    payload = {
        "firstName": first_name,
        "lastName": last_name,
        "locationId": GHL_LOCATION_ID,
        "companyName": company,
        "source": "nexus-bdr-agent",
    }

    if email: payload["email"] = email
    if phone: payload["phone"] = phone
    if lead.get("city"): payload["city"] = lead["city"]
    if lead.get("state"): payload["state"] = lead["state"]
    if lead.get("country"): payload["country"] = lead["country"]

    domain = lead.get("domain", "")
    if domain:
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        payload["website"] = domain

    # Tags
    tags = ["nexus-bdr-agent", "source:apollo-export"]
    brand = lead.get("nexus_brand", "")
    if brand: tags.append(f"brand:{brand.lower()}")
    tier = lead.get("icp_tier", "")
    if tier: tags.append(f"quality:{tier.lower().replace(' ', '-')}")
    temp = lead.get("prospect_temperature", "")
    if temp: tags.append(f"temp:{temp.lower()}")
    dm = lead.get("decision_maker_level", "")
    if dm: tags.append(f"role:{dm.lower().replace(' ', '-')}")
    state = lead.get("state", "")[:2].upper()
    if state: tags.append(f"state:{state.lower()}")

    # Email quality tags
    ev = lead.get("email_verification", {})
    if isinstance(ev, dict):
        status = ev.get("status", "")
        if status == "valid": tags.append("email:verified")
        elif status == "invalid": tags.append("email:invalid")
        elif status == "accept_all": tags.append("email:catch-all")

    # Industry tags from keywords
    keywords = (lead.get("keywords") or "").lower()
    if "cannabis" in keywords or "marijuana" in keywords: tags.append("vertical:cannabis")
    if "hemp" in keywords or "cbd" in keywords: tags.append("vertical:hemp")
    if "extract" in keywords: tags.append("vertical:extraction")
    if "vape" in keywords or "cartridge" in keywords: tags.append("vertical:vape")

    payload["tags"] = tags

    # Custom fields
    custom_fields = build_custom_fields(lead, field_map or {})
    if custom_fields:
        payload["customFields"] = custom_fields

    # Create/upsert contact
    if email or phone:
        result = ghl_request("POST", "/contacts/upsert", data=payload)
    else:
        result = ghl_request("POST", "/contacts/", data=payload)

    contact = result.get("contact", {})
    contact_id = contact.get("id")

    # Create opportunity
    if contact_id and pipeline_id and stage_id:
        score = lead.get("nexus_lead_score", 0)
        # Hot leads start further in pipeline
        actual_stage = stage_id
        opp_name = f"{company} — {brand}" if brand else company

        ghl_request("POST", "/opportunities/", data={
            "pipelineId": pipeline_id,
            "pipelineStageId": actual_stage,
            "locationId": GHL_LOCATION_ID,
            "contactId": contact_id,
            "name": opp_name,
            "status": "open",
            "source": "nexus-bdr-agent",
            "monetaryValue": lead.get("estimated_deal_value", 0),
        })

    return contact_id


# ─── GHL WORKFLOW BLUEPRINT ───────────────────────────────

def generate_workflow_blueprint():
    """Generate step-by-step GHL workflow setup instructions."""
    blueprint = """# 🔧 GHL Workflow Blueprint — Nexus BDR Automation
*Build these workflows in GHL UI. Each one triggers automatically.*
*Generated: """ + datetime.utcnow().strftime("%B %d, %Y") + """*

---

## Overview

Your CRM has 53 custom fields, a scoring system, and brand assignment.
These workflows make it all AUTOMATIC — when a contact enters or changes,
the right things happen without manual intervention.

Build these in order. Each takes 5-10 minutes in GHL Workflow Builder.

---

## Workflow 1: 🏷️ Auto-Tag by Score Tier

**Trigger:** Contact Tag Added contains "nexus-bdr-agent"
**Purpose:** Ensure every imported contact gets properly categorized

**Actions:**
1. IF custom field "Nexus Lead Score" >= 80:
   - Add tag: "priority:hot"
   - Add tag: "action:outreach-now"
   - Send Internal Notification → "🔥 HOT LEAD: {{contact.name}} at {{contact.company}} — Score: {{custom.nexus_lead_score}}"

2. ELSE IF "Nexus Lead Score" >= 60:
   - Add tag: "priority:warm"
   - Add tag: "action:outreach-this-week"

3. ELSE IF "Nexus Lead Score" >= 40:
   - Add tag: "priority:cool"
   - Add tag: "action:nurture"

4. ELSE:
   - Add tag: "priority:cold"
   - Add tag: "action:research-needed"

---

## Workflow 2: 📧 New Lead Welcome Sequence — TBF

**Trigger:** Contact Tag Added = "brand:tbf" AND "priority:hot" OR "priority:warm"
**Purpose:** Auto-enroll hot/warm TBF leads in outreach sequence

**Actions:**
1. Wait 1 hour (avoid looking automated)
2. Send Email: TBF Introduction
   - Subject: "Quick question about {{contact.company}}'s terpene sourcing"
   - Template: Professional, science-forward, reference their specific products
   - FROM: Your TBF sales email

3. Wait 3 days
4. IF Email Opened:
   - Send Email: TBF Value Prop
   - Subject: "Batch consistency data from TBF"
   - Attach: TBF COA sample or consistency report

5. Wait 4 days
6. IF No Reply:
   - Send Email: TBF Sample Offer
   - Subject: "Complimentary sample kit for {{contact.company}}"

7. Wait 7 days
8. IF No Reply:
   - Add tag: "status:sequence-complete-no-reply"
   - Move opportunity to "Outreach Sent" stage

9. IF Reply at any point:
   - Remove from sequence
   - Add tag: "status:replied"
   - Move opportunity to "Engaged"
   - Send Internal Notification → "🎉 REPLY from {{contact.name}} at {{contact.company}}"

---

## Workflow 3: 📧 New Lead Welcome Sequence — DFT

**Trigger:** Contact Tag Added = "brand:dft" AND "priority:hot" OR "priority:warm"
**Purpose:** Auto-enroll hot/warm DFT leads in outreach sequence

**Actions:**
Same structure as Workflow 2 but:
- DFT brand voice (edgy, direct, anti-corporate)
- Subject lines: more casual, reference hype strains
- FROM: Your DFT sales email
- Email 1: "Your [product they make] deserves better terps"
- Email 2: "Why craft extractors are ditching [competitor]"
- Email 3: "Free Runtz + Biscotti sample kit"

---

## Workflow 4: 🔄 Engagement Escalation

**Trigger:** Contact Email Opened >= 3 times OR Contact Email Link Clicked
**Purpose:** Escalate engaged prospects for immediate follow-up

**Actions:**
1. Update custom field "Prospect Temperature" → "Warm" (or "Hot" if already Warm)
2. Add tag: "signal:engaged"
3. Move opportunity → "Engaged" stage
4. Send Internal Notification → "👀 {{contact.name}} is engaging — opened {{email.opens}} times"
5. IF Click:
   - Add tag: "signal:clicked"
   - Send Internal Notification → "🖱️ {{contact.name}} clicked — follow up NOW"

---

## Workflow 5: 📞 Reply Handler

**Trigger:** Contact Replied to Email
**Purpose:** Immediately alert on replies and update CRM

**Actions:**
1. Remove all sequence tags
2. Add tag: "status:replied"
3. Update "Response Status" → "Replied"
4. Update "Last Touch Date" → {{current_date}}
5. Increment "Total Touches"
6. Move opportunity → "Engaged"
7. Send Internal Notification (URGENT) → "📨 REPLY from {{contact.name}}: Preview of reply text"

---

## Workflow 6: ⏰ Re-engagement (Stale Leads)

**Trigger:** Contact custom field "Last Touch Date" is more than 30 days ago
         AND "Response Status" != "Replied"
         AND "Total Touches" < 5
**Purpose:** Re-engage cold leads with fresh angle

**Actions:**
1. Wait until 9:00 AM contact's timezone
2. Send Email: Re-engagement
   - New angle — don't repeat original sequence
   - Reference something new (industry news, new product, trade show)
3. Add tag: "status:re-engaged"
4. Update "Total Touches" + 1

---

## Workflow 7: 📦 Sample Follow-Up

**Trigger:** Custom field "Sample Sent" = true
**Purpose:** Follow up after samples are delivered

**Actions:**
1. Wait 5 days
2. Send Email: "How'd the samples turn out?"
3. Wait 3 days
4. IF No Reply:
   - Send Email: "Quick check — did the {{custom.sample_products}} samples arrive?"
5. Wait 5 days
6. IF No Reply:
   - Add tag: "status:sample-no-response"
   - Send Internal Notification → "Sample sent to {{contact.company}} — no response after 13 days"

---

## Workflow 8: 🎪 Trade Show Pre-Event

**Trigger:** Custom field "Trade Shows" is not empty
         AND event date is within 14 days (manual tag trigger)
**Purpose:** Warm outreach before industry events

**Actions:**
1. Add tag: "event:pre-outreach"
2. Send Email: "See you at [Event]?"
   - Reference their trade show attendance
   - Suggest meeting at the event
3. Wait 3 days
4. IF Reply → Internal notification + move to "Meeting Booked"

---

## Workflow 9: 📊 Weekly Pipeline Report

**Trigger:** Every Monday at 8:00 AM
**Purpose:** Weekly summary of pipeline health

**Actions:**
1. Send Internal Notification with pipeline stats:
   - New leads this week
   - Leads in each stage
   - Replies received
   - Meetings booked
   - Top 5 hottest prospects

---

## Workflow 10: 🚨 High-Value Lead Alert

**Trigger:** Contact Created with custom field "Nexus Lead Score" >= 80
**Purpose:** Immediate alert for hot leads

**Actions:**
1. Send Internal Notification (SMS + Email):
   "🔥 HIGH-VALUE LEAD ALERT
   {{contact.name}} — {{contact.title}} at {{contact.company}}
   Score: {{custom.nexus_lead_score}} | Brand: {{custom.nexus_brand}}
   {{contact.email}} | {{contact.phone}}
   State: {{contact.state}} | Industry: {{custom.content_themes}}"

2. Add tag: "priority:immediate-outreach"
3. Create Task: "Call {{contact.name}} at {{contact.company}} within 24 hours"

---

## Tag Taxonomy Reference

### Source Tags (auto-applied on import)
- source:apollo-export
- source:claude-research
- source:instagram
- source:trade-show
- source:csv-import
- source:license-db
- source:reddit
- source:social-intel

### Brand Tags
- brand:tbf
- brand:dft

### Priority Tags
- priority:hot (score 80+)
- priority:warm (score 60-79)
- priority:cool (score 40-59)
- priority:cold (score 0-39)

### Status Tags
- status:new
- status:researched
- status:outreach-sent
- status:replied
- status:engaged
- status:sequence-complete-no-reply
- status:re-engaged
- status:sample-no-response

### Signal Tags
- signal:engaged (3+ opens)
- signal:clicked
- signal:expanding
- signal:hiring
- signal:new-product

### Role Tags
- role:c-suite
- role:vp
- role:director
- role:manager
- role:individual

### Email Quality Tags
- email:verified
- email:invalid
- email:catch-all

### Vertical Tags
- vertical:cannabis
- vertical:hemp
- vertical:extraction
- vertical:vape

---

## Email Template Checklist

Create these email templates in GHL before activating workflows:

### TBF Templates
1. **TBF Intro** — Science-forward, professional, references their products
2. **TBF Value Prop** — Batch consistency data, COA example
3. **TBF Sample Offer** — Complimentary sample kit, specific strains
4. **TBF Re-engagement** — Fresh angle, industry news hook

### DFT Templates
1. **DFT Intro** — Edgy, direct, references their craft approach
2. **DFT Value Prop** — Hype strain accuracy, small-batch focus
3. **DFT Sample Offer** — Free sample kit, exotic strains
4. **DFT Re-engagement** — Fresh angle, underground market insight

### Shared Templates
1. **Sample Follow-Up** — "How'd the samples turn out?"
2. **Trade Show Pre-Event** — "See you at [Event]?"
3. **Meeting Confirmation** — Calendar link + prep notes
4. **Proposal Follow-Up** — After sending pricing/proposal

---

*Build workflows in this order. Test each with a single contact before activating for all.*
"""
    return blueprint


# ─── MAIN PIPELINE ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Apollo Pipeline Commander — Nexus BDR")
    parser.add_argument("--input", help="Imported Apollo JSON file")
    parser.add_argument("--verify-emails", action="store_true", help="Verify emails with Hunter API")
    parser.add_argument("--find-missing-emails", action="store_true", help="Find missing emails with Hunter")
    parser.add_argument("--import-ghl", action="store_true", help="Import to GHL")
    parser.add_argument("--pipeline-id", default="YA64eItHkj1Fe6RxYRIp")
    parser.add_argument("--stage-id", default="5c18feb6-82f2-479f-8e56-409e1075c905")
    parser.add_argument("--blueprint-only", action="store_true", help="Just generate workflow blueprint")
    parser.add_argument("--max", type=int, default=200)

    args = parser.parse_args()

    print(f"\n  {'━'*60}")
    print(f"  🚀 APOLLO PIPELINE COMMANDER")
    print(f"  {'━'*60}\n")

    # Blueprint
    if args.blueprint_only or not args.input:
        print("  📋 Generating GHL Workflow Blueprint...\n")
        blueprint = generate_workflow_blueprint()
        bp_path = REFS_DIR / "ghl-workflow-blueprint.md"
        REFS_DIR.mkdir(exist_ok=True)
        bp_path.write_text(blueprint)
        print(f"  💾 Blueprint saved: {bp_path}")
        if not args.input:
            print(f"\n  {'━'*60}\n")
            return

    # Load
    print(f"  📂 Loading: {args.input}")
    with open(args.input) as f:
        data = json.load(f)
    leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else [data]))
    leads = leads[:args.max]
    print(f"     Loaded {len(leads)} leads\n")

    if not leads:
        print("  ❌ No leads found."); sys.exit(1)

    # Score
    print("  📊 Scoring with enhanced local engine...")
    for lead in leads:
        score_lead(lead)
        assign_brand(lead)

    scores = [l.get("nexus_lead_score", 0) for l in leads]
    hot = sum(1 for s in scores if s >= 80)
    warm = sum(1 for s in scores if 60 <= s < 80)
    cool = sum(1 for s in scores if 40 <= s < 60)
    cold = sum(1 for s in scores if s < 40)

    print(f"     🔥 Hot (80-100):  {hot}")
    print(f"     🟡 Warm (60-79):  {warm}")
    print(f"     🔵 Cool (40-59):  {cool}")
    print(f"     ⚪ Cold (0-39):   {cold}")

    tbf = sum(1 for l in leads if l.get("nexus_brand") == "TBF")
    dft = sum(1 for l in leads if l.get("nexus_brand") == "DFT")
    print(f"\n     🏷️  TBF: {tbf} | DFT: {dft}")

    # Hunter verification
    if args.verify_emails and HUNTER_API_KEY:
        print(f"\n  🔍 Verifying emails with Hunter...")
        verified = 0
        invalid = 0
        skipped = 0
        for i, lead in enumerate(leads):
            email = lead.get("email", "")
            if not email:
                skipped += 1
                continue
            # Only verify high-priority leads first (save Hunter credits)
            if lead.get("nexus_lead_score", 0) < 40:
                skipped += 1
                continue

            print(f"    [{i+1}] {email}...", end=" ", flush=True)
            result = hunter_verify_email(email)
            if result:
                lead["email_verification"] = result
                if result["status"] == "valid":
                    verified += 1
                    print(f"✅ valid ({result['score']})")
                elif result["status"] == "invalid":
                    invalid += 1
                    lead["do_not_email"] = True
                    print(f"❌ invalid")
                else:
                    print(f"⚠️ {result['status']} ({result['score']})")
            else:
                print("skip (no credits)")
                break
            time.sleep(0.5)

        print(f"\n     ✅ Verified: {verified} | ❌ Invalid: {invalid} | ⏭️ Skipped: {skipped}")

    # Find missing emails
    if args.find_missing_emails and HUNTER_API_KEY:
        missing = [l for l in leads if not l.get("email") and l.get("domain") and l.get("nexus_lead_score", 0) >= 40]
        if missing:
            print(f"\n  🔎 Finding emails for {len(missing)} contacts with Hunter...")
            found = 0
            for lead in missing:
                name = lead.get("contact_name", "")
                parts = name.split()
                if len(parts) < 2:
                    continue
                result = hunter_find_email(lead["domain"], parts[0], " ".join(parts[1:]))
                if result and result.get("email"):
                    lead["email"] = result["email"]
                    lead["email_source"] = "hunter"
                    lead["email_confidence"] = result.get("confidence", 0)
                    found += 1
                    print(f"    ✅ {name} → {result['email']} ({result['confidence']}%)")
                time.sleep(1)
            print(f"\n     📧 Found {found} new emails")

    # Save scored output
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    output_path = OUTPUT_DIR / f"scored_apollo_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump({"metadata": {
            "source": args.input, "total": len(leads),
            "scored_at": datetime.utcnow().isoformat(),
            "hot": hot, "warm": warm, "cool": cool, "cold": cold,
            "tbf": tbf, "dft": dft,
        }, "leads": leads}, f, indent=2)
    print(f"\n  💾 Scored data: {output_path}")

    # GHL Import
    if args.import_ghl:
        if not GHL_API_TOKEN or not GHL_LOCATION_ID:
            print("\n  ❌ GHL credentials not set.")
        else:
            print(f"\n  📤 Importing {len(leads)} leads to GHL...")
            field_map = load_field_map()
            imported = 0
            errors = 0

            for i, lead in enumerate(leads):
                company = lead.get("company_name", lead.get("contact_name", "?"))
                score = lead.get("nexus_lead_score", 0)
                brand = lead.get("nexus_brand", "?")
                temp = lead.get("prospect_temperature", "?")
                print(f"  [{i+1}/{len(leads)}] {company} (Score:{score} {brand} {temp})...", end=" ", flush=True)

                # Skip invalid emails
                if lead.get("do_not_email"):
                    print("⏭️ invalid email")
                    continue

                contact_id = import_to_ghl(lead, args.pipeline_id, args.stage_id, field_map)
                if contact_id:
                    print(f"✅")
                    imported += 1
                else:
                    print("⚠️")
                    errors += 1
                time.sleep(0.2)

            print(f"\n  {'━'*50}")
            print(f"  ✅ GHL Import: {imported} imported, {errors} errors")
            print(f"  {'━'*50}")

    # Top prospects
    print(f"\n  🎯 Top 10 Prospects:")
    top = sorted(leads, key=lambda l: l.get("nexus_lead_score", 0), reverse=True)[:10]
    for i, l in enumerate(top, 1):
        email = l.get("email", "?")
        ev = ""
        if isinstance(l.get("email_verification"), dict):
            ev = f" [{l['email_verification']['status']}]"
        print(f"  {i:2}. {l.get('company_name','?')[:25]:25} | {l.get('contact_name','?')[:20]:20} | Score: {l.get('nexus_lead_score',0):3} | {l.get('nexus_brand','?'):3} | {l.get('prospect_temperature','?'):4} | {email}{ev}")
        if l.get("score_reasons"):
            print(f"      Reasons: {', '.join(l['score_reasons'][:4])}")

    # Generate blueprint
    print(f"\n  📋 Generating GHL Workflow Blueprint...")
    blueprint = generate_workflow_blueprint()
    bp_path = REFS_DIR / "ghl-workflow-blueprint.md"
    REFS_DIR.mkdir(exist_ok=True)
    bp_path.write_text(blueprint)
    print(f"  💾 Blueprint: {bp_path}")

    print(f"\n  {'━'*60}")
    print(f"  Next steps:")
    print(f"  1. Review top prospects above")
    print(f"  2. Build GHL workflows from blueprint: {bp_path}")
    print(f"  3. Run: python3 scripts/sales_intel_brief.py --company \"[top prospect]\"")
    print(f"  {'━'*60}\n")


if __name__ == "__main__":
    main()
