#!/usr/bin/env python3
"""
KILL SHOT BUNDLE — One-command outreach package
=================================================
Produces a complete, send-ready bundle for any target account.
Logs attribution in War Room v2 so the learning loop fires.

Usage:
    python3 kill_shot_bundle.py --company "Mellow Fellow"
    python3 kill_shot_bundle.py --company "Mellow Fellow" --dry-run

Output:
    demo_bundle/<company>_<timestamp>/
      01_why_now.md
      02_account_brief.docx
      03_competitor_wedge.md
      04_email.txt
      05_linkedin_dm.txt
      06_call_opener.txt
      07_heygen_script.txt
      08_task_payload.json
      09_attribution.json

Then demo the learning loop:
    python3 war_room_v2.py learn --action-id <id> --outcome meeting
    python3 war_room_v2.py status
"""

import os, sys, json, argparse, re, shutil
from datetime import datetime
from pathlib import Path

# ── Resolve paths ──
SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs" if (SCRIPT_DIR / "outputs").exists() else SCRIPT_DIR.parent / "outputs"
DEMO_ROOT = SCRIPT_DIR / "demo_bundle"

# ── Import War Room ──
sys.path.insert(0, str(SCRIPT_DIR))
KnowledgeGraph = None
WR_OUTPUT = OUTPUT_DIR
WR_VERSION = None
try:
    from war_room import KnowledgeGraph, OUTPUT_DIR as WR_OUTPUT
    WR_VERSION = "v1"
except ImportError:
    pass

if not KnowledgeGraph:
    try:
        from war_room_v2 import KnowledgeGraph, OUTPUT_DIR as WR_OUTPUT
        WR_VERSION = "v2"
    except ImportError:
        pass

if not KnowledgeGraph:
    print("  ⚠️  War Room not available — bundle will generate without knowledge graph integration")


def find_company(graph, query):
    """Find a company entity by name, domain, or partial match."""
    companies = graph.get_entities_by_type("company")
    q = query.strip().lower()

    # Exact key match
    for key, c in companies.items():
        if q == key:
            return key, c

    # Name match (exact then partial)
    for key, c in companies.items():
        name = (c.get("name") or "").lower()
        if q == name:
            return key, c

    for key, c in companies.items():
        name = (c.get("name") or "").lower()
        if q in name or name in q:
            return key, c

    # Domain match
    for key, c in companies.items():
        domain = (c.get("domain") or "").lower().replace("www.", "").rstrip("/")
        if domain and (q in domain or domain in q):
            return key, c

    # List available companies to help user
    print(f"\n  Could not find: '{query}'")
    print(f"  Available companies in War Room:")
    for key, c in sorted(companies.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True)[:15]:
        print(f"    {c.get('name', '?')} [{c.get('domain', '')}]")
    sys.exit(1)


def find_competitor_data(graph, supplier_name):
    """Find competitor entity data for a supplier."""
    if not supplier_name:
        return None
    competitors = graph.get_entities_by_type("competitor")
    for key, comp in competitors.items():
        if supplier_name.lower() in (comp.get("name") or "").lower():
            return comp
    return None


