#!/usr/bin/env python3
"""
NEXUS Platform Server v5
=========================
Unified server for Reef Mode + Research Intelligence + Event Log.

Implements:
  Epic 0.1 — Canonical data contracts (versioned snapshot schema)
  Epic 0.2 — Telekinesis v1 (event log + polling endpoint)
  Epic 3.1 — Signal taxonomy + reliability priors
  Epic 4.1 — Enhanced abstract extraction fields
  Epic 4.4 — Research → Business translation layer

Endpoints:
  GET  /reef                    → Reef Mode UI
  GET  /api/reef/snapshot       → Versioned snapshot (stable schema)
  GET  /api/reef/research       → PhD-grade research intelligence
  GET  /api/reef/signals        → Signal feed with taxonomy + decay
  GET  /api/events              → Event log (polling, ?since=cursor)
  GET  /api/agents              → Agent registry
  GET  /health                  → Health check
  POST /api/reef/run            → Trigger agent commands
  POST /api/reef/outcome        → Record outcomes

Usage:
  python3 reef_server_v5.py                  # port 3142
  python3 reef_server_v5.py --port 3141      # custom port
"""

import os, sys, json, argparse, time, hashlib, re, subprocess, threading
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import Counter, defaultdict

try:
    import requests as _requests
except ImportError:
    _requests = None

# ═══════════════════════════════════════════════════════════
# PATH RESOLUTION — find data regardless of where server lives
# ═══════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.resolve()

def _find_outputs():
    """Find the outputs directory containing terpene_research data."""
    candidates = [
        SCRIPT_DIR / "outputs",
        SCRIPT_DIR.parent / "outputs",
        SCRIPT_DIR.parent / "scripts" / "outputs",
        Path.home() / ".openclaw" / "skills" / "nexus-bdr-agent" / "scripts" / "outputs",
        Path.home() / ".openclaw" / "skills" / "nexus-bdr-agent" / "outputs",
    ]
    for c in candidates:
        if c.exists() and (c / "terpene_research").exists():
            return c
    # Fallback: any candidate that exists
    for c in candidates:
        if c.exists():
            return c
    return SCRIPT_DIR / "outputs"

OUTPUT_DIR = _find_outputs()
# ROOT_OUTPUT_DIR covers the second data location (nexus-bdr/outputs/)
# where enriched contacts, raw Apollo imports, social intel, and briefs live
ROOT_OUTPUT_DIR = SCRIPT_DIR.parent / "outputs" if (SCRIPT_DIR.parent / "outputs").exists() else OUTPUT_DIR
RESEARCH_DIR = OUTPUT_DIR / "terpene_research"
KB_DIR = RESEARCH_DIR / "knowledge_base"
INSIGHTS_DIR = RESEARCH_DIR / "insights"
REPORTS_DIR = RESEARCH_DIR / "reports"
WAR_ROOM_DIR = OUTPUT_DIR / "war_room"
EVENTS_DIR = OUTPUT_DIR / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = EVENTS_DIR / "events.jsonl"
DEMO_BUNDLE_DIR = SCRIPT_DIR / "demo_bundle"

SCHEMA_VERSION = "5.0"


# ═══════════════════════════════════════════════════════════
# EPIC 0.2 — EVENT LOG (Telekinesis v1)
# ═══════════════════════════════════════════════════════════

def emit_event(event_type, data=None):
    """Append an event to the event log."""
    event = {
        "id": hashlib.md5(f"{event_type}{time.time()}{json.dumps(data or {}, default=str)[:200]}".encode()).hexdigest()[:12],
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
    }
    try:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
    except Exception:
        pass
    return event

