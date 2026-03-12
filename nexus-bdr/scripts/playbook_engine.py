#!/usr/bin/env python3
"""
PLAYBOOK ENGINE — Terpene Belt Farms / Duty Free Terpenes
============================================================
5 playbooks with trigger rules, persona mapping, offer stacks,
and template-driven outreach. The system DECIDES which play to run
based on War Room signals, not generic prospecting.

Playbooks:
  1. VAPE_MARGIN_DEFENSE     — Supplier switch for vape brands
  2. BEVERAGE_INNOVATION     — GRAS-trajectory effects profiles for bev
  3. COMAN_ENABLEMENT        — Launch velocity for contract manufacturers
  4. REGULATORY_READINESS    — COA/compliance pack for audit-conscious buyers
  5. COMPETITOR_STRIKE        — Displacement when competitor has vulnerability

Usage:
    python3 playbook_engine.py --company "Mellow Fellow"
    python3 playbook_engine.py --company "Mellow Fellow" --playbook COMPETITOR_STRIKE
    python3 playbook_engine.py --list   # Show all playbooks
    python3 playbook_engine.py --score "Mellow Fellow"  # Score all playbooks for a company

Each playbook produces a complete Kill Shot Bundle with playbook-specific:
  - Email (tone, CTA, and offer matched to play)
  - LinkedIn DM
  - Call script (opener, objection handling, close)
  - HeyGen video script
  - 2-week pilot plan
  - Task payload
"""

import os, sys, json, re, argparse
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs" if (SCRIPT_DIR / "outputs").exists() else SCRIPT_DIR.parent / "outputs"
BUNDLE_ROOT = SCRIPT_DIR / "demo_bundle"

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from war_room_v2 import KnowledgeGraph
    WR = "v2"
except ImportError:
    from war_room import KnowledgeGraph
    WR = "v1"


# ═══════════════════════════════════════════════════════════
# PLAYBOOK DEFINITIONS
# ═══════════════════════════════════════════════════════════