def build_bundle(graph, company_key, company, dry_run=False):
    """Generate the complete kill shot bundle."""
    now = datetime.utcnow()
    stamp = now.strftime("%Y%m%d_%H%M")
    safe_name = re.sub(r'[^a-z0-9]+', '_', (company.get("name") or "target").lower()).strip('_')
    bundle_dir = DEMO_ROOT / f"{safe_name}_{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    company_name = company.get("name", "Target Company")
    contact = company.get("top_contact", "") or "there"
    title = company.get("top_title", "")
    domain = company.get("domain", "")
    supplier = company.get("current_supplier", "")
    tier = company.get("pipeline_tier", "unknown")
    score = company.get("avg_score", 0)
    contacts_count = company.get("contacts", 0)
    switching_triggers = company.get("switching_triggers", [])
    terpene_relevance = company.get("terpene_relevance", "")
    annual_value = company.get("annual_value", "")

    # Get signals linked to this entity
    recent = graph.get_recent_signals(hours=24*14)
    entity_signals = [s for s in recent if company_key in s.get("entities", [])]
    entity_signals.sort(key=lambda x: x.get("effective_weight", x.get("weight", 0)) * x.get("strength", 1), reverse=True)
    trigger_signal_ids = [s.get("id") for s in entity_signals if s.get("id")][:10]

    # Get competitor data
    competitor = find_competitor_data(graph, supplier)

    # ══════════════════════════════════════════════
    # 01 — WHY NOW
    # ══════════════════════════════════════════════
    lines = []
    lines.append(f"# Why Now: {company_name}")
    lines.append(f"*Generated {now.strftime('%B %d, %Y at %H:%M UTC')} by Nexus BDR*\n")
    lines.append(f"---\n")

    lines.append(f"## Account Snapshot")
    lines.append(f"- **Company:** {company_name}")
    lines.append(f"- **Domain:** {domain}")
    lines.append(f"- **Pipeline tier:** {tier.upper()}")
    lines.append(f"- **Nexus score:** {score}")
    lines.append(f"- **Contacts identified:** {contacts_count}")
    lines.append(f"- **Primary contact:** {contact}" + (f" ({title})" if title else ""))
    if supplier:
        lines.append(f"- **Current supplier:** {supplier}")
    if annual_value:
        lines.append(f"- **Est. annual value:** {annual_value}")
    lines.append("")

    if entity_signals:
        lines.append(f"## Trigger Signals ({len(entity_signals)} active)")
        for s in entity_signals[:8]:
            sig_type = s.get("type", "signal").replace("_", " ").title()
            src = s.get("source", "")
            ew = s.get("effective_weight", s.get("weight", "?"))
            strength = s.get("strength", "?")
            ts = s.get("timestamp", "")[:10]
            data = s.get("data", {})
            detail = data.get("title", data.get("competitor", data.get("company", "")))
            lines.append(f"- **{sig_type}** (weight: {ew}, strength: {strength}) — {src} — {ts}")
            if detail:
                lines.append(f"  {detail[:100]}")
        lines.append("")

    if competitor:
        lines.append(f"## Supplier Vulnerability: {supplier}")
        tp = competitor.get("trustpilot_rating")
        if tp:
            lines.append(f"- **Trustpilot:** {tp}/5" + (" ⚠️ BELOW AVERAGE" if tp < 4.0 else ""))
        if competitor.get("hiring"):
            lines.append(f"- **Hiring:** Active (may indicate churn or scaling issues)")
        vuln = competitor.get("vulnerability_score", 0)
        if vuln:
            lines.append(f"- **Vulnerability score:** {vuln}")
        lines.append("")

    if switching_triggers:
        lines.append(f"## Known Switching Triggers")
        for t in switching_triggers:
            lines.append(f"- {t}")
        lines.append("")

    lines.append(f"## Recommended Angle")
    if supplier and competitor and competitor.get("trustpilot_rating", 5) < 4.0:
        lines.append(f"**Supplier displacement wedge.** {supplier} has below-average reviews ({competitor.get('trustpilot_rating')}/5). Lead with quality consistency, batch reliability, and COA transparency. Offer validation kit.")
    elif switching_triggers:
        lines.append(f"**Trigger-based outreach.** {len(switching_triggers)} switching triggers identified. Lead with specific pain point resolution.")
    else:
        lines.append(f"**Value proposition.** Lead with CDT pricing advantage (25-100x vs botanical), R&D kit offer, and 2-week validation plan.")

    (bundle_dir / "01_why_now.md").write_text("\n".join(lines), encoding="utf-8")

    # ══════════════════════════════════════════════
    # 02 — ACCOUNT BRIEF DOCX
    # ══════════════════════════════════════════════
    docx_found = False
    # Search for existing brief
    for search_dir in [OUTPUT_DIR, WR_OUTPUT, SCRIPT_DIR / "outputs"]:
        for pattern in [f"*{safe_name}*brief*.docx", "*mellow*brief*.docx", "mellow_fellow_brief.docx"]:
            matches = list(search_dir.glob(pattern))
            if matches:
                shutil.copy2(matches[0], bundle_dir / "02_account_brief.docx")
                docx_found = True
                break
        if docx_found:
            break

    # Also check briefs subdirectory
    if not docx_found:
        briefs_dir = OUTPUT_DIR / "briefs"
        if briefs_dir.exists():
            for f in briefs_dir.glob("*.docx"):
                if safe_name in f.name.lower() or "mellow" in f.name.lower():
                    shutil.copy2(f, bundle_dir / "02_account_brief.docx")
                    docx_found = True
                    break

    if not docx_found:
        (bundle_dir / "02_NOTE_no_brief.txt").write_text(
            f"No DOCX brief found for {company_name}.\n"
            f"Generate one: python3 sales_intel_brief_v4.py --company \"{company_name}\" --domain {domain}\n"
            f"Then convert: python3 brief_to_docx.py --brief outputs/briefs/brief_*.json",
            encoding="utf-8"
        )

    # ══════════════════════════════════════════════
    # 03 — COMPETITOR WEDGE
    # ══════════════════════════════════════════════
    wedge = []
    wedge.append(f"# Competitor Wedge: {company_name}")
    wedge.append(f"*Displacement strategy for Terpene Belt Farms / Duty Free Terpenes*\n")
    wedge.append(f"---\n")

    if supplier and competitor:
        tp = competitor.get("trustpilot_rating")
        wedge.append(f"## Current Supplier: {supplier}")
        if tp:
            wedge.append(f"- Trustpilot: **{tp}/5**" + (" — VULNERABILITY" if tp < 4.0 else ""))
        if competitor.get("hiring"):
            wedge.append(f"- Active hiring — potential growing pains")
        wedge.append("")

        wedge.append(f"## TBF/DFT Advantages vs {supplier}")
        wedge.append(f"- **Consistency:** Single-source CDT with batch-to-batch COA documentation")
        wedge.append(f"- **Pricing:** CDT at $5K-8K/L vs botanical at $45-80/L — but vertically integrated at $1.5-3K/L")
        wedge.append(f"- **Speed:** 2-week validation program with matched sensory profiles")
        wedge.append(f"- **Documentation:** Full COAs, terpene profiles, GRAS-trajectory compliance docs")
        wedge.append("")

        wedge.append(f"## 2-Week Switch Plan")
        wedge.append(f"1. **Day 1-3:** Send R&D validation kit (3-5 CDT profiles matching their current SKUs)")
        wedge.append(f"2. **Day 4-7:** Side-by-side sensory evaluation with their formulation team")
        wedge.append(f"3. **Day 8-10:** Cost/lead-time comparison + consistency documentation review")
        wedge.append(f"4. **Day 11-14:** Small-batch pilot run (1-2 SKUs) with full QC documentation")
    else:
        wedge.append(f"## Discovery Approach")
        wedge.append(f"- Identify current terpene/flavor supplier")
        wedge.append(f"- Offer side-by-side R&D kit and validation plan")
        wedge.append(f"- Lead with consistency, lead times, and documentation advantages")

    (bundle_dir / "03_competitor_wedge.md").write_text("\n".join(wedge), encoding="utf-8")

    # ══════════════════════════════════════════════
    # 04 — EMAIL
    # ══════════════════════════════════════════════
    email_lines = []
    if supplier and competitor and competitor.get("trustpilot_rating", 5) < 4.0:
        # Supplier displacement angle
        email_lines.append(f"Subject: Quick question about terpene consistency at {company_name}\n")
        email_lines.append(f"Hi {contact},\n")
        email_lines.append(f"I've been tracking the terpene supplier landscape for brands like {company_name}, and a few signals came across our system that usually show up right before teams re-evaluate their formulation stack.\n")
        email_lines.append(f"Rather than pitch you, I'd rather make this easy: we can send a small R&D kit (3-5 CDT profiles matched to your current direction) plus a 2-week validation plan so your team can compare:")
        email_lines.append(f"- Sensory consistency batch-to-batch")
        email_lines.append(f"- Lead times and supply reliability")
        email_lines.append(f"- Documentation readiness (COAs, specs, compliance)\n")
        email_lines.append(f"Worth a 10-minute call this week to see if it's relevant?\n")
        email_lines.append(f"Best,\nShareef – Terpene Belt Farms")
    else:
        # Generic value prop
        email_lines.append(f"Subject: R&D kit for {company_name} — terpene/flavor validation\n")
        email_lines.append(f"Hi {contact},\n")
        email_lines.append(f"We work with brands like {company_name} on terpene formulation — specifically helping teams validate consistency, reduce supplier risk, and optimize their flavor/effects profiles.\n")
        email_lines.append(f"If you're open to it, we can send a small R&D kit tailored to your product line, plus a 2-week validation plan your team can run alongside your current setup.\n")
        email_lines.append(f"Would a quick 10-minute call make sense this week?\n")
        email_lines.append(f"Best,\nShareef – Terpene Belt Farms")

    (bundle_dir / "04_email.txt").write_text("\n".join(email_lines), encoding="utf-8")

    # ══════════════════════════════════════════════
    # 05 — LINKEDIN DM
    # ══════════════════════════════════════════════
    dm = f"""Hey {contact} — I put together a quick account brief on {company_name} and noticed a few signals that usually come up right before brands re-check their terpene/flavor supply chain.

We can send a small R&D kit matched to your current product direction + a 2-week validation plan. No commitment — just a side-by-side comparison.

Want me to share the 1-pager?"""

    (bundle_dir / "05_linkedin_dm.txt").write_text(dm, encoding="utf-8")

    # ══════════════════════════════════════════════
    # 06 — CALL OPENER
    # ══════════════════════════════════════════════
    call = f"""CALL SCRIPT: {company_name}
Contact: {contact}{f' — {title}' if title else ''}

[OPENER]
"Hey {contact} — Shareef from Terpene Belt Farms. Quick one.

We track terpene supply signals across brands in your space, and when we see a couple of these triggers together, teams usually start re-checking consistency, lead times, and pricing.

I'm not trying to sell you on anything — but if I send a small R&D kit plus a 2-week validation plan, would you be the right person to run a side-by-side comparison?"

[IF INTERESTED]
"Great. I'll have our lab team put together 3-5 CDT profiles matched to your current product line. You'll get full COAs, sensory notes, and a validation checklist. Takes about 2 weeks, zero commitment."

[OBJECTION: We're happy with our current supplier]
"Totally get that. Most of our partners said the same thing — this isn't about replacing anyone. It's about having a documented comparison on file so if consistency, pricing, or lead times ever become an issue, you already have a validated alternative ready to go."

[CLOSE]
"Can I get the best shipping address for that R&D kit?" """

    (bundle_dir / "06_call_opener.txt").write_text(call, encoding="utf-8")

    # ══════════════════════════════════════════════
    # 07 — HEYGEN SCRIPT
    # ══════════════════════════════════════════════
    heygen = f"""[HEYGEN VIDEO SCRIPT — 45 seconds]
[Avatar: Shareef, professional setting]

Hey {contact} — Shareef here from Terpene Belt Farms.

I'm reaching out because our market intelligence system flagged {company_name} as a brand that might benefit from validating their terpene supply chain.

Rather than pitch you, here's what I'd like to do: send a small R&D kit — 3 to 5 CDT profiles matched to your current product direction — plus a 2-week validation plan your team can run side-by-side with what you're using now.

Full COAs, sensory notes, consistency documentation — everything you'd need to make a comparison.

If that's useful, hit reply and I'll get it shipped out this week.

Talk soon.

[END — CTA: Reply to this email]"""

    (bundle_dir / "07_heygen_script.txt").write_text(heygen, encoding="utf-8")

    # ══════════════════════════════════════════════
    # 08 — TASK PAYLOAD (GHL-ready)
    # ══════════════════════════════════════════════
    task_payload = {
        "company_key": company_key,
        "company_name": company_name,
        "contact": contact,
        "title": title,
        "domain": domain,
        "playbook": "supplier_displacement" if supplier else "value_proposition",
        "actions": [
            {"step": 1, "type": "send_email", "asset": "04_email.txt", "day": 0},
            {"step": 2, "type": "send_linkedin_dm", "asset": "05_linkedin_dm.txt", "day": 1},
            {"step": 3, "type": "send_heygen_video", "asset": "07_heygen_script.txt", "day": 3},
            {"step": 4, "type": "call", "asset": "06_call_opener.txt", "day": 5},
            {"step": 5, "type": "follow_up_email", "asset": "04_email.txt", "day": 7, "note": "Modify subject to follow-up"},
        ],
        "generated_at": now.isoformat() + "Z",
        "dry_run": dry_run,
        "nexus_score": score,
        "pipeline_tier": tier,
    }
    (bundle_dir / "08_task_payload.json").write_text(json.dumps(task_payload, indent=2), encoding="utf-8")

    # ══════════════════════════════════════════════
    # 09 — ATTRIBUTION (War Room action log)
    # ══════════════════════════════════════════════

    # Log action in War Room with proper attribution
    action_id = f"ks_{stamp}"
    try:
        if hasattr(graph, 'create_action'):
            action_id = graph.create_action(
                action_type="kill_shot_bundle",
                target_entity=company_key,
                action_data={
                    "company": company_name,
                    "bundle_path": str(bundle_dir),
                    "signals_used": len(trigger_signal_ids),
                    "angle": "supplier_displacement" if supplier else "value_proposition",
                },
                trigger_signal_ids=trigger_signal_ids,
                top_features=[f"score:{score}", f"tier:{tier}", f"supplier:{supplier}" if supplier else "no_supplier"],
            )
        elif hasattr(graph, 'record_action'):
            action_id = graph.record_action(
                "kill_shot_bundle",
                company_key,
                {"company": company_name, "signals_used": len(trigger_signal_ids)},
            )
        graph.save()
    except Exception as e:
        print(f"  ⚠️  War Room attribution error (bundle still created): {e}")

    attribution = {
        "run_id": stamp,
        "action_id": action_id,
        "war_room_version": WR_VERSION,
        "company_key": company_key,
        "company_name": company_name,
        "trigger_signal_ids": trigger_signal_ids,
        "bundle_path": str(bundle_dir),
        "generated_at": now.isoformat() + "Z",
    }
    (bundle_dir / "09_attribution.json").write_text(json.dumps(attribution, indent=2), encoding="utf-8")

    return bundle_dir, action_id, trigger_signal_ids