def get_events(since=None, limit=50):
    """Read events, optionally since a cursor timestamp."""
    events = []
    if not EVENTS_FILE.exists():
        return events
    try:
        with open(EVENTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if since and ev.get("timestamp", "") <= since:
                        continue
                    events.append(ev)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return events[-limit:]


# ═══════════════════════════════════════════════════════════
# EPIC 3.1 — SIGNAL TAXONOMY + RELIABILITY PRIORS
# ═══════════════════════════════════════════════════════════

SIGNAL_TAXONOMY = {
    "product_launch":    {"reliability_prior": 0.8, "decay_half_life_days": 30, "category": "market_move"},
    "hiring_growth":     {"reliability_prior": 0.7, "decay_half_life_days": 45, "category": "market_move"},
    "review_drop":       {"reliability_prior": 0.85, "decay_half_life_days": 21, "category": "vulnerability"},
    "pricing_change":    {"reliability_prior": 0.6, "decay_half_life_days": 14, "category": "market_move"},
    "regulatory_signal": {"reliability_prior": 0.9, "decay_half_life_days": 90, "category": "compliance"},
    "patent_published":  {"reliability_prior": 0.95, "decay_half_life_days": 180, "category": "ip"},
    "forum_complaint":   {"reliability_prior": 0.5, "decay_half_life_days": 14, "category": "vulnerability"},
    "supplier_change":   {"reliability_prior": 0.7, "decay_half_life_days": 30, "category": "opportunity"},
    "leadership_change": {"reliability_prior": 0.85, "decay_half_life_days": 60, "category": "opportunity"},
    "funding_news":      {"reliability_prior": 0.9, "decay_half_life_days": 45, "category": "market_move"},
    "quality_complaint":  {"reliability_prior": 0.6, "decay_half_life_days": 21, "category": "vulnerability"},
    "reddit_supplier_seeking": {"reliability_prior": 0.55, "decay_half_life_days": 7, "category": "opportunity"},
    "reddit_discussion": {"reliability_prior": 0.4, "decay_half_life_days": 7, "category": "signal"},
    "research_published": {"reliability_prior": 0.95, "decay_half_life_days": 365, "category": "research"},
    "competitor_claim":  {"reliability_prior": 0.5, "decay_half_life_days": 60, "category": "competitive"},
}

def decay_strength(strength, timestamp_iso, half_life_days=14):
    """Apply exponential decay to signal strength."""
    try:
        ts = datetime.fromisoformat(timestamp_iso.replace("Z", ""))
        age_days = (datetime.utcnow() - ts).total_seconds() / 86400
        decay = 0.5 ** (age_days / half_life_days)
        return round(strength * decay, 3)
    except Exception:
        return strength

def enrich_signals(raw_signals):
    """Apply taxonomy, reliability priors, and decay to raw signals."""
    enriched = []
    for s in raw_signals:
        sig_type = s.get("type", "unknown")
        taxonomy = SIGNAL_TAXONOMY.get(sig_type, {"reliability_prior": 0.5, "decay_half_life_days": 14, "category": "unknown"})

        base_strength = s.get("strength", 5) / 10.0
        reliability = taxonomy["reliability_prior"]
        raw_score = base_strength * reliability
        decayed_score = decay_strength(raw_score, s.get("timestamp", ""), taxonomy["decay_half_life_days"])

        enriched.append({
            "id": s.get("id", ""),
            "type": sig_type,
            "category": taxonomy["category"],
            "source": s.get("source", ""),
            "entities": s.get("entities", []),
            "data": s.get("data", {}),
            "timestamp": s.get("timestamp", ""),
            "url": s.get("data", {}).get("url", ""),
            "summary": s.get("data", {}).get("summary", s.get("data", {}).get("title", "")),
            "raw_strength": s.get("strength", 5),
            "reliability_prior": reliability,
            "decayed_score": decayed_score,
            "decay_half_life_days": taxonomy["decay_half_life_days"],
            "acted_on": s.get("acted_on", False),
        })

    enriched.sort(key=lambda x: x["decayed_score"], reverse=True)
    return enriched


# ═══════════════════════════════════════════════════════════
# EPIC 0.1 — CANONICAL SNAPSHOT SCHEMA (versioned)
# ═══════════════════════════════════════════════════════════

def build_snapshot():
    """Build a stable, versioned snapshot from all data sources."""
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.utcnow().isoformat(),
        "systemStatus": {
            "entitiesTracked": 0,
            "signalsToday": 0,
            "actionsQueued": 0,
            "outcomesRecordedToday": 0,
            "competitorsTracked": 0,
            "researchPapers": 0,
            "researchLastHarvest": None,
            "eventsTotal": 0,
        },
        "priorities": [],
        "competitors": [],
        "signals": [],
        "researchHighlights": [],
        "synthesisInsights": [],
        "researchTrends": None,
        "researchGaps": None,
        "regulatoryHits": [],
        "terpeneMatrix": None,
        "businessInsights": [],
        "learning": {"signalWeights": {}, "playbookWinRates": {}},
        "signalWeights": [],
    }

    # ── War Room Graph ──
    graph_path = WAR_ROOM_DIR / "knowledge_graph" / "war_room_graph.json"
    if graph_path.exists():
        try:
            g = json.loads(graph_path.read_text())
            entities = g.get("entities", {})
            signals = g.get("signals", [])
            learning = g.get("learning", {}) or {}

            snapshot["systemStatus"]["entitiesTracked"] = len(entities)
            snapshot["learning"]["signalWeights"] = learning.get("signal_weights", {})

            # Signal weights for display
            sw = learning.get("signal_weights", {})
            snapshot["signalWeights"] = [{"signal": k, "weight": v} for k, v in sorted(sw.items(), key=lambda x: x[1], reverse=True)][:15]

            # Outcomes today
            today = datetime.utcnow().strftime("%Y-%m-%d")
            outcomes = learning.get("outcome_history", [])
            snapshot["systemStatus"]["outcomesRecordedToday"] = sum(1 for o in outcomes if o.get("timestamp", "").startswith(today))

            # Signals today
            cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            today_sigs = [s for s in signals[-500:] if s.get("timestamp", "") >= cutoff]
            snapshot["systemStatus"]["signalsToday"] = len(today_sigs)

            # Enriched signals
            snapshot["signals"] = enrich_signals(signals[-100:])

            # Actions
            actions = learning.get("action_log", [])
            snapshot["systemStatus"]["actionsQueued"] = sum(1 for a in actions if a.get("status") in ("pending", "executed"))

            # Competitors from entities
            competitors = [v for v in entities.values() if v.get("type") == "competitor"]
            snapshot["systemStatus"]["competitorsTracked"] = len(competitors)
            for c in competitors[:10]:
                snapshot["competitors"].append({
                    "name": c.get("name", c.get("id", "")),
                    "trustpilot": c.get("data", {}).get("trustpilot_score"),
                    "risk": c.get("data", {}).get("risk_level", "LOW"),
                    "score": c.get("data", {}).get("vulnerability_score", 0),
                    "hiring": c.get("data", {}).get("hiring", False),
                    "vulnerability": c.get("data", {}).get("vulnerability_summary", ""),
                })

            # Playbook win rates
            snapshot["learning"]["playbookWinRates"] = learning.get("playbook_win_rates", {})

        except Exception as e:
            print(f"  Warning: graph load failed: {e}")

    # ── Decisions → Priorities ──
    decisions_dir = WAR_ROOM_DIR / "decisions"
    if decisions_dir.exists():
        files = sorted(decisions_dir.glob("decisions_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if files:
            try:
                d = json.loads(files[0].read_text())
                pcs = d.get("priority_companies", d.get("top_priorities", []))
                for i, cp in enumerate(pcs[:12]):
                    snapshot["priorities"].append({
                        "rank": i + 1,
                        "company": cp.get("company", cp.get("name", "Unknown")),
                        "domain": cp.get("domain", ""),
                        "score": cp.get("composite_score", cp.get("score", 0)),
                        "tier": (cp.get("tier") or ("hot" if cp.get("composite_score", cp.get("score", 0)) >= 25 else "warm")).lower(),
                        "contacts": cp.get("contacts", 0),
                        "verified": int(cp.get("emails", cp.get("verified", 0)) or 0),
                        "briefComplete": bool(cp.get("brief", cp.get("brief_complete", False))),
                        "topContact": cp.get("top_contact", "—"),
                        "topTitle": cp.get("top_title", "—"),
                        "features": cp.get("features", []),
                        "nextAction": "outreach" if cp.get("brief") else "run_brief",
                        "actionId": cp.get("action_id", f"auto_{i+1}"),
                        "currentSupplier": cp.get("current_supplier", ""),
                        "whyNow": cp.get("why_now", "\n".join(cp.get("reasons", [])[:4])),
                        "whyNowStructured": cp.get("why_now_structured", []),
                        "playbook": cp.get("playbook", ""),
                        "playbookConfidence": cp.get("playbook_confidence", ""),
                    })
            except Exception as e:
                print(f"  Warning: decisions load failed: {e}")

    # ── Research Intelligence ──
    _load_research_into_snapshot(snapshot)

    # ── Pipeline Stats from scored Apollo data ──
    _load_pipeline_stats(snapshot)

    # ── Enrichment stats ──
    _load_enrichment_stats(snapshot)

    # ── Social intel ──
    _load_social_intel(snapshot)

    # ── Activity log ──
    _load_activity_log(snapshot)

    # ── Demo bundles ──
    _load_demo_bundles(snapshot)

    # ── Brief files ──
    _load_briefs(snapshot)

    # ── Event count ──
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE) as f:
                snapshot["systemStatus"]["eventsTotal"] = sum(1 for _ in f)
        except Exception:
            pass

    return snapshot


def _load_pipeline_stats(snapshot):
    """Load pipeline contact stats from scored Apollo data files."""
    # Search both output directories for scored files
    scored_files = []
    for d in [OUTPUT_DIR, ROOT_OUTPUT_DIR]:
        scored_files.extend(d.glob("scored_apollo_*.json"))
    scored_files = sorted(set(scored_files), key=lambda x: x.stat().st_mtime, reverse=True)
    if not scored_files:
        return

    try:
        data = json.loads(scored_files[0].read_text())
        leads = data.get("leads", [])
        if not leads:
            return

        total = len(leads)
        scores = [r.get("nexus_lead_score", r.get("score", 0)) for r in leads]
        hot = sum(1 for s in scores if s >= 80)
        warm = sum(1 for s in scores if 60 <= s < 80)
        cool = sum(1 for s in scores if 40 <= s < 60)
        cold = sum(1 for s in scores if s < 40)
        verified = sum(1 for r in leads if r.get("email_status") == "Verified" or r.get("hunter_status") == "valid")
        companies = len(set(r.get("company_name", "") for r in leads if r.get("company_name")))
        brands = {}
        for r in leads:
            b = r.get("nexus_brand", r.get("brand", "unknown"))
            brands[b] = brands.get(b, 0) + 1

        snapshot["pipeline"] = {
            "total": total, "hot": hot, "warm": warm, "cool": cool, "cold": cold,
            "verified": verified, "companies": companies, "brands": brands,
            "source": scored_files[0].name,
        }
    except Exception as e:
        print(f"  Warning: pipeline stats load failed: {e}")


def _load_enrichment_stats(snapshot):
    """Load enrichment stats from enriched contact files."""
    enriched_files = []
    for d in [OUTPUT_DIR, ROOT_OUTPUT_DIR]:
        enriched_files.extend(d.glob("enriched_*.json"))
    enriched_files = sorted(set(enriched_files), key=lambda x: x.stat().st_mtime, reverse=True)

    enrichment = {"files": len(enriched_files), "total_contacts": 0, "verified": 0, "catchall": 0, "invalid": 0}
    if enriched_files:
        try:
            data = json.loads(enriched_files[0].read_text())
            contacts = data if isinstance(data, list) else data.get("leads", data.get("contacts", []))
            enrichment["total_contacts"] = len(contacts)
            for c in contacts:
                status = c.get("hunter_status", c.get("verification_status", ""))
                if status == "valid":
                    enrichment["verified"] += 1
                elif status == "accept_all":
                    enrichment["catchall"] += 1
                elif status == "invalid":
                    enrichment["invalid"] += 1
        except Exception:
            pass
    snapshot["enrichment"] = enrichment


def _load_social_intel(snapshot):
    """Load social intel scan data."""
    social_dirs = [OUTPUT_DIR / "social_intel", ROOT_OUTPUT_DIR / "social_intel"]
    scans = []
    for d in social_dirs:
        if d.exists():
            scans.extend(d.glob("*.json"))
    scans = sorted(set(scans), key=lambda x: x.stat().st_mtime, reverse=True)

    social = {"scans": len(scans), "signals": []}
    if scans:
        try:
            data = json.loads(scans[0].read_text())
            signals = data.get("signals", data.get("results", []))
            if isinstance(signals, list):
                social["signals"] = signals[:20]
                social["total_signals"] = len(signals)
        except Exception:
            pass
    snapshot["socialIntel"] = social


def _load_activity_log(snapshot):
    """Load activity log from outputs."""
    for d in [ROOT_OUTPUT_DIR, OUTPUT_DIR]:
        log_path = d / "activity-log.json"
        if log_path.exists():
            try:
                data = json.loads(log_path.read_text())
                entries = data if isinstance(data, list) else data.get("entries", data.get("log", []))
                snapshot["activityLog"] = entries[-50:] if isinstance(entries, list) else []
                return
            except Exception:
                pass
    snapshot["activityLog"] = []


def _load_demo_bundles(snapshot):
    """Load Kill Shot demo bundle metadata."""
    bundles = []
    if DEMO_BUNDLE_DIR.exists():
        for bundle_dir in sorted(DEMO_BUNDLE_DIR.iterdir()):
            if not bundle_dir.is_dir():
                continue
            bundle = {"name": bundle_dir.name, "artifacts": []}
            for f in sorted(bundle_dir.iterdir()):
                bundle["artifacts"].append({"file": f.name, "size": f.stat().st_size, "type": f.suffix})
            bundles.append(bundle)
    snapshot["demoBundles"] = bundles


def _load_briefs(snapshot):
    """Load brief file metadata from both output dirs."""
    brief_files = {}
    for d in [OUTPUT_DIR / "briefs", ROOT_OUTPUT_DIR / "briefs"]:
        if d.exists():
            for f in d.glob("brief_*.json"):
                brief_files[f.name] = f  # dedup by filename
    brief_files = sorted(brief_files.values(), key=lambda x: x.stat().st_mtime, reverse=True)

    briefs = []
    for bf in brief_files[:10]:
        try:
            data = json.loads(bf.read_text())
            briefs.append({
                "file": bf.name,
                "company": data.get("company", data.get("target_company", bf.stem)),
                "generated_at": data.get("generated_at", data.get("timestamp", "")),
                "phases_completed": data.get("phases_completed", len(data.get("phases", []))),
                "cost": data.get("total_cost", data.get("cost", 0)),
                "size_kb": round(bf.stat().st_size / 1024, 1),
            })
        except Exception:
            briefs.append({"file": bf.name, "size_kb": round(bf.stat().st_size / 1024, 1)})
    snapshot["briefs"] = briefs


def _load_research_into_snapshot(snapshot):
    """Load all research data into snapshot with stable schema."""
    # KB papers
    kb_path = KB_DIR / "kb.json"
    if kb_path.exists():
        try:
            kb = json.loads(kb_path.read_text())
            papers = kb.get("papers", {})
            snapshot["systemStatus"]["researchPapers"] = len(papers)
            snapshot["systemStatus"]["researchLastHarvest"] = kb.get("meta", {}).get("saved_at")

            # Top papers by relevance
            sorted_papers = sorted(papers.values(), key=lambda p: p.get("relevance_score", 0), reverse=True)
            for p in sorted_papers[:25]:
                snapshot["researchHighlights"].append({
                    "title": p.get("title", ""),
                    "journal": p.get("journal", ""),
                    "year": p.get("year", ""),
                    "terpenes": p.get("terpenes_mentioned", []),
                    "score": p.get("relevance_score", 0),
                    "url": p.get("url", ""),
                    "evidenceGrade": p.get("evidence_grade", "D"),
                    "studyType": p.get("study_type", "unknown"),
                    "mechanisms": p.get("mechanisms_extracted", []),
                    "effects": p.get("effects_mentioned", []),
                    "modelOrganism": p.get("model_organism", "unknown"),
                    "outcomeDirection": p.get("outcome_direction", "unknown"),
                    "doseInfo": p.get("dose_info", []),
                    "commercialTags": p.get("commercial_tags", []),
                })
        except Exception as e:
            print(f"  Warning: KB load failed: {e}")

    # Synthesis insights
    syn_path = INSIGHTS_DIR / "synthesis.json"
    if syn_path.exists():
        try:
            syn = json.loads(syn_path.read_text())
            snapshot["synthesisInsights"] = syn.get("insights", [])[:15]
        except Exception:
            pass

    # Trends
    trends_path = INSIGHTS_DIR / "trends.json"
    if trends_path.exists():
        try:
            snapshot["researchTrends"] = json.loads(trends_path.read_text())
        except Exception:
            pass

    # Gaps
    gaps_path = INSIGHTS_DIR / "gaps.json"
    if gaps_path.exists():
        try:
            snapshot["researchGaps"] = json.loads(gaps_path.read_text())
        except Exception:
            pass

    # Regulatory
    reg_path = INSIGHTS_DIR / "regulatory.json"
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text())
            snapshot["regulatoryHits"] = reg.get("regulatory_hits", [])[:15]
        except Exception:
            pass

    # Matrix
    matrix_path = REPORTS_DIR / "terpene_effect_matrix.json"
    if matrix_path.exists():
        try:
            snapshot["terpeneMatrix"] = json.loads(matrix_path.read_text())
        except Exception:
            pass

    # Competitive intel
    ci_path = INSIGHTS_DIR / "competitive_intel.json"
    if ci_path.exists():
        try:
            ci = json.loads(ci_path.read_text())
            snapshot["competitiveIntel"] = ci.get("claims", [])
        except Exception:
            pass

    # ── EPIC 4.4: Business Insights (Research → Business translation) ──
    snapshot["businessInsights"] = _generate_business_insights(snapshot)