PLAYBOOKS = {

    "VAPE_MARGIN_DEFENSE": {
        "name": "Vape Margin Defense / Supplier Switch",
        "short": "Switch kit + 2-week validation + SKU mapping",
        "description": "For vape brands experiencing margin pressure, inconsistency, or supplier friction. Lead with cost comparison and batch reliability.",
        "kpi": "Meetings booked + pilots started",
        "offer": "R&D validation kit (3-5 CDT profiles matched to current SKUs) + 2-week side-by-side comparison plan",
        "persona_targets": ["CEO", "COO", "VP Operations", "VP R&D", "Head of Product", "Formulation Lead", "Procurement"],
        "trigger_rules": {
            "required_any": ["vape", "disposable", "cartridge", "pod", "510", "dab", "concentrate"],
            "boost_signals": ["trustpilot_below_4.0", "trustpilot_below_3.5", "hiring_signal", "reddit_complaint", "price_discussion", "competitor_weakness"],
            "boost_features": ["current_supplier", "switching_triggers"],
        },
        "confidence_weights": {
            "has_vape_products": 30,
            "has_current_supplier": 20,
            "supplier_has_vulnerability": 25,
            "has_switching_triggers": 15,
            "brief_completed": 10,
        },
        "email_template": {
            "subject": "Quick question about terpene consistency at {company}",
            "body": """Hi {contact},

I've been tracking the terpene supplier landscape for vape brands like {company}, and a few signals came across our system that usually show up right before teams re-evaluate their formulation stack.

Rather than pitch, I'd rather make this easy: we can send a small R&D kit — 3 to 5 CDT profiles matched to your current SKUs — plus a 2-week validation plan so your team can compare:

- Sensory consistency batch-to-batch
- Lead times and supply reliability
- Documentation readiness (COAs, specs, compliance)
- Cost structure (our vertically integrated model typically saves 25-40% on CDT)

Worth a 10-minute call this week to see if it's relevant?

Best,
Shareef — Terpene Belt Farms""",
        },
        "dm_template": """Hey {contact} — I put together a quick brief on {company}'s terpene supply chain. We're seeing a few signals that usually mean brands are re-checking consistency and pricing on their vape profiles.

We can send a small R&D kit (3-5 CDT profiles matched to your SKUs) + a 2-week validation plan. No commitment, just a side-by-side comparison.

Want me to share the 1-pager?""",
        "call_template": """CALL SCRIPT: {company} — VAPE MARGIN DEFENSE

Contact: {contact} ({title})

[OPENER]
"Hey {contact} — Shareef from Terpene Belt Farms. Quick one.

We track terpene supply signals across vape brands in your space. When we see a couple of these triggers together — consistency issues, pricing pressure, lead time friction — teams usually start re-evaluating their formulation stack.

I'm not trying to replace anyone today. But if I send a small R&D kit with 3-5 CDT profiles matched to your top SKUs, plus a 2-week validation plan, would you be the right person to run that comparison?"

[IF INTERESTED]
"Great. Our lab will put together profiles matched to your {product_lines}. You'll get full COAs, sensory notes, and a validation checklist. Takes 2 weeks, zero commitment, and you'll have a documented alternative on file."

[OBJECTION: Happy with current supplier]
"Totally get that. Most of our partners said the same thing. This isn't about replacing — it's about having a validated backup. If consistency, pricing, or lead times ever become an issue, you already have a comparison ready. Think of it as insurance for your formulation stack."

[OBJECTION: We do our own extraction]
"That's actually ideal. We work with several vertically integrated brands who use our profiles as a benchmark or supplement for strains they can't source consistently. The R&D kit lets your team compare side-by-side at no risk."

[CLOSE]
"Can I get the best shipping address for that R&D kit?"
""",
        "heygen_template": """Hey {contact} — Shareef here from Terpene Belt Farms.

I'm reaching out because our market intelligence system flagged {company} as a vape brand that might benefit from validating their terpene supply chain.

Here's what I'd like to do: send a small R&D kit — 3 to 5 CDT profiles matched to your current product direction — plus a 2-week validation plan your team can run side-by-side.

Full COAs, sensory notes, consistency documentation — everything you need for a clean comparison.

If that's useful, hit reply and I'll get it shipped this week.""",
        "pilot_plan": [
            "Day 1-3: Ship R&D validation kit (3-5 CDT profiles matched to top vape SKUs)",
            "Day 4-7: Side-by-side sensory evaluation with formulation team",
            "Day 8-10: Cost/lead-time comparison + COA documentation review",
            "Day 11-14: Small-batch pilot run (1-2 SKUs) with full QC documentation",
        ],
    },

    "BEVERAGE_INNOVATION": {
        "name": "Beverage Innovation / Effects Profiles",
        "short": "Effects-profile kit + sensory descriptors + GRAS trajectory",
        "description": "For beverage and functional food brands exploring terpene-enhanced products. Lead with effects language (not health claims), GRAS positioning, and sensory design.",
        "kpi": "R&D trial requests",
        "offer": "Effects-profile tasting kit + sensory descriptor guide + formulation notes + GRAS-trajectory documentation",
        "persona_targets": ["VP Innovation", "R&D Director", "Head of Product Development", "Flavor Scientist", "CEO"],
        "trigger_rules": {
            "required_any": ["beverage", "drink", "seltzer", "functional", "wellness", "food", "edible", "gummy", "supplement"],
            "boost_signals": ["new_product_launch", "funding_news", "research_breakthrough"],
            "boost_features": ["terpene_relevance"],
        },
        "confidence_weights": {
            "has_beverage_products": 35,
            "is_innovation_stage": 20,
            "has_funding": 15,
            "terpene_relevance_high": 20,
            "brief_completed": 10,
        },
        "email_template": {
            "subject": "Terpene effects profiles for {company}'s product development",
            "body": """Hi {contact},

We work with beverage and functional brands on terpene-enhanced product development — specifically helping R&D teams design effects-based profiles (calm, focus, uplift, refresh) with full sensory documentation and GRAS-trajectory ingredients.

For {company}, we can put together a small effects-profile tasting kit with:

- 3-5 functional profiles designed for beverage applications
- Sensory descriptors and flavor pairing notes
- Formulation guidelines (solubility, stability, dosing)
- GRAS-trajectory documentation for your regulatory team

Would a 15-minute call make sense to see if this fits your product roadmap?

Best,
Shareef — Terpene Belt Farms""",
        },
        "dm_template": """Hey {contact} — we help beverage/functional brands design terpene effects profiles (calm, focus, uplift) with GRAS-trajectory ingredients and full sensory documentation.

I can send a small tasting kit + formulation notes tailored to {company}'s direction. Worth a quick look?""",
        "call_template": """CALL SCRIPT: {company} — BEVERAGE INNOVATION

Contact: {contact} ({title})

[OPENER]
"Hey {contact} — Shareef from Terpene Belt Farms. We work with beverage and functional brands on terpene-enhanced product development.

What we do differently is effects-based profiling — calm, focus, uplift, refresh — with full sensory documentation and GRAS-trajectory ingredients. No health claims, just functional design that your R&D team can work with.

I'd love to send a small effects-profile tasting kit tailored to {company}'s direction. Would you be the right person to evaluate that?"

[IF INTERESTED]
"Great. We'll design 3-5 profiles based on your product direction. Each comes with sensory descriptors, flavor pairing notes, formulation guidelines for beverage applications, and GRAS-trajectory documentation for your regulatory team."

[OBJECTION: We already work with flavor houses]
"Perfect — we're not replacing your flavor work. We're adding a functional layer. Think of terpenes as the effects architecture underneath your flavor profile. Many brands use our CDT profiles alongside their existing flavor systems."

[CLOSE]
"What's the best way to get a tasting kit to your R&D team?"
""",
        "heygen_template": """Hey {contact} — Shareef from Terpene Belt Farms.

We help beverage brands design effects-based terpene profiles — think calm, focus, uplift — with GRAS-trajectory ingredients and full sensory documentation. No health claims, just functional product design.

I'd love to send {company} a small effects-profile tasting kit with formulation notes tailored to your product direction.

If that's interesting, hit reply and I'll get it set up.""",
        "pilot_plan": [
            "Day 1-3: Ship effects-profile tasting kit (3-5 functional profiles for beverage)",
            "Day 4-7: Sensory evaluation with R&D/flavor team",
            "Day 8-12: Formulation trials — solubility, stability, dosing in target matrix",
            "Day 13-14: Review results + discuss custom profile development for launch SKUs",
        ],
    },

    "COMAN_ENABLEMENT": {
        "name": "Co-Manufacturer Enablement",
        "short": "Launch menu + lead-time/MOQ + rapid new SKU support",
        "description": "For contract manufacturers and white-label producers needing a reliable terpene supply partner with fast turnaround, flexible MOQs, and documentation.",
        "kpi": "Partner onboarding calls",
        "offer": "Terpene menu with profiles, MOQs, lead times + bulk pricing + documentation package",
        "persona_targets": ["VP Manufacturing", "Operations Director", "Procurement Manager", "Production Lead", "CEO"],
        "trigger_rules": {
            "required_any": ["manufacturer", "co-man", "white label", "private label", "contract", "production", "manufacturing"],
            "boost_signals": ["hiring_signal", "new_product_launch"],
            "boost_features": [],
        },
        "confidence_weights": {
            "is_manufacturer": 35,
            "has_multiple_clients": 15,
            "scaling_signals": 20,
            "brief_completed": 10,
            "has_contacts": 20,
        },
        "email_template": {
            "subject": "Terpene supply partnership for {company}",
            "body": """Hi {contact},

We work with contract manufacturers and white-label producers as a terpene supply partner — providing consistent CDT and botanical profiles with fast turnaround, flexible MOQs, and full documentation.

For {company}, here's what we can set up:

- Full terpene menu with CDT + botanical profiles
- MOQ and lead-time options designed for co-man flexibility
- Bulk pricing structure with volume tiers
- Complete documentation package (COAs, specs, safety data, compliance)

Would a quick call make sense to explore a supply partnership?

Best,
Shareef — Terpene Belt Farms""",
        },
        "dm_template": """Hey {contact} — we partner with co-mans and white-label producers as a terpene supply source. Fast turnaround, flexible MOQs, full documentation.

I can send our terpene menu + pricing structure. Worth a look for {company}?""",
        "call_template": """CALL SCRIPT: {company} — CO-MAN ENABLEMENT

Contact: {contact} ({title})

[OPENER]
"Hey {contact} — Shareef from Terpene Belt Farms. We partner with contract manufacturers as a terpene supply source.

What makes us different for co-mans: fast turnaround, flexible MOQs, and a documentation package that covers every audit. We know your clients need speed and your team needs consistency.

Can I send our terpene menu and pricing structure?"

[IF INTERESTED]
"Great. I'll send the full menu — CDT and botanical profiles with MOQs, lead times, and volume pricing. Plus our documentation package so your compliance team can review upfront."

[CLOSE]
"What's the best email for that menu?"
""",
        "heygen_template": """Hey {contact} — Shareef from Terpene Belt Farms.

We partner with co-mans and white-label producers as a terpene supply source. Fast turnaround, flexible MOQs, and documentation that covers every audit.

I'd love to send {company} our terpene menu and pricing structure.

Hit reply and I'll get it over to you.""",
        "pilot_plan": [
            "Day 1-2: Ship terpene menu + sample kit (top 10 profiles) + pricing structure",
            "Day 3-5: Review with procurement/operations team",
            "Day 6-10: Trial order on 2-3 profiles for client project",
            "Day 11-14: Documentation review + onboarding as approved vendor",
        ],
    },

    "REGULATORY_READINESS": {
        "name": "Regulatory & Audit Readiness",
        "short": "COA/spec bundle + process story + clean-room posture",
        "description": "For buyers where compliance, documentation, and audit readiness are the primary concern. Lead with COA quality, process transparency, and regulatory positioning.",
        "kpi": "Procurement/compliance engaged",
        "offer": "Documentation package: COAs, specs, safety data, process documentation, clean-room certifications",
        "persona_targets": ["VP Quality", "Quality Assurance Director", "Compliance Officer", "Procurement Manager", "Regulatory Affairs"],
        "trigger_rules": {
            "required_any": ["pharmaceutical", "pharma", "medical", "clinical", "GMP", "FDA", "compliance", "regulatory", "audit"],
            "boost_signals": ["regulatory_change", "clinical_trial"],
            "boost_features": [],
        },
        "confidence_weights": {
            "is_regulated_industry": 35,
            "has_compliance_focus": 25,
            "regulatory_signal": 20,
            "brief_completed": 10,
            "has_contacts": 10,
        },
        "email_template": {
            "subject": "Terpene supply with full documentation + audit readiness — {company}",
            "body": """Hi {contact},

We work with brands where regulatory readiness and documentation quality are non-negotiable. Our terpene supply comes with:

- Full panel COAs for every batch (potency, residual solvents, heavy metals, microbial)
- Detailed specifications and safety data sheets
- Process documentation and clean-room manufacturing posture
- Traceability from source material to finished product

For {company}, I can send our documentation package upfront so your compliance team can evaluate before any product discussion.

Would that be useful?

Best,
Shareef — Terpene Belt Farms""",
        },
        "dm_template": """Hey {contact} — we supply terpenes with full-panel COAs, process documentation, and audit-ready specs. Everything your compliance team needs upfront.

Can I send {company}'s team our documentation package?""",
        "call_template": """CALL SCRIPT: {company} — REGULATORY READINESS

Contact: {contact} ({title})

[OPENER]
"Hey {contact} — Shareef from Terpene Belt Farms. I know for brands like {company}, documentation and audit readiness come before everything else.

We lead with our documentation package — full panel COAs, process documentation, clean-room posture, and traceability. Can I send that to your compliance team for evaluation?"

[IF INTERESTED]
"Great. I'll send the full package: COAs, specs, SDS, process documentation, and our clean-room certification materials. Your team can review at their pace — no product commitment required."

[CLOSE]
"Who on your team should I send the documentation package to?"
""",
        "heygen_template": """Hey {contact} — Shareef from Terpene Belt Farms.

I know documentation and compliance come first for {company}. So rather than pitch products, I want to send your team our documentation package upfront.

Full panel COAs, process documentation, clean-room certifications, and full traceability. Your compliance team can evaluate before any product conversation.

Hit reply and I'll get it sent over.""",
        "pilot_plan": [
            "Day 1-2: Ship documentation package (COAs, specs, SDS, process docs)",
            "Day 3-7: Compliance/QA team review",
            "Day 8-10: Follow-up call to address documentation questions",
            "Day 11-14: Sample request + vendor qualification process",
        ],
    },

    "COMPETITOR_STRIKE": {
        "name": "Competitor Vulnerability Strike",
        "short": "Replacement matrix + cost comparison + pilot",
        "description": "When a specific competitor has active vulnerability signals (low reviews, quality complaints, pricing issues). Lead with the specific weakness and position TBF as the validated alternative.",
        "kpi": "Competitor displacement wins",
        "offer": "Replacement matrix (their profiles → TBF equivalents) + cost comparison + 2-week pilot",
        "persona_targets": ["CEO", "COO", "VP Operations", "VP R&D", "Procurement", "Head of Product"],
        "trigger_rules": {
            "required_any": [],  # No product requirement — this is competitor-triggered
            "boost_signals": ["trustpilot_below_3.5", "trustpilot_below_4.0", "quality_complaint_about_competitor", "reddit_complaint", "reddit_supplier_seeking"],
            "boost_features": ["current_supplier"],
            "required_signals": ["trustpilot_below_4.0", "trustpilot_below_3.5", "quality_complaint_about_competitor", "competitor_weakness"],
        },
        "confidence_weights": {
            "supplier_has_vulnerability": 35,
            "has_current_supplier": 20,
            "trustpilot_below_4": 20,
            "has_switching_triggers": 15,
            "brief_completed": 10,
        },
        "email_template": {
            "subject": "Quick thought on your terpene supply chain — {company}",
            "body": """Hi {contact},

I'll be direct: we've been tracking terpene supplier performance across the industry, and {supplier}'s service quality has been flagging in public reviews and industry channels lately.

If {company} is evaluating alternatives (or just wants one documented), we can build a replacement matrix — mapping your current profiles to TBF equivalents — plus a cost comparison and a 2-week pilot plan.

No disruption to your current supply. Just a validated backup with:

- Profile-matched replacements for your top SKUs
- Side-by-side sensory comparison
- Cost and lead-time analysis
- Full documentation (COAs, specs, process)

Worth a 10-minute conversation?

Best,
Shareef — Terpene Belt Farms""",
        },
        "dm_template": """Hey {contact} — we've been tracking terpene supplier quality signals, and {supplier}'s reviews have been slipping.

If {company} wants a documented alternative ready, I can build a replacement matrix (your current profiles → TBF equivalents) + cost comparison. No commitment, just having a validated backup.

Interested?""",
        "call_template": """CALL SCRIPT: {company} — COMPETITOR STRIKE

Contact: {contact} ({title})
Target supplier: {supplier}

[OPENER]
"Hey {contact} — Shareef from Terpene Belt Farms. I'll be straightforward: we track terpene supplier quality across the industry, and {supplier}'s performance has been flagging in reviews and industry channels.

I'm not saying you need to switch — but if you want a documented alternative, I can build a replacement matrix mapping your current profiles to TBF equivalents, with a cost comparison and 2-week pilot plan. No disruption, just a validated backup."

[IF INTERESTED]
"Here's what we'll do: map your top 5-10 SKU profiles to our CDT/botanical equivalents, run a cost and lead-time comparison, and set up a 2-week side-by-side validation. You'll have a documented alternative on file either way."

[OBJECTION: We haven't had issues]
"That's good to hear. This is more about risk mitigation — having a validated alternative documented before you ever need it. Think of it as insurance for your formulation stack. The validation takes 2 weeks and costs you nothing."

[CLOSE]
"Can I get a list of your top 5 SKU profiles to start the replacement matrix?"
""",
        "heygen_template": """Hey {contact} — Shareef from Terpene Belt Farms.

I'll be direct: we track terpene supplier quality across the industry, and {supplier} has been showing some concerning signals in public reviews.

I'm not here to badmouth anyone — but if {company} wants a documented alternative ready, I can build a replacement matrix mapping your current profiles to ours, plus a cost comparison and 2-week pilot plan.

No disruption to your current supply. Just a validated backup.

Hit reply if that's useful.""",
        "pilot_plan": [
            "Day 1-3: Build replacement matrix (competitor profiles → TBF CDT/botanical equivalents)",
            "Day 4-7: Ship matched R&D kit + cost/lead-time comparison document",
            "Day 8-11: Side-by-side sensory and QC evaluation",
            "Day 12-14: Decision meeting — transition plan or documented backup",
        ],
    },
}


