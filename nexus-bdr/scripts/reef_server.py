#!/usr/bin/env python3
"""
NEXUS Platform Server v6
=========================
Unified server for Reef Mode + Research Intelligence + Event Log.

Implements:
  Epic 0.1 — Canonical data contracts (versioned snapshot schema)
  Epic 0.2 — Telekinesis v1 (event log + polling endpoint)
  Epic 3.1 — Signal taxonomy + reliability priors
  Epic 4.1 — Enhanced abstract extraction fields
  Epic 4.4 — Research → Business translation layer
  Epic 5.0 — Independent company dossiers
  Epic 5.1 — Enhanced pipeline with stages + forecasting
  Epic 5.2 — PhD-grade terpene intelligence lab

Endpoints:
  GET  /reef                        → Reef Mode UI
  GET  /api/reef/snapshot           → Versioned snapshot (stable schema)
  GET  /api/reef/research           → PhD-grade research intelligence
  GET  /api/reef/signals            → Signal feed with taxonomy + decay
  GET  /api/reef/companies          → All companies with independent data
  GET  /api/reef/company/<name>     → Full company dossier
  GET  /api/reef/pipeline           → Enhanced pipeline with stages + forecast
  GET  /api/events                  → Event log (polling, ?since=cursor)
  GET  /api/agents                  → Agent registry
  GET  /api/ontology                → Ontology schema + stats
  GET  /api/ontology/objects        → Query objects (?type=&department=&q=)
  GET  /api/ontology/object/<id>    → Single object + links (?department=)
  GET  /api/ontology/department/<d> → Department summary + available actions
  GET  /api/ontology/actions        → Action log (?department=&status=)
  GET  /api/ontology/reindex        → Force re-index from data files
  POST /api/ontology/actions        → Record a new cross-department action
  GET  /health                      → Health check
  POST /api/reef/run                → Trigger agent commands
  POST /api/reef/outcome            → Record outcomes

Usage:
  python3 reef_server.py                  # port 3142
  python3 reef_server.py --port 3141      # custom port
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

from ontology import (
    ObjectRegistry, index_from_existing_data,
    OBJECT_TYPES, LINK_TYPES, DEPARTMENTS, ACTION_TYPES, ONTOLOGY_VERSION,
)

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
RESEARCH_DIR = OUTPUT_DIR / "terpene_research"
KB_DIR = RESEARCH_DIR / "knowledge_base"
INSIGHTS_DIR = RESEARCH_DIR / "insights"
REPORTS_DIR = RESEARCH_DIR / "reports"
WAR_ROOM_DIR = OUTPUT_DIR / "war_room"
EVENTS_DIR = OUTPUT_DIR / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = EVENTS_DIR / "events.jsonl"

SCHEMA_VERSION = "7.0"

# ═══════════════════════════════════════════════════════════
# ONTOLOGY — Company-wide object registry
# ═══════════════════════════════════════════════════════════

REGISTRY = ObjectRegistry(OUTPUT_DIR)

def _init_ontology():
    """Initialize the ontology registry from existing data."""
    loaded = REGISTRY.load()
    if not loaded:
        counts = index_from_existing_data(REGISTRY, OUTPUT_DIR)
        REGISTRY.save()
        print(f"  Ontology: indexed {sum(counts.values())} objects from existing data: {dict(counts)}")
    else:
        print(f"  Ontology: loaded {len(REGISTRY.objects)} objects from disk")

BRIEFS_DIR = OUTPUT_DIR / "briefs"
SOCIAL_DIR = OUTPUT_DIR / "social_intel"
COMPETITOR_DIR = OUTPUT_DIR / "competitor_intel"
DEMO_BUNDLE_DIR = SCRIPT_DIR / "demo_bundle"


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

    # ── Event count ──
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE) as f:
                snapshot["systemStatus"]["eventsTotal"] = sum(1 for _ in f)
        except Exception:
            pass

    # ── Ontology stats ──
    snapshot["ontology"] = REGISTRY.stats()

    return snapshot


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
# EPIC 5.3 — COMPETITOR INTELLIGENCE DEEP DIVE
# ═══════════════════════════════════════════════════════════

def build_competitor_intel():
    """Build comprehensive competitor intelligence from war room + research."""
    snapshot = build_snapshot()
    competitors = snapshot.get("competitors", [])
    competitive_claims = snapshot.get("competitiveIntel", [])

    # Load competitor vulnerability scan if available
    vuln_dir = OUTPUT_DIR / "competitor_intel"
    if not vuln_dir.exists():
        vuln_dir = OUTPUT_DIR.parent / "outputs" / "competitor_intel"
    vuln_data = {}
    if vuln_dir.exists():
        for f in sorted(vuln_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:1]:
            try:
                raw = json.loads(f.read_text())
                comps_raw = raw.get("competitors_scanned", raw.get("competitors", {}))
                if isinstance(comps_raw, dict):
                    vuln_data = comps_raw
                elif isinstance(comps_raw, list):
                    for item in comps_raw:
                        if isinstance(item, dict) and item.get("name"):
                            vuln_data[item["name"]] = item
            except Exception:
                pass

    # Merge all competitor data
    comp_map = {}
    for c in competitors:
        name = c.get("name", "")
        if name:
            comp_map[name] = {**c, "signals": [], "displacement_angles": []}

    # Add vulnerability scan data
    for name, v_data in vuln_data.items():
        if isinstance(v_data, dict):
            if name in comp_map:
                comp_map[name].update({k: val for k, val in v_data.items() if k not in comp_map[name] or not comp_map[name][k]})
            else:
                comp_map[name] = {"name": name, **v_data, "signals": [], "displacement_angles": []}

    # Known competitor profiles (enriched with domain knowledge)
    COMPETITOR_DB = {
        "True Terpenes": {"pricing": "$80-150/L botanical, $2K-4K/L CDT", "weakness": "Slow custom orders (4-6 weeks), quality complaints, price increases", "tbf_angle": "Faster turnaround, better consistency, competitive pricing at scale", "dft_angle": "Hype strains they don't carry, faster shipping, no minimum BS", "market_position": "Market leader", "trustpilot_est": 3.0},
        "Abstrax Tech": {"pricing": "Premium CDT, $3K-6K/L", "weakness": "Expensive, complex ordering, slow response", "tbf_angle": "Match scientific rigor with simpler ordering", "dft_angle": "Great terps without PhD-level process", "market_position": "Premium/R&D focused", "trustpilot_est": 4.2},
        "Floraplex": {"pricing": "$30-60/L botanical", "weakness": "Inconsistent quality, synthetic undertones, no custom blending", "tbf_angle": "Consistency at volume pricing", "dft_angle": "Authentic profiles without synthetic taste", "market_position": "Budget botanical", "trustpilot_est": 3.8},
        "Denver Terpenes": {"pricing": "$50-100/L", "weakness": "Limited selection, regional only", "tbf_angle": "National reach + wider catalog", "dft_angle": "More strain options, same pricing", "market_position": "Regional player", "trustpilot_est": 3.5},
        "Peak Supply Co": {"pricing": "$40-80/L", "weakness": "Limited B2B, inconsistent availability", "tbf_angle": "Enterprise-grade supply chain", "dft_angle": "Reliable stock, no backorders", "market_position": "Mid-market", "trustpilot_est": 3.2},
        "Terps USA": {"pricing": "$25-50/L", "weakness": "Bottom-tier, no COAs, suspected synthetic", "tbf_angle": "Full COA transparency", "dft_angle": "Real botanical vs synthetic garbage", "market_position": "Bottom-tier", "trustpilot_est": 2.8},
        "Extract Consultants": {"pricing": "$60-120/L", "weakness": "Formulation-focused, slow innovation", "tbf_angle": "Faster R&D pipeline", "dft_angle": "No consulting fees, just great terps", "market_position": "Consulting/formulation", "trustpilot_est": 3.9},
    }

    for name, profile in COMPETITOR_DB.items():
        if name not in comp_map:
            comp_map[name] = {"name": name, "signals": [], "displacement_angles": []}
        comp_map[name].update({k: v for k, v in profile.items() if k not in comp_map[name] or not comp_map[name][k]})

    # Attach competitor signals from war room
    for sig in snapshot.get("signals", []):
        for name in comp_map:
            if name.lower() in sig.get("summary", "").lower() or name.lower() in str(sig.get("entities", [])).lower():
                comp_map[name]["signals"].append(sig)

    result = list(comp_map.values())
    result.sort(key=lambda x: x.get("trustpilot_est", x.get("trustpilot", 5) or 5))
    return {
        "competitors": result,
        "claims": competitive_claims,
        "total": len(result),
    }


# ═══════════════════════════════════════════════════════════
# EPIC 5.4 — SYSTEM ANALYTICS + PERFORMANCE
# ═══════════════════════════════════════════════════════════

def build_analytics():
    """Build system analytics: pipeline health, costs, agent performance."""
    snapshot = build_snapshot()
    companies, _ = build_company_list()

    # Pipeline health metrics
    total = len(companies)
    stages = {"new": 0, "scored": 0, "enriched": 0, "researched": 0, "outreach_ready": 0}
    brands = {"TBF": 0, "DFT": 0}
    temps = {"Hot": 0, "Warm": 0, "Cool": 0, "Cold": 0}
    score_sum = 0
    contacts_sum = 0
    emails_sum = 0
    verified_sum = 0
    briefs_done = 0
    with_outreach = 0
    regions = {}

    for co in companies:
        stages[co.get("stage", "new")] = stages.get(co.get("stage", "new"), 0) + 1
        brands[co.get("brand", "DFT")] = brands.get(co.get("brand", "DFT"), 0) + 1
        temps[co.get("temperature", "Cold")] = temps.get(co.get("temperature", "Cold"), 0) + 1
        score_sum += co.get("avg_score", 0)
        contacts_sum += co.get("contact_count", 0)
        emails_sum += co.get("emails_total", 0)
        verified_sum += co.get("emails_verified", 0)
        if co.get("brief_status") == "complete":
            briefs_done += 1
        if co.get("outreach_bundle"):
            with_outreach += 1
        region = co.get("country", co.get("state", "Unknown"))
        regions[region] = regions.get(region, 0) + 1

    # Signal analytics
    signals = snapshot.get("signals", [])
    signal_by_cat = {}
    for s in signals:
        cat = s.get("category", "unknown")
        signal_by_cat[cat] = signal_by_cat.get(cat, 0) + 1

    # Research metrics
    research_papers = snapshot["systemStatus"]["researchPapers"]
    insights_count = len(snapshot.get("synthesisInsights", []))
    business_insights = len(snapshot.get("businessInsights", []))
    regulatory_hits = len(snapshot.get("regulatoryHits", []))

    # Agent registry
    agent_count = len(AGENT_REGISTRY)

    # Learning metrics
    learning = snapshot.get("learning", {})
    signal_weights = learning.get("signalWeights", {})
    playbook_wins = learning.get("playbookWinRates", {})

    return {
        "pipeline": {
            "total_companies": total,
            "total_contacts": contacts_sum,
            "total_emails": emails_sum,
            "verified_emails": verified_sum,
            "avg_score": round(score_sum / total) if total else 0,
            "briefs_complete": briefs_done,
            "outreach_ready": with_outreach,
            "stages": stages,
            "brands": brands,
            "temperatures": temps,
            "regions": dict(sorted(regions.items(), key=lambda x: -x[1])[:15]),
            "pipeline_velocity": {
                "new_to_scored_pct": round(stages.get("scored", 0) / max(total, 1) * 100),
                "scored_to_enriched_pct": round(stages.get("enriched", 0) / max(stages.get("scored", 1), 1) * 100),
                "enriched_to_researched_pct": round(stages.get("researched", 0) / max(stages.get("enriched", 1), 1) * 100),
                "researched_to_outreach_pct": round(stages.get("outreach_ready", 0) / max(stages.get("researched", 1), 1) * 100),
            },
        },
        "intelligence": {
            "entities_tracked": snapshot["systemStatus"]["entitiesTracked"],
            "competitors_tracked": snapshot["systemStatus"]["competitorsTracked"],
            "signals_total": len(signals),
            "signals_today": snapshot["systemStatus"]["signalsToday"],
            "signals_by_category": signal_by_cat,
            "research_papers": research_papers,
            "synthesis_insights": insights_count,
            "business_insights": business_insights,
            "regulatory_hits": regulatory_hits,
        },
        "system": {
            "agents": agent_count,
            "signal_weights": len(signal_weights) if isinstance(signal_weights, dict) else 0,
            "outcomes_recorded": snapshot["systemStatus"]["outcomesRecordedToday"],
            "events_total": snapshot["systemStatus"]["eventsTotal"],
            "actions_queued": snapshot["systemStatus"]["actionsQueued"],
        },
        "learning": {
            "signal_weights": snapshot.get("signalWeights", []),
            "playbook_win_rates": playbook_wins,
        },
    }


# ═══════════════════════════════════════════════════════════
# EPIC 5.0 — INDEPENDENT COMPANY DOSSIERS
# ═══════════════════════════════════════════════════════════

def _load_pipeline_leads():
    """Load scored/enriched pipeline data, preferring most recent."""
    for prefix in ("scored_apollo_", "enriched_", "imported_"):
        files = sorted(OUTPUT_DIR.glob(f"{prefix}*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if files:
            try:
                data = json.loads(files[0].read_text())
                return data.get("leads", []), str(files[0].name)
            except Exception:
                continue
    return [], ""


def _load_briefs():
    """Load all company briefs keyed by company name."""
    briefs = {}
    if not BRIEFS_DIR.exists():
        return briefs
    for f in sorted(BRIEFS_DIR.glob("brief_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(f.read_text())
            company = data.get("metadata", {}).get("company", "")
            if company and company not in briefs:
                briefs[company] = data
        except Exception:
            continue
    return briefs


def _load_demo_bundles():
    """Load demo bundle data keyed by company name."""
    bundles = {}
    if not DEMO_BUNDLE_DIR.exists():
        return bundles
    for d in DEMO_BUNDLE_DIR.iterdir():
        if not d.is_dir():
            continue
        company_key = d.name.rsplit("_", 2)[0].replace("_", " ").title()
        bundle = {"files": [], "outreach": {}}
        for f in sorted(d.iterdir()):
            bundle["files"].append(f.name)
            if f.suffix in (".txt", ".md"):
                try:
                    content = f.read_text(encoding="utf-8")[:3000]
                    key = f.stem.split("_", 1)[-1] if "_" in f.stem else f.stem
                    bundle["outreach"][key] = content
                except Exception:
                    pass
            elif f.suffix == ".json":
                try:
                    content = json.loads(f.read_text())
                    key = f.stem.split("_", 1)[-1] if "_" in f.stem else f.stem
                    bundle["outreach"][key] = content
                except Exception:
                    pass
        if company_key not in bundles:
            bundles[company_key] = bundle
    return bundles


def build_company_list():
    """Build independent company profiles from pipeline + briefs + signals."""
    leads, source = _load_pipeline_leads()
    briefs = _load_briefs()
    bundles = _load_demo_bundles()
    snapshot = build_snapshot()
    signals = snapshot.get("signals", [])

    # Group leads by company
    company_map = {}
    for lead in leads:
        co = lead.get("company_name", "Unknown")
        if co == "Unknown" or not co:
            continue
        if co not in company_map:
            company_map[co] = {
                "name": co,
                "domain": lead.get("domain", ""),
                "state": lead.get("state", ""),
                "country": lead.get("country", ""),
                "industry": lead.get("industry", ""),
                "employees": lead.get("employees", ""),
                "company_size": lead.get("company_size", ""),
                "company_linkedin": lead.get("company_linkedin", ""),
                "brand": lead.get("nexus_brand", "DFT"),
                "brand_reason": lead.get("brand_reason", ""),
                "keywords": lead.get("keywords", ""),
                "technologies": lead.get("technologies", ""),
                "contacts": [],
                "scores": [],
                "emails_verified": 0,
                "emails_total": 0,
                "extraction_methods": [],
                "product_types": [],
            }
        c = company_map[co]
        score = lead.get("nexus_lead_score", 0)
        c["scores"].append(score)
        contact = {
            "name": lead.get("contact_name", ""),
            "title": lead.get("title", ""),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", ""),
            "linkedin": lead.get("linkedin", lead.get("linkedin_url", "")),
            "seniority": lead.get("seniority", ""),
            "department": lead.get("department", lead.get("departments", "")),
            "decision_maker_level": lead.get("decision_maker_level", ""),
            "score": score,
            "score_reasons": lead.get("score_reasons", []),
            "temperature": lead.get("prospect_temperature", ""),
            "email_status": lead.get("email_status", ""),
            "icp_tier": lead.get("icp_tier", ""),
        }
        if lead.get("email"):
            c["emails_total"] += 1
            if lead.get("email_status") in ("Valid", "Verified", "valid"):
                c["emails_verified"] += 1
        c["contacts"].append(contact)
        for m in lead.get("extraction_methods", []):
            if m not in c["extraction_methods"]:
                c["extraction_methods"].append(m)
        for p in lead.get("product_types", []):
            if p not in c["product_types"]:
                c["product_types"].append(p)

    # Enrich with brief data
    for co_name, co in company_map.items():
        brief = briefs.get(co_name)
        if brief:
            phases = brief.get("phases", {})
            p1 = phases.get("phase_1", {})
            p4 = phases.get("phase_4", {})
            p6 = phases.get("phase_6", {})
            co["brief_status"] = "complete"
            co["brief_data"] = {
                "description": p1.get("description", ""),
                "founded": p1.get("founded", ""),
                "headquarters": p1.get("headquarters", ""),
                "business_model": p1.get("business_model", ""),
                "company_type": p1.get("company_type", ""),
                "brand_positioning": p1.get("brand_positioning", ""),
                "key_products": p1.get("key_products_overview", []),
                "recent_news": p1.get("recent_news", []),
                "growth_signals": p1.get("growth_signals", []),
                "social_media": p1.get("social_media", {}),
                "terpene_relevance": p1.get("initial_terpene_relevance", ""),
                "size_estimate": p1.get("size_estimate", {}),
                "markets": p1.get("markets", {}),
            }
            co["supplier_intel"] = p4.get("current_supplier_assessment", {})
            co["displacement_strategy"] = p4.get("displacement_strategy", {})
            co["pricing_intel"] = p4.get("pricing_intelligence", {})
            co["executive_summary"] = p6.get("executive_summary", {})
            co["objections"] = p6.get("objections", [])
            co["outreach_sequence"] = p6.get("outreach_sequence", [])
            co["sample_kit"] = p6.get("sample_kit", {})
            co["deal_model"] = p6.get("deal_model", phases.get("phase_5", {}).get("deal_model", {}))
        else:
            co["brief_status"] = "pending"

        # Attach bundle outreach
        for bundle_key, bundle in bundles.items():
            if bundle_key.lower().replace(" ", "") in co_name.lower().replace(" ", ""):
                co["outreach_bundle"] = bundle.get("outreach", {})
                break

        # Attach relevant signals
        co_signals = []
        for sig in signals:
            entities = sig.get("entities", [])
            summary = sig.get("summary", "").lower()
            if any(co_name.lower() in str(e).lower() for e in entities) or co_name.lower() in summary:
                co_signals.append(sig)
        co["signals"] = co_signals[:20]

    # Build sorted list
    companies = []
    for co in company_map.values():
        avg_score = round(sum(co["scores"]) / len(co["scores"])) if co["scores"] else 0
        top_score = max(co["scores"]) if co["scores"] else 0
        co["avg_score"] = avg_score
        co["top_score"] = top_score
        co["contact_count"] = len(co["contacts"])
        co["temperature"] = "Hot" if avg_score >= 80 else "Warm" if avg_score >= 60 else "Cool" if avg_score >= 40 else "Cold"
        # Sort contacts: highest score first, then by decision maker level
        dm_order = {"C-Suite": 0, "VP": 1, "Director": 2, "Manager": 3, "Individual": 4}
        co["contacts"].sort(key=lambda x: (-x["score"], dm_order.get(x["decision_maker_level"], 5)))
        co["top_contact"] = co["contacts"][0] if co["contacts"] else None
        # Determine pipeline stage
        if co.get("outreach_bundle"):
            co["stage"] = "outreach_ready"
        elif co.get("brief_status") == "complete":
            co["stage"] = "researched"
        elif co["emails_verified"] > 0:
            co["stage"] = "enriched"
        elif co["contact_count"] > 0:
            co["stage"] = "scored"
        else:
            co["stage"] = "new"
        del co["scores"]
        companies.append(co)

    companies.sort(key=lambda x: -x["avg_score"])
    return companies, source


def build_pipeline_data():
    """Build enhanced pipeline with stages, forecasting, and velocity."""
    companies, source = build_company_list()

    # Stage counts
    stages = {"new": [], "scored": [], "enriched": [], "researched": [], "outreach_ready": [], "engaged": [], "meeting": [], "proposal": [], "won": []}
    for co in companies:
        stage = co.get("stage", "new")
        if stage in stages:
            stages[stage].append(co["name"])

    # Temperature distribution
    temps = {"Hot": 0, "Warm": 0, "Cool": 0, "Cold": 0}
    total_contacts = 0
    total_emails = 0
    total_verified = 0
    brand_split = {"TBF": 0, "DFT": 0}
    for co in companies:
        temps[co["temperature"]] = temps.get(co["temperature"], 0) + 1
        total_contacts += co["contact_count"]
        total_emails += co["emails_total"]
        total_verified += co["emails_verified"]
        brand_split[co.get("brand", "DFT")] = brand_split.get(co.get("brand", "DFT"), 0) + 1

    # Revenue forecast (from deal models)
    forecast = {"conservative": 0, "likely": 0, "upside": 0}
    for co in companies:
        dm = co.get("deal_model", {})
        if dm:
            for tier in ("conservative", "likely", "upside"):
                tier_data = dm.get(tier, {})
                val = tier_data.get("annual_value", tier_data.get("annual_revenue", ""))
                if isinstance(val, str):
                    nums = re.findall(r'[\d,]+', val.replace(",", ""))
                    if nums:
                        try:
                            forecast[tier] += int(nums[0])
                        except ValueError:
                            pass
                elif isinstance(val, (int, float)):
                    forecast[tier] += int(val)

    # Hot list: top 5 with next actions
    hot_list = []
    for co in companies[:10]:
        if co["temperature"] in ("Hot", "Warm"):
            next_action = "Run sales intel brief" if co["brief_status"] == "pending" else \
                         "Generate kill shot bundle" if not co.get("outreach_bundle") else \
                         "Send outreach sequence"
            hot_list.append({
                "company": co["name"],
                "score": co["avg_score"],
                "brand": co.get("brand", ""),
                "contacts": co["contact_count"],
                "verified_emails": co["emails_verified"],
                "top_contact": co["top_contact"]["name"] if co.get("top_contact") else "",
                "top_title": co["top_contact"]["title"] if co.get("top_contact") else "",
                "stage": co["stage"],
                "next_action": next_action,
                "brief_status": co["brief_status"],
            })
            if len(hot_list) >= 5:
                break

    return {
        "source": source,
        "total_companies": len(companies),
        "total_contacts": total_contacts,
        "total_emails": total_emails,
        "total_verified": total_verified,
        "temperatures": temps,
        "brand_split": brand_split,
        "stages": {k: {"count": len(v), "companies": v} for k, v in stages.items()},
        "forecast": forecast,
        "hot_list": hot_list,
        "companies": companies,
    }


# ═══════════════════════════════════════════════════════════
# JSX SERVING
# ═══════════════════════════════════════════════════════════

def find_reef_jsx():
    """Find the dashboard JSX file (prefer unified nexus_dashboard)."""
    candidates = [
        SCRIPT_DIR / "nexus_v5.jsx",
        SCRIPT_DIR / "nexus_dashboard.jsx",
        SCRIPT_DIR / "reef_mode.jsx",
        SCRIPT_DIR / "reef_mode_v5.jsx",
        SCRIPT_DIR / "reef_mode_v4.jsx",
        SCRIPT_DIR / "reef_mode_v3.jsx",
        SCRIPT_DIR.parent / "scripts" / "nexus_v5.jsx",
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

        # ── Companies list (Epic 5.0) ──
        elif path == "/api/reef/companies":
            companies, source = build_company_list()
            self._json({"schema_version": SCHEMA_VERSION, "source": source, "companies": companies})

        # ── Single company dossier (Epic 5.0) ──
        elif path.startswith("/api/reef/company/"):
            company_name = path.split("/api/reef/company/", 1)[1]
            company_name = company_name.replace("%20", " ").replace("+", " ")
            companies, _ = build_company_list()
            match = None
            for co in companies:
                if co["name"].lower() == company_name.lower():
                    match = co
                    break
            if not match:
                for co in companies:
                    if company_name.lower() in co["name"].lower():
                        match = co
                        break
            if match:
                self._json({"schema_version": SCHEMA_VERSION, "company": match})
            else:
                self._json({"error": f"Company '{company_name}' not found"}, 404)

        # ── Enhanced pipeline (Epic 5.1) ──
        elif path == "/api/reef/pipeline":
            self._json({"schema_version": SCHEMA_VERSION, **build_pipeline_data()})

        # ── Competitor intelligence (Epic 5.3) ──
        elif path == "/api/reef/competitors":
            self._json({"schema_version": SCHEMA_VERSION, **build_competitor_intel()})

        # ── Analytics (Epic 5.4) ──
        elif path == "/api/reef/analytics":
            self._json({"schema_version": SCHEMA_VERSION, **build_analytics()})

        # ── Job status ──
        elif path == "/api/reef/job":
            job_id = (qs.get("job_id") or [""])[0]
            self._json({"job_id": job_id, "status": "succeeded"})

        # ── Health ──
        elif path == "/health":
            jsx = find_reef_jsx()
            self._json({
                "status": "ok",
                "schema_version": SCHEMA_VERSION,
                "output_dir": str(OUTPUT_DIR),
                "research_dir_exists": RESEARCH_DIR.exists(),
                "kb_exists": (KB_DIR / "kb.json").exists(),
                "war_room_exists": (WAR_ROOM_DIR / "knowledge_graph" / "war_room_graph.json").exists(),
                "jsx_found": str(jsx) if jsx else None,
                "events_count": sum(1 for _ in open(EVENTS_FILE)) if EVENTS_FILE.exists() else 0,
            })

        # ══════════════════════════════════════════════════════
        # ONTOLOGY API — Company-wide object model
        # ══════════════════════════════════════════════════════

        # GET /api/ontology — Schema + stats overview
        elif path == "/api/ontology":
            self._json({
                "ontology_version": ONTOLOGY_VERSION,
                "schema_version": SCHEMA_VERSION,
                "stats": REGISTRY.stats(),
                "object_types": {k: {"label": v["label"], "departments": v["departments"]} for k, v in OBJECT_TYPES.items()},
                "link_types": LINK_TYPES,
                "departments": DEPARTMENTS,
                "action_types": ACTION_TYPES,
            })

        # GET /api/ontology/objects?type=company&department=bdr&q=search
        elif path == "/api/ontology/objects":
            obj_type = (qs.get("type") or [None])[0]
            dept = (qs.get("department") or [None])[0]
            query = (qs.get("q") or [None])[0]
            limit = int((qs.get("limit") or ["50"])[0])

            if query:
                results = REGISTRY.search(query, obj_type=obj_type, department=dept, limit=limit)
            elif obj_type:
                results = REGISTRY.get_by_type(obj_type, department=dept)[:limit]
            else:
                results = [o.to_dict() for o in list(REGISTRY.objects.values())[:limit]]

            self._json({
                "ontology_version": ONTOLOGY_VERSION,
                "count": len(results),
                "objects": results,
            })

        # GET /api/ontology/object/<id>?department=bdr
        elif path.startswith("/api/ontology/object/"):
            obj_id = path.split("/api/ontology/object/", 1)[1]
            dept = (qs.get("department") or [None])[0]
            obj = REGISTRY.get(obj_id)
            if obj:
                data = obj.project(dept) if dept else obj.to_dict()
                linked = REGISTRY.get_linked(obj_id, department=dept)
                if data:
                    data["linked_objects"] = linked
                    self._json({"ontology_version": ONTOLOGY_VERSION, "object": data})
                else:
                    self._json({"error": f"Object not visible to department '{dept}'"}, 403)
            else:
                self._json({"error": "Object not found"}, 404)

        # GET /api/ontology/department/<dept>
        elif path.startswith("/api/ontology/department/"):
            dept = path.split("/api/ontology/department/", 1)[1]
            if dept in DEPARTMENTS:
                self._json({
                    "ontology_version": ONTOLOGY_VERSION,
                    **REGISTRY.department_summary(dept),
                })
            else:
                self._json({"error": f"Unknown department '{dept}'"}, 404)

        # GET /api/ontology/actions?department=bdr&status=pending
        elif path == "/api/ontology/actions":
            dept = (qs.get("department") or [None])[0]
            status = (qs.get("status") or [None])[0]
            limit = int((qs.get("limit") or ["50"])[0])
            actions = REGISTRY.get_actions(department=dept, status=status, limit=limit)
            self._json({"ontology_version": ONTOLOGY_VERSION, "count": len(actions), "actions": actions})

        # GET /api/ontology/notifications?department=rd&since=2026-01-01
        elif path == "/api/ontology/notifications":
            dept = (qs.get("department") or [None])[0]
            since = (qs.get("since") or [None])[0]
            limit = int((qs.get("limit") or ["50"])[0])
            notifications = REGISTRY.get_notifications(department=dept, since=since, limit=limit)
            self._json({"ontology_version": ONTOLOGY_VERSION, "count": len(notifications), "notifications": notifications})

        # GET /api/ontology/reindex — Force re-index from data files
        elif path == "/api/ontology/reindex":
            REGISTRY.objects.clear()
            REGISTRY.by_type.clear()
            counts = index_from_existing_data(REGISTRY, OUTPUT_DIR)
            REGISTRY.save()
            self._json({"ontology_version": ONTOLOGY_VERSION, "reindexed": True, "counts": counts})

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

        elif path == "/api/reef/campaign/generate":
            name = body.get("name", "Untitled Campaign")
            ctype = body.get("type", "product_launch")
            audience = body.get("audience", "enterprise")
            terpenes = body.get("terpenes", [])
            message = body.get("message", "")
            tone = body.get("tone", "professional")
            brand = body.get("brand", "TBF")

            terp_str = ", ".join(terpenes) if terpenes else "Myrcene, Limonene, Beta-Caryophyllene"
            brand_name = "Terpene Belt Farms" if brand in ("TBF", "BOTH") else "Duty Free Terpenes"
            primary_color = "#2D5016" if brand == "TBF" else "#1a1a2e"
            accent_color = "#D4A843" if brand == "TBF" else "#ec4899"

            result = {
                "campaign": body,
                "landing_page": {
                    "title": name,
                    "headline": message or f"Experience the Future of Terpenes with {brand_name}",
                    "subheadline": f"Precision-crafted botanical terpene blends featuring {terp_str}",
                    "hero_cta": "Request Sample Kit",
                    "sections": [
                        {"title": f"Why {brand_name}", "content": "Industry-leading purity, consistency, and compliance. Every batch third-party tested. Farm-to-formula traceability."},
                        {"title": "Featured Terpenes", "content": terp_str},
                        {"title": "The Science", "content": "Backed by 400+ peer-reviewed papers. Evidence-graded formulation guidance. Compliance-safe claims."},
                        {"title": "Quality Guarantee", "content": "ISO-certified extraction. Full COA on every batch. Dedicated formulation support."},
                    ],
                    "color_scheme": {"primary": primary_color, "accent": accent_color, "bg": "#FAFAF5" if brand == "TBF" else "#0f0f23"},
                },
                "email_sequence": [
                    {"subject": f"Introducing: {name}", "preview": "The terpene formulation your customers have been asking for",
                     "body_outline": f"Hook: Industry trend + pain point\nValue: What makes {brand_name} different\nProof: Research backing + customer results\nCTA: Schedule a call or request samples"},
                    {"subject": f"The science behind {name}", "preview": "432 papers. One clear conclusion.",
                     "body_outline": f"Lead with research credibility\nHighlight {terp_str} effects\nCompliance-safe framing\nCTA: Download the research brief"},
                    {"subject": f"Last chance: {name} early access", "preview": "Priority pricing expires Friday",
                     "body_outline": "Urgency + exclusivity\nRecap value proposition\nSocial proof\nFinal CTA: Order now"},
                ],
                "figma_status": "Design specifications generated. Connect Figma API token to auto-create designs in your workspace.",
            }
            print(f"  🎨 Campaign generated: {name} ({ctype}, {audience})")
            self._json(result)

        elif path == "/api/reef/outcome":
            action_id = body.get("action_id", "")
            outcome = body.get("outcome", "")
            channel = body.get("channel", "")
            persona = body.get("persona", "")
            playbook = body.get("playbook", "")
            notes = body.get("notes", "")
            emit_event("OutcomeRecorded", {
                "action_id": action_id, "outcome": outcome,
                "channel": channel, "persona": persona,
                "playbook": playbook, "notes": notes,
            })
            print(f"  📝 Outcome: {action_id} → {outcome} ({channel})")
            self._json({"status": "recorded", "action_id": action_id, "outcome": outcome})

        # ── Ontology: Record action ──
        elif path == "/api/ontology/actions":
            action_type = body.get("action_type", "")
            department = body.get("department", "")
            actor = body.get("actor", "system")
            target_ids = body.get("target_ids", [])
            notes = body.get("notes", "")
            if not action_type or not department:
                self._json({"error": "action_type and department required"}, 400)
                return
            action = REGISTRY.record_action(action_type, department, actor, target_ids, notes)
            emit_event("OntologyAction", {"action": action})
            REGISTRY.save()
            self._json({"ontology_version": ONTOLOGY_VERSION, "action": action})

        # ── Ontology: Complete action (triggers workflows) ──
        elif path == "/api/ontology/actions/complete":
            action_id = body.get("action_id", "")
            outcome = body.get("outcome")
            if not action_id:
                self._json({"error": "action_id required"}, 400)
                return
            result = REGISTRY.complete_action(action_id, outcome)
            if result:
                emit_event("OntologyActionCompleted", {"action_id": action_id, "effects": len(result["effects"])})
                REGISTRY.save()
                self._json({"ontology_version": ONTOLOGY_VERSION, **result})
            else:
                self._json({"error": f"Action '{action_id}' not found"}, 404)

        # ── Ontology: Mark notification read ──
        elif path == "/api/ontology/notifications/read":
            notification_id = body.get("notification_id", "")
            department = body.get("department", "")
            if not notification_id or not department:
                self._json({"error": "notification_id and department required"}, 400)
                return
            for n in REGISTRY.notifications:
                if n["id"] == notification_id and department not in n.get("read_by", []):
                    n.setdefault("read_by", []).append(department)
            REGISTRY.save()
            self._json({"status": "ok"})

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

    # Initialize ontology
    _init_ontology()

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

    ont_stats = REGISTRY.stats()

    print(f"\n{'='*55}")
    print(f"  NEXUS PLATFORM SERVER v6")
    print(f"  Schema: {SCHEMA_VERSION}  |  Ontology: {ONTOLOGY_VERSION}")
    print(f"{'='*55}")
    print(f"  UI:       http://localhost:{args.port}/reef")
    print(f"  Snapshot: http://localhost:{args.port}/api/reef/snapshot")
    print(f"  Research: http://localhost:{args.port}/api/reef/research")
    print(f"  Signals:  http://localhost:{args.port}/api/reef/signals")
    print(f"  Ontology: http://localhost:{args.port}/api/ontology")
    print(f"  Events:   http://localhost:{args.port}/api/events")
    print(f"  Agents:   http://localhost:{args.port}/api/agents")
    print(f"  Health:   http://localhost:{args.port}/health")
    print(f"{'='*55}")
    print(f"  Data:")
    print(f"    Output dir:  {OUTPUT_DIR}")
    print(f"    Research KB: {kb_papers} papers")
    print(f"    War Room:    {graph_entities} entities")
    print(f"    Ontology:    {ont_stats['total_objects']} objects, {ont_stats['total_links']} links")
    print(f"    JSX:         {jsx or 'NOT FOUND'}")
    print(f"{'='*55}")
    print(f"  Departments: {', '.join(DEPARTMENTS.keys())}")
    print(f"{'='*55}\n")

    if kb_papers == 0:
        print("  ⚠️  No research papers. Run:")
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