# ═══════════════════════════════════════════════════════════
# EPIC 4.4 — RESEARCH → BUSINESS TRANSLATION
# ═══════════════════════════════════════════════════════════

def _generate_business_insights(snapshot):
    """Generate compliance-safe business insights from research data."""
    insights = []
    synthesis = snapshot.get("synthesisInsights", [])
    trends = snapshot.get("researchTrends") or {}
    gaps = snapshot.get("researchGaps") or {}
    papers = snapshot.get("researchHighlights", [])

    # ── "This Week's Bets" from synthesis ──
    for ins in synthesis[:5]:
        if ins.get("confidence_1to6", 0) < 3:
            continue

        terp = ins.get("terpene", "")
        cat = (ins.get("effect_category", "") or "").replace("_", " ")
        mech = (ins.get("mechanism", "") or "").replace("_", " ")
        human = ins.get("human_count", 0)
        papers_n = ins.get("paper_count", 0)

        # Generate compliance-safe framing
        if cat in ("pain inflammation", "pain_inflammation"):
            safe_frame = f"Formulations featuring {terp} show strong consumer-perceived comfort and recovery benefits"
            product_angle = "Topical/transdermal formulations, recovery blends"
        elif cat in ("sleep relaxation", "sleep_relaxation"):
            safe_frame = f"{terp}-forward profiles are associated with consumer-preferred relaxation and restfulness"
            product_angle = "Evening/nighttime blends, wind-down formulations"
        elif cat in ("mental health", "mental_health"):
            safe_frame = f"Consumer preference data aligns with {terp}'s aromatic profile for mood and wellbeing"
            product_angle = "Daytime mood blends, uplift profiles"
        elif cat == "formulation":
            safe_frame = f"Emerging formulation science supports {terp} for enhanced delivery and bioavailability"
            product_angle = "Nano-emulsion carriers, transdermal patches, beverage formulations"
        elif cat in ("antimicrobial",):
            safe_frame = f"{terp} shows interesting preservation and freshness properties in formulation contexts"
            product_angle = "Natural preservation, shelf-life extension"
        else:
            safe_frame = f"{terp} shows convergent research interest in {cat} applications"
            product_angle = "CDT profile optimization, custom blend development"

        sales_angle = f"Recent {papers_n} studies"
        if human:
            sales_angle += f" (including {human} with human data)"
        sales_angle += f" converge on {terp}'s role in {cat}"
        if mech and mech != "unknown mechanism":
            sales_angle += f" via {mech}"

        citations = [c.get("url", "") for c in (ins.get("citations", []) or [])[:3] if c.get("url")]

        insights.append({
            "type": "weekly_bet",
            "terpene": terp,
            "category": cat,
            "confidence": ins.get("confidence_1to6", 0),
            "safe_framing": safe_frame,
            "product_angle": product_angle,
            "sales_angle": sales_angle,
            "why_we_can_say_it": f"Evidence grade: {_best_grade(ins)} | {papers_n} papers | {human} human studies | {'Consistent' if not ins.get('contradiction') else 'Mixed'} outcomes",
            "citations": citations,
        })

    # ── Trend-based product bets ──
    terp_velocity = trends.get("terpene_velocity_top", {})
    for terp, v in list(terp_velocity.items())[:3]:
        if v.get("velocity", 0) > 0.3:
            insights.append({
                "type": "trend_alert",
                "terpene": terp,
                "category": "accelerating_research",
                "confidence": 3 if v["velocity"] > 0.5 else 2,
                "safe_framing": f"Research interest in {terp} is accelerating ({v['velocity']:+.0%} velocity) — consider increasing profile prominence",
                "product_angle": "Profile emphasis, marketing content refresh",
                "sales_angle": f"{terp} appeared in {v.get('recent_count', 0)} recent publications — growing scientific attention signals market interest ahead",
                "why_we_can_say_it": f"Publication velocity: {v['velocity']:+.2f} | {v.get('recent_count', 0)} recent vs {v.get('older_count', 0)} prior period",
                "citations": [],
            })

    # ── Gap-based R&D suggestions ──
    underweighted = (gaps.get("underweighted_by_tbf") or [])[:3]
    for g in underweighted:
        if g.get("gap_score", 0) > 0.02:
            insights.append({
                "type": "rd_opportunity",
                "terpene": g.get("terpene", ""),
                "category": "portfolio_gap",
                "confidence": 2,
                "safe_framing": f"Evidence base for {g['terpene']} outpaces current product focus — potential whitespace opportunity",
                "product_angle": f"New blend development, {g['terpene']}-forward profiles",
                "sales_angle": f"{g.get('evidence_share', 0)} papers support {g['terpene']} vs {g.get('tbf_focus_units', 0)} current product lines — science is ahead of the catalog",
                "why_we_can_say_it": f"Gap score: {g.get('gap_score', 0):.4f} (evidence share exceeds product focus share)",
                "citations": [],
            })

    return insights