def main():
    parser = argparse.ArgumentParser(description="Kill Shot Bundle — one-command outreach package")
    parser.add_argument("--company", required=True, help='Company name or domain')
    parser.add_argument("--dry-run", action="store_true", help="Don't push to GHL")
    args = parser.parse_args()

    print(f"\n{'═'*60}")
    print(f"  KILL SHOT BUNDLE GENERATOR")
    print(f"  War Room: {WR_VERSION}")
    print(f"{'═'*60}\n")

    if not KnowledgeGraph:
        print("  ⚠️  War Room not available. Cannot generate bundle without knowledge graph.")
        print("  Make sure war_room.py is in the same directory.")
        sys.exit(1)

    graph = KnowledgeGraph()
    company_key, company = find_company(graph, args.company)

    print(f"  Target: {company.get('name', '?')}")
    print(f"  Domain: {company.get('domain', '?')}")
    print(f"  Score: {company.get('avg_score', 0)} | Tier: {company.get('pipeline_tier', '?')}")
    print(f"  Contact: {company.get('top_contact', '?')}")
    print(f"  Supplier: {company.get('current_supplier', 'Unknown')}")
    print()

    bundle_dir, action_id, trigger_ids = build_bundle(graph, company_key, company, args.dry_run)

    print(f"\n{'─'*60}")
    print(f"  ✅ BUNDLE CREATED: {bundle_dir}/")
    print(f"  ✅ War Room action: {action_id}")
    print(f"  ✅ Attribution: {len(trigger_ids)} trigger signals linked")
    print(f"{'─'*60}")

    # List bundle contents
    print(f"\n  Bundle contents:")
    for f in sorted(bundle_dir.iterdir()):
        size = f.stat().st_size
        print(f"    {f.name} ({size:,} bytes)")

    print(f"\n  ══ DEMO THE LEARNING LOOP ══")
    print(f"  python3 war_room_v2.py learn --action-id {action_id} --outcome meeting")
    print(f"  python3 war_room_v2.py status")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()