# ═══════════════════════════════════════════════════════════
# PLAYBOOK SELECTOR — Scores all playbooks for a company
# ═══════════════════════════════════════════════════════════

def score_playbooks(graph, company_key, company):
    """Score all playbooks for a company and return ranked list."""
    results = []
    recent_signals = graph.get_recent_signals(hours=168)
    entity_signals = [s for s in recent_signals if company_key in s.get("entities", [])]

    # Gather company attributes
    desc = json.dumps(company, default=str).lower()
    has_supplier = bool(company.get("current_supplier", ""))
    has_triggers = len(company.get("switching_triggers", [])) > 0
    has_brief = company.get("brief_completed", False)
    contacts = company.get("contacts", 0)

    # Get competitor data if supplier known
    supplier_vuln = False
    supplier_name = company.get("current_supplier", "")
    if supplier_name:
        competitors = graph.get_entities_by_type("competitor")
        for ck, cv in competitors.items():
            if supplier_name.lower().split("(")[0].strip() in cv.get("name", "").lower():
                tp = cv.get("trustpilot_rating")
                if tp and tp < 4.0:
                    supplier_vuln = True

    signal_types = {s.get("type") for s in entity_signals}

    for pb_id, pb in PLAYBOOKS.items():
        score = 0
        reasons = []
        rules = pb["trigger_rules"]

        # Check product/industry match
        required = rules.get("required_any", [])
        if required:
            matched = [r for r in required if r in desc]
            if matched:
                score += 25
                reasons.append(f"Product match: {', '.join(matched[:3])}")
            else:
                # No product match = low confidence unless it's COMPETITOR_STRIKE
                if pb_id != "COMPETITOR_STRIKE":
                    score -= 20

        # Check required signals (for COMPETITOR_STRIKE)
        req_sigs = rules.get("required_signals", [])
        if req_sigs:
            matched_sigs = [s for s in req_sigs if s in signal_types]
            if matched_sigs:
                score += 20
                reasons.append(f"Required signals: {', '.join(matched_sigs[:3])}")
            elif not supplier_vuln:
                score -= 30  # Missing required signal = not this playbook

        # Boost from signal types
        for boost_sig in rules.get("boost_signals", []):
            if boost_sig in signal_types:
                score += 8
                reasons.append(f"Signal: {boost_sig}")

        # Boost from features
        for feat in rules.get("boost_features", []):
            if feat == "current_supplier" and has_supplier:
                score += 10
                reasons.append("Has known supplier")
            elif feat == "switching_triggers" and has_triggers:
                score += 10
                reasons.append(f"Switching triggers: {len(company.get('switching_triggers', []))}")
            elif feat == "terpene_relevance" and company.get("terpene_relevance"):
                score += 10
                reasons.append("Terpene relevance confirmed")

        # Standard boosts
        if has_brief:
            score += pb["confidence_weights"].get("brief_completed", 5)
            reasons.append("Brief completed")
        if has_supplier and supplier_vuln:
            score += pb["confidence_weights"].get("supplier_has_vulnerability", 15)
            reasons.append("Supplier vulnerable")
        if contacts >= 5:
            score += 5

        confidence = "HIGH" if score >= 50 else "MEDIUM" if score >= 25 else "LOW"

        results.append({
            "playbook_id": pb_id,
            "name": pb["name"],
            "short": pb["short"],
            "score": score,
            "confidence": confidence,
            "reasons": reasons,
            "kpi": pb["kpi"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def select_playbook(graph, company_key, company, override=None):
    """Select the best playbook or use override."""
    if override and override in PLAYBOOKS:
        pb = PLAYBOOKS[override]
        return override, pb, "HIGH (manual override)"

    scored = score_playbooks(graph, company_key, company)
    if scored and scored[0]["score"] > 0:
        best = scored[0]
        return best["playbook_id"], PLAYBOOKS[best["playbook_id"]], best["confidence"]

    # Default fallback
    return "VAPE_MARGIN_DEFENSE", PLAYBOOKS["VAPE_MARGIN_DEFENSE"], "LOW (default)"


# ═══════════════════════════════════════════════════════════
# BUNDLE GENERATOR — Playbook-specific Kill Shot
# ═══════════════════════════════════════════════════════════

def generate_playbook_bundle(graph, company_key, company, playbook_id, playbook, confidence, dry_run=False):
    """Generate a complete Kill Shot Bundle using the selected playbook."""
    import shutil

    now = datetime.utcnow()
    stamp = now.strftime("%Y%m%d_%H%M")
    safe_name = re.sub(r'[^a-z0-9]+', '_', (company.get("name") or "target").lower()).strip('_')
    bundle_dir = BUNDLE_ROOT / f"{safe_name}_{playbook_id.lower()}_{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    name = company.get("name", "Target")
    contact = company.get("top_contact", "") or "there"
    title = company.get("top_title", "")
    domain = company.get("domain", "")
    supplier = company.get("current_supplier", "Unknown")
    product_lines = company.get("terpene_relevance", "their product lines")

    fmt = {
        "company": name, "contact": contact, "title": title,
        "domain": domain, "supplier": supplier, "product_lines": product_lines,
    }

    # Get trigger signals
    recent = graph.get_recent_signals(hours=336)
    entity_signals = [s for s in recent if company_key in s.get("entities", [])]
    trigger_ids = [s["id"] for s in entity_signals if s.get("id")][:10]

    # 01 — WHY NOW (structured triggers)
    why = []
    why.append(f"# Why Now: {name}")
    why.append(f"*Playbook: {playbook['name']}*")
    why.append(f"*Confidence: {confidence}*")
    why.append(f"*Generated: {now.strftime('%B %d, %Y')}*\n")
    why.append(f"---\n")
    why.append(f"## Triggers\n")

    triggers_data = []
    if supplier and supplier != "Unknown":
        triggers_data.append({"trigger": "Known supplier identified", "evidence": supplier, "implication": "Displacement opportunity exists"})
    if company.get("switching_triggers"):
        for t in company["switching_triggers"]:
            triggers_data.append({"trigger": "Switching trigger", "evidence": t, "implication": "Active evaluation window"})
    for sig in entity_signals[:5]:
        triggers_data.append({
            "trigger": sig.get("type", "").replace("_", " ").title(),
            "evidence": sig.get("data", {}).get("title", sig.get("data", {}).get("competitor", ""))[:80],
            "implication": f"Source: {sig.get('source', '?')} (reliability: {sig.get('source_reliability', '?')})"
        })
    if not triggers_data:
        triggers_data.append({"trigger": "Pipeline score", "evidence": f"Score {company.get('avg_score', 0)}", "implication": "High-value target"})

    for td in triggers_data:
        why.append(f"**{td['trigger']}**")
        why.append(f"- Evidence: {td['evidence']}")
        why.append(f"- Implication: {td['implication']}\n")

    why.append(f"## Recommended Offer\n")
    why.append(f"{playbook['offer']}\n")
    why.append(f"## KPI\n")
    why.append(f"{playbook['kpi']}")

    (bundle_dir / "01_why_now.md").write_text("\n".join(why), encoding="utf-8")

    # 02 — BRIEF DOCX
    docx_found = False
    for search_dir in [OUTPUT_DIR, SCRIPT_DIR / "outputs"]:
        for pattern in [f"*{safe_name}*brief*.docx", "*mellow*brief*.docx"]:
            for f in search_dir.glob(pattern):
                shutil.copy2(f, bundle_dir / "02_account_brief.docx")
                docx_found = True
                break
            if docx_found:
                break
        if docx_found:
            break
    if not docx_found:
        (bundle_dir / "02_NOTE_generate_brief.txt").write_text(
            f"python3 sales_intel_brief_v4.py --company \"{name}\" --domain {domain}", encoding="utf-8")

    # 03 — COMPETITOR WEDGE
    wedge = []
    wedge.append(f"# Competitor Wedge: {name}")
    wedge.append(f"*Playbook: {playbook['name']}*\n---\n")
    if supplier and supplier != "Unknown":
        wedge.append(f"## Target Supplier: {supplier}\n")
        wedge.append(f"## TBF Advantages")
        wedge.append(f"- Batch-to-batch consistency with full COA documentation")
        wedge.append(f"- Vertically integrated CDT: $1.5-3K/L vs premium $5-8K/L")
        wedge.append(f"- 2-week validation program — zero disruption\n")
    wedge.append(f"## Pilot Plan")
    for step in playbook["pilot_plan"]:
        wedge.append(f"- {step}")
    (bundle_dir / "03_competitor_wedge.md").write_text("\n".join(wedge), encoding="utf-8")

    # 04-07 — OUTREACH ASSETS (playbook-specific templates)
    et = playbook["email_template"]
    (bundle_dir / "04_email.txt").write_text(
        f"Subject: {et['subject'].format(**fmt)}\n\n{et['body'].format(**fmt)}", encoding="utf-8")

    (bundle_dir / "05_linkedin_dm.txt").write_text(
        playbook["dm_template"].format(**fmt), encoding="utf-8")

    (bundle_dir / "06_call_opener.txt").write_text(
        playbook["call_template"].format(**fmt), encoding="utf-8")

    (bundle_dir / "07_heygen_script.txt").write_text(
        playbook["heygen_template"].format(**fmt), encoding="utf-8")

    # 08 — TASK PAYLOAD
    task = {
        "company_key": company_key, "company_name": name,
        "contact": contact, "title": title, "domain": domain,
        "playbook_id": playbook_id, "playbook_name": playbook["name"],
        "confidence": confidence,
        "actions": [
            {"step": 1, "type": "send_email", "asset": "04_email.txt", "day": 0},
            {"step": 2, "type": "send_linkedin_dm", "asset": "05_linkedin_dm.txt", "day": 1},
            {"step": 3, "type": "send_heygen_video", "asset": "07_heygen_script.txt", "day": 3},
            {"step": 4, "type": "call", "asset": "06_call_opener.txt", "day": 5},
        ],
        "pilot_plan": playbook["pilot_plan"],
        "generated_at": now.isoformat() + "Z",
        "dry_run": dry_run,
    }
    (bundle_dir / "08_task_payload.json").write_text(json.dumps(task, indent=2), encoding="utf-8")

    # 09 — ATTRIBUTION
    if WR == "v2":
        action_id = graph.create_action(
            action_type=f"playbook_{playbook_id.lower()}",
            target_entity=company_key,
            action_data={"company": name, "playbook": playbook_id, "confidence": confidence,
                         "signals_used": len(trigger_ids)},
            trigger_signal_ids=trigger_ids,
            top_features=[f"playbook:{playbook_id}", f"confidence:{confidence}"],
        )
    else:
        action_id = graph.record_action(f"playbook_{playbook_id.lower()}", company_key,
            {"company": name, "playbook": playbook_id})

    graph.save()

    attr = {"run_id": stamp, "action_id": action_id, "playbook_id": playbook_id,
            "confidence": confidence, "company_key": company_key, "company_name": name,
            "trigger_signal_ids": trigger_ids, "bundle_path": str(bundle_dir)}
    (bundle_dir / "09_attribution.json").write_text(json.dumps(attr, indent=2), encoding="utf-8")

    return bundle_dir, action_id, trigger_ids


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def find_company(graph, query):
    companies = graph.get_entities_by_type("company")
    q = query.strip().lower()
    for key, c in companies.items():
        name = (c.get("name") or "").lower()
        if q == name or q in name or name in q:
            return key, c
    for key, c in companies.items():
        domain = (c.get("domain") or "").lower()
        if domain and (q in domain or domain in q):
            return key, c
    print(f"\n  Company not found: '{query}'")
    print(f"  Available:")
    for k, c in sorted(companies.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True)[:10]:
        print(f"    {c.get('name','?')} [{c.get('domain','')}]")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Playbook Engine — TBF/DFT")
    parser.add_argument("--company", help="Company name or domain")
    parser.add_argument("--playbook", help="Override playbook selection")
    parser.add_argument("--list", action="store_true", help="List all playbooks")
    parser.add_argument("--score", help="Score all playbooks for a company")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list:
        print(f"\n{'═'*60}")
        print(f"  PLAYBOOK ENGINE — 5 Playbooks")
        print(f"{'═'*60}\n")
        for pid, pb in PLAYBOOKS.items():
            print(f"  {pid}")
            print(f"    {pb['name']}")
            print(f"    Offer: {pb['short']}")
            print(f"    KPI: {pb['kpi']}")
            print()
        return

    if not args.company and not args.score:
        parser.print_help()
        return

    graph = KnowledgeGraph()
    target = args.company or args.score
    company_key, company = find_company(graph, target)

    if args.score:
        print(f"\n{'═'*60}")
        print(f"  PLAYBOOK SCORES: {company.get('name', '?')}")
        print(f"{'═'*60}\n")
        scored = score_playbooks(graph, company_key, company)
        for s in scored:
            emoji = "🟢" if s["confidence"] == "HIGH" else "🟡" if s["confidence"] == "MEDIUM" else "🔴"
            print(f"  {emoji} {s['playbook_id']:<25} Score: {s['score']:>4}  [{s['confidence']}]")
            print(f"     {s['name']}")
            if s["reasons"]:
                for r in s["reasons"][:3]:
                    print(f"       · {r}")
            print()
        return

    # Select playbook
    pb_id, pb, confidence = select_playbook(graph, company_key, company, args.playbook)

    print(f"\n{'═'*60}")
    print(f"  PLAYBOOK ENGINE")
    print(f"{'═'*60}\n")
    print(f"  Target: {company.get('name', '?')}")
    print(f"  Playbook: {pb['name']}")
    print(f"  Confidence: {confidence}")
    print(f"  Offer: {pb['short']}")
    print()

    bundle_dir, action_id, trigger_ids = generate_playbook_bundle(
        graph, company_key, company, pb_id, pb, confidence, args.dry_run)

    print(f"{'─'*60}")
    print(f"  ✅ BUNDLE: {bundle_dir}/")
    print(f"  ✅ Action: {action_id}")
    print(f"  ✅ Attribution: {len(trigger_ids)} trigger signals")
    print(f"{'─'*60}")
    print(f"\n  Contents:")
    for f in sorted(bundle_dir.iterdir()):
        print(f"    {f.name} ({f.stat().st_size:,} bytes)")
    print(f"\n  Record outcome:")
    print(f"  python3 war_room_v2.py learn --action-id {action_id} --outcome meeting")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