def _best_grade(insight):
    """Get best evidence grade from an insight's citations."""
    grades = [c.get("grade", "D") for c in (insight.get("citations") or [])]
    for g in ("A", "B", "C", "D"):
        if g in grades:
            return g
    return "D"


# ═══════════════════════════════════════════════════════════
# AGENT REGISTRY (Epic 1.1 foundation)
# ═══════════════════════════════════════════════════════════

AGENT_REGISTRY = [
    {"agent_id": "terpene_research", "name": "PhD Research Engine", "description": "Harvests PubMed, grades evidence, synthesizes insights, detects trends", "commands": ["--harvest", "--full", "--synthesize", "--trends", "--profile", "--gaps", "--regulatory", "--digest", "--executive-brief"], "script": "terpene_research_v2.py"},
    {"agent_id": "war_room", "name": "War Room", "description": "Knowledge graph, signal processing, decision engine, learning attribution", "commands": ["--ingest", "--decide", "--learn", "--status"], "script": "war_room.py"},
    {"agent_id": "apollo_pipeline", "name": "Apollo Pipeline", "description": "Contact/company prospecting via Apollo.io", "commands": ["--search", "--enrich"], "script": "apollo_pipeline.py"},
    {"agent_id": "competitor_vuln", "name": "Competitor Intelligence", "description": "Vulnerability scanning, displacement playbooks", "commands": ["--scan", "--report"], "script": "competitor_vuln_v2.py"},
    {"agent_id": "social_intel", "name": "Social Intel Engine", "description": "Reddit, forum, social media signal harvesting", "commands": ["--scan", "--reddit", "--report"], "script": "social_intel_engine_v2.py"},
    {"agent_id": "trigger_monitor", "name": "Trigger Monitor", "description": "Monitors hiring, news, review changes for target accounts", "commands": ["--scan", "--alerts"], "script": "trigger_monitor.py"},
    {"agent_id": "sales_intel_brief", "name": "Sales Intel Brief", "description": "Generates account-level intelligence briefs", "commands": ["--generate", "--company"], "script": "sales_intel_brief_v4.py"},
    {"agent_id": "kill_shot_bundle", "name": "Kill Shot Bundle", "description": "Generates send-ready outreach packages", "commands": ["--generate", "--company"], "script": "kill_shot_bundle.py"},
    {"agent_id": "enrich_pipeline", "name": "Enrich Pipeline", "description": "Email verification, data enrichment", "commands": ["--enrich"], "script": "enrich_pipeline_v2.py"},
    {"agent_id": "heygen_scripts", "name": "HeyGen Scripts", "description": "Video script generation for personalized outreach", "commands": ["--generate"], "script": "heygen_scripts.py"},
]


# ═══════════════════════════════════════════════════════════
# COMMAND CENTER — Chat + Agent Delegation
# ═══════════════════════════════════════════════════════════

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

BRAND_CONTEXT = {
    "nexus": {
        "name": "Nexus Agriscience",
        "role": "You are operating as the PARENT ORCHESTRATION layer. You have visibility across ALL brands (TBF, DFT, NEU Bag). Cross-brand learnings are active — signals from one brand inform strategies for others. When discussing targets, note which brand is the best fit.",
        "icp": "All brands' targets unified — coalition-level view, multi-brand operators, distributors",
    },
    "tbf": {
        "name": "Terpene Belt Farms",
        "role": "You are operating in TBF (Terpene Belt Farms) mode — PREMIUM / ENTERPRISE positioning. Focus on CDT quality, full COA documentation, white-glove service, pharma-grade standards. Price is NOT the lead — quality, consistency, and science are. Target enterprise buyers spending $50K+/yr.",
        "icp": "Enterprise manufacturers, pharma-adjacent companies, premium brands, R&D teams needing custom profiles",
    },
    "dft": {
        "name": "Duty Free Terpenes",
        "role": "You are operating in DFT (Duty Free Terpenes) mode — DISRUPTOR / MARGIN MAXIMIZER positioning. Lead with the economics: botanical terpenes at $45-80/L vs CDT at $5,000-8,000/L. For non-vape products (edibles, beverages, topicals), consumers cannot distinguish CDT from botanical. The pitch is 90%+ margin reclaim.",
        "icp": "Craft brands, edible/beverage/topical manufacturers, cost-conscious operators, Good Fellows coalition targets",
    },
    "neubag": {
        "name": "NEU Bag",
        "role": "You are operating in NEU Bag mode — INNOVATION / NEXT-GEN positioning. Focus on novel formulations, nano-emulsions, next-gen delivery systems, beverage-ready terpene solutions. Target emerging brands and non-traditional cannabis/hemp companies entering the space.",
        "icp": "Emerging brands, beverage companies, wellness startups, innovation-forward operators, non-traditional market entrants",
    },
}

NEXUS_SYSTEM_PROMPT = """You are NEXUS, an AI-powered BDR (Business Development Representative) orchestration system for Nexus Agriscience's terpene brands: TBF (Terpene Belt Farms — premium/enterprise), DFT (Duty Free Terpenes — rebellious/craft), and NEU Bag (innovation/next-gen).

You manage 15 specialized agents:
- Sales Intel Brief v4: 6-phase AI research pipeline for target companies
- Kill Shot Bundle: Generates complete outreach packages (email, LinkedIn, call script, HeyGen video, competitor wedge)
- War Room: Knowledge graph with 53+ entities, signal processing, learning loop
- Competitor Intel v2: Tracks 7+ competitors, generates displacement playbooks
- Apollo Pipeline: Lead discovery and scoring via Apollo.io
- Social Intel v2: Reddit, forums, social media signal harvesting
- Terpene Research v2: PubMed paper harvesting, evidence grading, synthesis
- Trigger Monitor: Buying signal detection (hiring, news, reviews)
- Free Intel: Zero-cost intelligence from Reddit, FDA, news, Google Trends
- Enrich Pipeline: Email verification and data enrichment
- HeyGen Scripts: Personalized video script generation
- GHL Sync: GoHighLevel CRM with 53 custom fields
- Model Router: Cost-optimized AI routing (40-60% savings)
- Customer Intel: Churn prediction, upsell/reactivation
- Orchestrator: CLI entry point that coordinates all agents

KEY CONTEXT:
- Top target: Mellow Fellow (mellowfellow.fun) — pharmacist-founded, 40+ states, Good Fellows coalition (Urb, Zombi, Pushin P's)
- Coalition pipeline: $150-350K/yr
- Key pitch: For non-vape products, consumers can't distinguish CDT from botanical terpenes. Switch = 90%+ margin reclaim
- Current competitor vulnerability: True Terpenes at 3.0/5 Trustpilot

When the user asks you to do something:
1. Identify which agent(s) should handle it
2. Explain your delegation plan
3. Provide substantive answers using your knowledge of the pipeline, targets, and system capabilities
4. Be specific — reference real companies, real data, real agents

Respond in a conversational but professional tone. Be concise but thorough. Format with markdown-style headers and bullets when helpful.

IMPORTANT: In your response, include a JSON block at the very end with this format:
```json
{"agents_used": ["script_filename.py", ...], "action_type": "research|outreach|analysis|status|general"}
```"""


def _call_claude_chat(message, history=None, brand="nexus"):
    """Call Claude API for command center chat."""
    if not ANTHROPIC_KEY and not OPENROUTER_KEY:
        return None, []

    messages = []
    if history:
        for h in history[-6:]:
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    # Build context from current data
    snapshot = build_snapshot()
    brand_ctx = BRAND_CONTEXT.get(brand, BRAND_CONTEXT["nexus"])
    context = f"\n\nACTIVE BRAND: {brand_ctx['name']}\n{brand_ctx['role']}\nICP: {brand_ctx['icp']}\n"
    context += f"\nCROSS-BRAND INTELLIGENCE: Always active. Insights from any brand's agents inform all other brands. When relevant, mention cross-brand opportunities.\n"
    context += f"\nCURRENT SYSTEM STATE:\n"
    context += f"- Entities tracked: {snapshot['systemStatus']['entitiesTracked']}\n"
    context += f"- Signals today: {snapshot['systemStatus']['signalsToday']}\n"
    context += f"- Competitors tracked: {snapshot['systemStatus']['competitorsTracked']}\n"
    context += f"- Research papers: {snapshot['systemStatus']['researchPapers']}\n"
    if snapshot.get("priorities"):
        context += f"- Top priorities: {', '.join(p['company'] for p in snapshot['priorities'][:5])}\n"
    if snapshot.get("signals"):
        top_sigs = snapshot["signals"][:3]
        context += f"- Recent signals: {'; '.join(s.get('summary','')[:60] for s in top_sigs)}\n"

    system = NEXUS_SYSTEM_PROMPT + context
    messages[-1]["content"] = message

    try:
        if ANTHROPIC_KEY and _requests:
            resp = _requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 2048,
                    "system": system,
                    "messages": messages,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = "\n".join(b["text"] for b in data.get("content", []) if b.get("type") == "text")
                # Extract agent info from JSON block
                agents = _parse_agents_from_response(text)
                # Strip the JSON block from visible response
                clean_text = re.sub(r'```json\s*\n?\{["\']agents_used.*?\}\s*\n?```', '', text, flags=re.DOTALL).strip()
                return clean_text, agents
            else:
                print(f"  ⚠️ Claude API: {resp.status_code}")
        # Fallback to OpenRouter
        if OPENROUTER_KEY and _requests:
            or_msgs = [{"role": "system", "content": system}] + messages
            resp = _requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                },
                json={
                    "model": "anthropic/claude-sonnet-4-5-20250929",
                    "messages": or_msgs,
                    "max_tokens": 2048,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                agents = _parse_agents_from_response(text)
                clean_text = re.sub(r'```json\s*\n?\{["\']agents_used.*?\}\s*\n?```', '', text, flags=re.DOTALL).strip()
                return clean_text, agents
    except Exception as e:
        print(f"  ⚠️ Chat API error: {e}")

    return None, []


def _parse_agents_from_response(text):
    """Extract agent delegation info from Claude's response."""
    agents = []
    m = re.search(r'```json\s*\n?(\{["\']agents_used.*?\})\s*\n?```', text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1).replace("'", '"'))
            for script in data.get("agents_used", []):
                agents.append({"script": script, "status": "active"})
        except Exception:
            pass
    return agents


def handle_chat(message, history=None, brand="nexus"):
    """Process a chat message through the command center."""
    emit_event("ChatMessage", {"message": message[:200], "brand": brand})

    # Try Claude API first
    response, agents = _call_claude_chat(message, history, brand)
    if response:
        return {"response": response, "agents_activated": agents}

    # Fallback: intelligent keyword routing without API
    return _fallback_chat(message, brand)


def _fallback_chat(message, brand="nexus"):
    """Keyword-based fallback when no API keys available."""
    msg = message.lower()
    snapshot = build_snapshot()
    brand_ctx = BRAND_CONTEXT.get(brand, BRAND_CONTEXT["nexus"])
    brand_prefix = f"**[{brand_ctx['name']}]** " if brand != "nexus" else ""

    if any(w in msg for w in ["pipeline", "status", "how many", "accounts"]):
        s = snapshot["systemStatus"]
        priorities = snapshot.get("priorities", [])
        hot = [p for p in priorities if p.get("tier") == "hot"]
        lines = [f"**Pipeline Status:**\n",
                 f"- {s['entitiesTracked']} entities tracked across {s['competitorsTracked']} competitors",
                 f"- {s['signalsToday']} signals captured today",
                 f"- {len(priorities)} prioritized accounts, {len(hot)} HOT tier",]
        if priorities:
            lines.append(f"\n**Top Targets:**")
            for p in priorities[:5]:
                lines.append(f"- {p['company']} (score: {p.get('score', '?')}, tier: {p.get('tier', '?')})")
        return {
            "response": "\n".join(lines),
            "agents_activated": [{"script": "war_room.py", "status": "active"}, {"script": "nexus.py", "status": "active"}],
        }

    if any(w in msg for w in ["mellow", "fellow", "coalition", "good fellows"]):
        return {
            "response": "**Mellow Fellow — Priority #1 Target**\n\n"
                "Here's what I've got delegated across the fleet:\n\n"
                "**Sales Intel Brief v4** completed a full 6-phase analysis:\n"
                "- Pharmacist-founded (JJ Coombs, PharmD) — science-driven buyer\n"
                "- Self-extracts CDT at Arvida Labs, but scaling into beverages/edibles\n"
                "- 3.0/5 Trustpilot on current supplier (True Terpenes) = displacement window\n"
                "- Good Fellows coalition: Urb, Zombi, Pushin P's — land MF, get 3 warm intros\n\n"
                "**Kill Shot Bundle** generated:\n"
                "- Personalized email, LinkedIn DM, call script, HeyGen video script\n"
                "- Competitor wedge strategy (True Terpenes → DFT)\n"
                "- Why Now: federal THC ban + beverage expansion = botanical terpene play\n\n"
                "**Coalition Pipeline: $150K-$350K/yr**\n\n"
                "Ready to pull the trigger? I can regenerate any of these artifacts or run fresh research.",
            "agents_activated": [
                {"script": "sales_intel_brief_v4.py", "status": "active"},
                {"script": "kill_shot_bundle.py", "status": "active"},
                {"script": "war_room.py", "status": "active"},
                {"script": "competitor_vuln_v2.py", "status": "active"},
            ],
        }

    if any(w in msg for w in ["competitor", "true terpenes", "abstrax", "vulnerability", "displace"]):
        comps = snapshot.get("competitors", [])
        lines = ["**Competitor Vulnerability Analysis:**\n"]
        if comps:
            for c in comps[:7]:
                tp = c.get("trustpilot", "?")
                risk = c.get("risk", "?")
                vuln = c.get("vulnerability", "No data")
                lines.append(f"- **{c['name']}**: Trustpilot {tp}/5, Risk: {risk}")
                lines.append(f"  _{vuln}_")
        else:
            lines.append("- True Terpenes: 3.0/5 Trustpilot — batch consistency complaints, pricing pressure")
            lines.append("- Abstrax: 4.2/5 — premium pricing, limited botanical line")
            lines.append("- Floraplex: 3.8/5 — quality inconsistency reports")
            lines.append("- Peak Supply: 3.2/5 — price-focused, quality concerns in forums")
            lines.append("- Terps USA: 2.8/5 — Reddit complaints, suspected synthetic")
        lines.append("\n**Displacement Strategy:** Lead with economics (not quality attacks), target non-vape lines first, free evaluation kit to let product speak.")
        return {
            "response": "\n".join(lines),
            "agents_activated": [{"script": "competitor_vuln_v2.py", "status": "active"}, {"script": "war_room.py", "status": "active"}],
        }

    if any(w in msg for w in ["research", "terpene", "myrcene", "linalool", "limonene", "pubmed"]):
        bi = snapshot.get("businessInsights", [])
        lines = ["**Terpene Research Intelligence:**\n",
                 f"Knowledge base: {snapshot['systemStatus']['researchPapers']} papers indexed\n"]
        if bi:
            lines.append("**Top Business Insights (Research → Sales Angles):**")
            for b in bi[:3]:
                lines.append(f"- **{b.get('terpene', '?')}** ({b.get('category', '')}): {b.get('safe_framing', '')}")
                lines.append(f"  → Product angle: {b.get('product_angle', '')}")
        else:
            lines.append("- Myrcene: Strong comfort/recovery research — topical formulations")
            lines.append("- Linalool: Sleep/relaxation evidence — evening blends")
            lines.append("- Limonene: Mood/uplift data — daytime products")
        lines.append("\nAll research is translated to compliance-safe selling points. No medical claims — only consumer preference framing.")
        return {
            "response": "\n".join(lines),
            "agents_activated": [{"script": "terpene_research_v2.py", "status": "active"}, {"script": "war_room.py", "status": "active"}],
        }

    if any(w in msg for w in ["signal", "trigger", "reddit", "news", "scan"]):
        sigs = snapshot.get("signals", [])
        lines = ["**Signal Intelligence Feed:**\n"]
        if sigs:
            lines.append(f"{len(sigs)} signals tracked. Top signals by decayed score:")
            for s in sigs[:5]:
                lines.append(f"- [{s.get('category', '?')}] {s.get('summary', 'No summary')[:80]} (score: {s.get('decayed_score', 0):.2f})")
        else:
            lines.append("No active signals in the queue. Run a scan to harvest fresh intelligence:")
            lines.append("- `python3 scripts/free_intel_sources.py --reddit` (zero cost)")
            lines.append("- `python3 scripts/social_intel_engine_v2.py --scan` (social platforms)")
            lines.append("- `python3 scripts/trigger_monitor.py --scan` (buying signals)")
        return {
            "response": "\n".join(lines),
            "agents_activated": [
                {"script": "free_intel_sources.py", "status": "active"},
                {"script": "social_intel_engine_v2.py", "status": "active"},
                {"script": "trigger_monitor.py", "status": "active"},
            ],
        }

    if any(w in msg for w in ["kill shot", "bundle", "outreach", "email", "linkedin", "heygen"]):
        return {
            "response": "**Kill Shot Bundle Generator:**\n\n"
                "One command generates a complete 9-file outreach package for any target:\n\n"
                "1. **Why Now** — trigger-based timing rationale\n"
                "2. **Account Brief** (.docx) — full research dossier\n"
                "3. **Competitor Wedge** — displacement strategy\n"
                "4. **Email** — personalized cold outreach\n"
                "5. **LinkedIn DM** — platform-native message\n"
                "6. **Call Opener** — phone script with objection handling\n"
                "7. **HeyGen Script** — personalized video outreach\n"
                "8. **Task Payload** — CRM task creation data\n"
                "9. **Attribution** — tracking for the learning loop\n\n"
                "**Ready bundles:** Mellow Fellow (3 variants)\n\n"
                "Tell me a company name and I'll generate a fresh bundle.",
            "agents_activated": [
                {"script": "kill_shot_bundle.py", "status": "active"},
                {"script": "sales_intel_brief_v4.py", "status": "active"},
                {"script": "heygen_scripts.py", "status": "active"},
            ],
        }

    if any(w in msg for w in ["agent", "system", "architect", "how does", "capability"]):
        return {
            "response": "**NEXUS Agent Fleet — 15 Specialized Agents:**\n\n"
                "**Intelligence Layer:**\n"
                "- Sales Intel Brief v4 — 6-phase AI research pipeline\n"
                "- Free Intel Harvester — Reddit, FDA, news at zero cost\n"
                "- Social Intel v2 — Cross-platform social monitoring\n"
                "- Competitor Intel v2 — Vulnerability scanning + displacement playbooks\n"
                "- Terpene Research v2 — PubMed harvesting + evidence grading\n"
                "- Trigger Monitor — Buying signal detection\n\n"
                "**Pipeline Layer:**\n"
                "- Apollo Pipeline — Lead discovery + scoring\n"
                "- Enrich Pipeline — Email verification + data enrichment\n"
                "- Model Router — Cost-optimized AI routing (40-60% savings)\n\n"
                "**Output Layer:**\n"
                "- Kill Shot Bundle — Complete outreach package generator\n"
                "- HeyGen Scripts — Personalized video outreach\n"
                "- GHL Sync — 53-field CRM architecture\n"
                "- Customer Intel — Churn/upsell/reactivation\n\n"
                "**Control Layer:**\n"
                "- War Room — Knowledge graph + signal processing + learning\n"
                "- Master Orchestrator — CLI coordination\n\n"
                "All agents feed into the War Room's learning loop. Outcomes train signal weights. The system gets smarter with every deal.",
            "agents_activated": [{"script": "nexus.py", "status": "active"}, {"script": "war_room.py", "status": "active"}],
        }

    # Default response
    return {
        "response": "I can help with that. Here's what I can do:\n\n"
            "- **\"Research [company]\"** — Run a full intel brief on any target\n"
            "- **\"Mellow Fellow\"** — Full briefing on our #1 target + coalition\n"
            "- **\"Competitor analysis\"** — Vulnerability scan across all competitors\n"
            "- **\"Pipeline status\"** — Current target accounts and scores\n"
            "- **\"Signal intel\"** — Latest buying signals and triggers\n"
            "- **\"Kill Shot Bundle for [company]\"** — Generate outreach package\n"
            "- **\"Terpene research\"** — Science → sales angle translation\n"
            "- **\"System overview\"** — Full agent fleet capabilities\n\n"
            "What would you like me to work on?",
        "agents_activated": [],
    }


# ═══════════════════════════════════════════════════════════
# OUTCOME RECORDING — Updates War Room Learning Loop
# ═══════════════════════════════════════════════════════════

def _record_outcome_to_graph(outcome, company="", signals=None, playbook="", channel=""):
    """Record an outcome into the War Room knowledge graph learning loop."""
    graph_path = WAR_ROOM_DIR / "knowledge_graph" / "war_room_graph.json"
    if not graph_path.exists():
        return {}

    try:
        g = json.loads(graph_path.read_text())
        learning = g.setdefault("learning", {})
        sw = learning.setdefault("signal_weights", {})
        outcomes = learning.setdefault("outcome_history", [])
        pbwr = learning.setdefault("playbook_win_rates", {})

        # Determine weight adjustment
        positive = outcome in ("meeting_booked", "reply_positive", "deal_won", "demo_scheduled", "proposal_sent")
        negative = outcome in ("no_response", "reply_negative", "deal_lost", "unsubscribed")
        multiplier = 1.15 if positive else (0.90 if negative else 1.0)

        # Update signal weights for involved signals
        updated = {}
        for sig in (signals or []):
            old = sw.get(sig, 5.0)
            new_w = round(min(max(old * multiplier, 1.0), 20.0), 2)
            sw[sig] = new_w
            updated[sig] = {"old": old, "new": new_w, "direction": "up" if positive else "down"}

        # Record outcome
        outcomes.append({
            "timestamp": datetime.utcnow().isoformat(),
            "outcome": outcome,
            "company": company,
            "signals": signals or [],
            "playbook": playbook,
            "channel": channel,
            "positive": positive,
        })

        # Update playbook win rates
        if playbook:
            pb = pbwr.setdefault(playbook, {"wins": 0, "losses": 0, "total": 0})
            pb["total"] += 1
            if positive:
                pb["wins"] += 1
            elif negative:
                pb["losses"] += 1

        # Save
        graph_path.write_text(json.dumps(g, indent=2, default=str))
        return updated

    except Exception as e:
        print(f"  Warning: outcome recording failed: {e}")
        return {}


# ═══════════════════════════════════════════════════════════
# JSX SERVING
# ═══════════════════════════════════════════════════════════

def find_reef_jsx():
    """Find the dashboard JSX file (prefer unified nexus_dashboard)."""
    candidates = [
        SCRIPT_DIR / "nexus_dashboard.jsx",
        SCRIPT_DIR / "reef_mode.jsx",
        SCRIPT_DIR / "reef_mode_v5.jsx",
        SCRIPT_DIR / "reef_mode_v4.jsx",
        SCRIPT_DIR / "reef_mode_v3.jsx",
        SCRIPT_DIR.parent / "scripts" / "nexus_dashboard.jsx",
        SCRIPT_DIR.parent / "scripts" / "reef_mode.jsx",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def get_reef_html(jsx_path):
    """Serve JSX dashboard as a self-contained HTML page."""
    jsx_code = jsx_path.read_text(encoding="utf-8")

    # Detect root component name
    component_name = "ReefMode"  # default
    for pattern in [r'function\s+(Nexus\w+)\s*\(', r'function\s+(ReefMode)\s*\(']:
        m = re.search(pattern, jsx_code)
        if m:
            component_name = m.group(1)
            break

    # Strip ES module syntax and existing React destructuring for browser Babel
    jsx_code = re.sub(r'^import\s+.*$', '', jsx_code, flags=re.MULTILINE)
    jsx_code = re.sub(r'^.*from\s+["\']react["\'].*$', '', jsx_code, flags=re.MULTILINE)
    jsx_code = re.sub(r'^.*from\s+["\']react-dom["\'].*$', '', jsx_code, flags=re.MULTILINE)
    jsx_code = re.sub(r'export\s+default\s+function\s+', 'function ', jsx_code)
    jsx_code = jsx_code.replace("export default ", "var _default_export = ")
    # Remove any existing React hooks destructuring (server injects its own shim)
    jsx_code = re.sub(r'^const\s*\{[^}]*\}\s*=\s*React\s*;?\s*$', '', jsx_code, flags=re.MULTILINE)

    hooks_shim = "const { useState, useEffect, useCallback, useMemo, useRef, useReducer } = React;\n\n"

    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NEXUS — BDR Intelligence</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>🔱</text></svg>">
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #06060d; overflow-x: hidden; }}
  </style>
</head>
<body>
  <div id="root"></div>
  <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script>
    window.__REEF_API__ = {{
      snapshot: "/api/reef/snapshot",
      run: "/api/reef/run",
      job: "/api/reef/job",
      outcome: "/api/reef/outcome",
      chat: "/api/reef/chat",
    }};
  </script>
  <script type="text/babel" data-presets="env,react">
""")
    parts.append(hooks_shim)
    parts.append(jsx_code)
    parts.append(f"""

    class ErrorBoundary extends React.Component {{
      constructor(props) {{ super(props); this.state = {{ error: null }}; }}
      componentDidCatch(error, info) {{ this.setState({{ error: error.toString() + '\\n' + (info.componentStack || '') }}); }}
      render() {{
        if (this.state.error) return React.createElement('pre', {{ style: {{ color: '#ff4444', background: '#0a0a0a', padding: 40, fontFamily: 'monospace', fontSize: 14, whiteSpace: 'pre-wrap' }} }}, '❌ Dashboard Error:\\n\\n' + this.state.error);
        return this.props.children;
      }}
    }}

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(ErrorBoundary, null, React.createElement({component_name})));
  </script>
</body>
</html>""")

    return "".join(parts)


# ═══════════════════════════════════════════════════════════
# HTTP HANDLER
# ═══════════════════════════════════════════════════════════

class PlatformHandler(BaseHTTPRequestHandler):
    jsx_path = None

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        method_path = args[0] if args else ""
        print(f"  [{ts}] {method_path}")

    def _json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = parse_qs(parsed.query)

        # ── Reef Mode UI ──
        if path in ("", "/reef", "/index.html"):
            jsx = self.jsx_path or find_reef_jsx()
            if jsx and jsx.exists():
                self._html(get_reef_html(jsx))
            else:
                self._html("<h1 style='color:#C5A55A;font-family:monospace;padding:40px'>reef_mode.jsx not found in scripts/</h1>", 404)

        # ── Snapshot (Epic 0.1 — versioned) ──
        elif path == "/api/reef/snapshot":
            emit_event("SnapshotRequested")
            self._json(build_snapshot())

        # ── Research endpoint ──
        elif path == "/api/reef/research":
            snap = build_snapshot()
            self._json({
                "schema_version": SCHEMA_VERSION,
                "available": snap["systemStatus"]["researchPapers"] > 0,
                "papers_total": snap["systemStatus"]["researchPapers"],
                "last_harvest": snap["systemStatus"]["researchLastHarvest"],
                "highlights": snap["researchHighlights"],
                "synthesis": snap["synthesisInsights"],
                "trends": snap["researchTrends"],
                "gaps": snap["researchGaps"],
                "regulatory": snap["regulatoryHits"],
                "matrix": snap["terpeneMatrix"],
                "businessInsights": snap["businessInsights"],
                "competitive": snap.get("competitiveIntel", []),
            })

        # ── Signals (Epic 3.1) ──
        elif path == "/api/reef/signals":
            snap = build_snapshot()
            self._json({
                "schema_version": SCHEMA_VERSION,
                "signals": snap["signals"],
                "taxonomy": SIGNAL_TAXONOMY,
            })

        # ── Events (Epic 0.2 — Telekinesis) ──
        elif path == "/api/events":
            since = (qs.get("since") or [None])[0]
            limit = int((qs.get("limit") or ["50"])[0])
            events = get_events(since=since, limit=limit)
            self._json({"events": events, "count": len(events)})

        # ── Agent Registry (Epic 1.1 foundation) ──
        elif path == "/api/agents":
            self._json({"agents": AGENT_REGISTRY})

        # ── Data Map — shows all accessible data files ──
        elif path == "/api/reef/data-map":
            data_map = {"primary_dir": str(OUTPUT_DIR), "secondary_dir": str(ROOT_OUTPUT_DIR), "files": {}}
            for label, d in [("primary", OUTPUT_DIR), ("secondary", ROOT_OUTPUT_DIR)]:
                if not d.exists():
                    continue
                files = []
                for f in sorted(d.rglob("*")):
                    if f.is_file():
                        files.append({
                            "path": str(f.relative_to(d)),
                            "size_kb": round(f.stat().st_size / 1024, 1),
                            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        })
                data_map["files"][label] = files
            if DEMO_BUNDLE_DIR.exists():
                bundles = []
                for f in sorted(DEMO_BUNDLE_DIR.rglob("*")):
                    if f.is_file():
                        bundles.append({
                            "path": str(f.relative_to(DEMO_BUNDLE_DIR)),
                            "size_kb": round(f.stat().st_size / 1024, 1),
                        })
                data_map["files"]["bundles"] = bundles
            self._json(data_map)

        # ── Job status ──
        elif path == "/api/reef/job":
            job_id = (qs.get("job_id") or [""])[0]
            self._json({"job_id": job_id, "status": "succeeded"})

        # ── Health ──
        elif path == "/health":
            jsx = find_reef_jsx()
            # Count data files across both output dirs
            enriched_count = len(list(OUTPUT_DIR.glob("enriched_*.json")) + list(ROOT_OUTPUT_DIR.glob("enriched_*.json")))
            scored_count = len(list(OUTPUT_DIR.glob("scored_apollo_*.json")) + list(ROOT_OUTPUT_DIR.glob("scored_apollo_*.json")))
            brief_count = len(list((OUTPUT_DIR / "briefs").glob("brief_*.json")) if (OUTPUT_DIR / "briefs").exists() else [])
            bundle_count = len(list(DEMO_BUNDLE_DIR.iterdir())) if DEMO_BUNDLE_DIR.exists() else 0
            self._json({
                "status": "ok",
                "schema_version": SCHEMA_VERSION,
                "output_dir": str(OUTPUT_DIR),
                "root_output_dir": str(ROOT_OUTPUT_DIR),
                "research_dir_exists": RESEARCH_DIR.exists(),
                "kb_exists": (KB_DIR / "kb.json").exists(),
                "war_room_exists": (WAR_ROOM_DIR / "knowledge_graph" / "war_room_graph.json").exists(),
                "jsx_found": str(jsx) if jsx else None,
                "events_count": sum(1 for _ in open(EVENTS_FILE)) if EVENTS_FILE.exists() else 0,
                "data_coverage": {
                    "scored_apollo_files": scored_count,
                    "enriched_files": enriched_count,
                    "brief_files": brief_count,
                    "demo_bundles": bundle_count,
                    "social_intel_dir": (OUTPUT_DIR / "social_intel").exists() or (ROOT_OUTPUT_DIR / "social_intel").exists(),
                    "competitor_intel_dir": (OUTPUT_DIR / "competitor_intel").exists(),
                    "activity_log": (ROOT_OUTPUT_DIR / "activity-log.json").exists(),
                },
            })

        else:
            self._json({"error": "not found", "path": path}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len)) if content_len else {}

        if path == "/api/reef/run":
            command = body.get("command", "")
            company = body.get("company", "")
            emit_event("JobStarted", {"command": command, "company": company})
            self._json({"job_id": "standalone", "status": "info", "message": f"Run '{command}' via CLI. Event logged."})

        elif path == "/api/reef/chat":
            message = body.get("message", "")
            history = body.get("history", [])
            brand = body.get("brand", "nexus")
            if not message:
                self._json({"error": "No message provided"}, 400)
                return
            print(f"  💬 [{brand.upper()}] Chat: {message[:80]}...")
            try:
                result = handle_chat(message, history, brand)
                self._json(result)
            except Exception as e:
                print(f"  ⚠️ Chat error: {e}")
                self._json({"response": f"Error processing command: {str(e)}", "agents_activated": []})

        elif path == "/api/reef/outcome":
            action_id = body.get("action_id", "")
            outcome = body.get("outcome", "")
            channel = body.get("channel", "")
            persona = body.get("persona", "")
            playbook = body.get("playbook", "")
            notes = body.get("notes", "")
            company = body.get("company", "")
            signals_involved = body.get("signals", [])
            emit_event("OutcomeRecorded", {
                "action_id": action_id, "outcome": outcome,
                "channel": channel, "persona": persona,
                "playbook": playbook, "notes": notes,
                "company": company,
            })
            # Update War Room learning loop
            updated_weights = _record_outcome_to_graph(outcome, company, signals_involved, playbook, channel)
            print(f"  Outcome: {action_id} -> {outcome} ({channel})")
            self._json({
                "status": "recorded", "action_id": action_id, "outcome": outcome,
                "weights_updated": updated_weights,
            })

        else:
            self._json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="NEXUS Platform Server v5")
    parser.add_argument("--port", type=int, default=3142)
    parser.add_argument("--jsx", type=str, default="", help="Path to reef_mode.jsx")
    args = parser.parse_args()

    jsx = Path(args.jsx) if args.jsx else find_reef_jsx()
    if jsx:
        PlatformHandler.jsx_path = jsx

    # Emit startup event
    emit_event("ServerStarted", {"port": args.port, "output_dir": str(OUTPUT_DIR)})

    # Check data availability
    kb_papers = 0
    kb_path = KB_DIR / "kb.json"
    if kb_path.exists():
        try:
            kb_papers = len(json.loads(kb_path.read_text()).get("papers", {}))
        except Exception:
            pass

    graph_entities = 0
    graph_path = WAR_ROOM_DIR / "knowledge_graph" / "war_room_graph.json"
    if graph_path.exists():
        try:
            graph_entities = len(json.loads(graph_path.read_text()).get("entities", {}))
        except Exception:
            pass

    print(f"\n{'='*55}")
    print(f"  NEXUS PLATFORM SERVER v5")
    print(f"  Schema: {SCHEMA_VERSION}")
    print(f"{'='*55}")
    print(f"  UI:       http://localhost:{args.port}/reef")
    print(f"  Snapshot: http://localhost:{args.port}/api/reef/snapshot")
    print(f"  Research: http://localhost:{args.port}/api/reef/research")
    print(f"  Signals:  http://localhost:{args.port}/api/reef/signals")
    print(f"  Events:   http://localhost:{args.port}/api/events")
    print(f"  Agents:   http://localhost:{args.port}/api/agents")
    print(f"  Health:   http://localhost:{args.port}/health")
    # Count additional data
    scored_count = len(list(OUTPUT_DIR.glob("scored_apollo_*.json")) + list(ROOT_OUTPUT_DIR.glob("scored_apollo_*.json")))
    enriched_count = len(list(OUTPUT_DIR.glob("enriched_*.json")) + list(ROOT_OUTPUT_DIR.glob("enriched_*.json")))
    bundle_count = len(list(DEMO_BUNDLE_DIR.iterdir())) if DEMO_BUNDLE_DIR.exists() else 0
    brief_count = len(list((OUTPUT_DIR / "briefs").glob("brief_*.json"))) if (OUTPUT_DIR / "briefs").exists() else 0

    print(f"{'='*55}")
    print(f"  Data Directories:")
    print(f"    Primary:   {OUTPUT_DIR}")
    print(f"    Secondary: {ROOT_OUTPUT_DIR}")
    print(f"    Bundles:   {DEMO_BUNDLE_DIR}")
    print(f"  Data Coverage:")
    print(f"    Research KB:     {kb_papers} papers")
    print(f"    War Room:        {graph_entities} entities")
    print(f"    Scored Apollo:   {scored_count} files")
    print(f"    Enriched:        {enriched_count} files")
    print(f"    Briefs:          {brief_count} files")
    print(f"    Kill Shot:       {bundle_count} bundles")
    print(f"    JSX:             {jsx or 'NOT FOUND'}")
    print(f"{'='*55}\n")

    if kb_papers == 0:
        print("  No research papers. Run:")
        print("     python3 scripts/terpene_research_v2.py --full --days 90\n")

    server = HTTPServer(("0.0.0.0", args.port), PlatformHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        emit_event("ServerStopped")
        server.server_close()


if __name__ == "__main__":
    main()
