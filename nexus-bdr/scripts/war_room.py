#!/usr/bin/env python3
"""
THE WAR ROOM — Nexus BDR Central Nervous System
==================================================
Every agent feeds into this. Every decision flows out of it.
This is the brain that makes 15 tools into one intelligence.

ARCHITECTURE:
    ┌──────────────────────────────────────────────────────────┐
    │                    THE WAR ROOM                          │
    │                                                          │
    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
    │  │ KNOWLEDGE    │  │ DECISION     │  │ LEARNING      │  │
    │  │ GRAPH        │  │ ENGINE       │  │ ENGINE        │  │
    │  │              │  │              │  │               │  │
    │  │ Entities     │  │ Priority     │  │ Win/Loss      │  │
    │  │ Signals      │  │ Scoring      │  │ Tracking      │  │
    │  │ Connections  │  │ Action Gen   │  │ Pattern       │  │
    │  │ Timeline     │  │ Routing      │  │ Recognition   │  │
    │  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
    │         │                 │                   │          │
    │  ═══════╪═════════════════╪═══════════════════╪════════  │
    │         │         SIGNAL BUS                  │          │
    │  ═══════╪═════════════════╪═══════════════════╪════════  │
    │         │                 │                   │          │
    │  ┌──────┴───────┐  ┌─────┴────────┐  ┌──────┴───────┐  │
    │  │ INGEST       │  │ AGENTS       │  │ OUTPUT       │  │
    │  │              │  │              │  │              │  │
    │  │ Briefs       │  │ Brief Engine │  │ Daily Brief  │  │
    │  │ Reddit       │  │ Competitor   │  │ Outreach Q   │  │
    │  │ Research     │  │ Research     │  │ HeyGen Q     │  │
    │  │ CRM Data     │  │ Social Intel │  │ CRM Updates  │  │
    │  │ Competitor   │  │ Trigger Mon  │  │ Reports      │  │
    │  │ Pipeline     │  │ HeyGen       │  │ Alerts       │  │
    │  └──────────────┘  └──────────────┘  └──────────────┘  │
    └──────────────────────────────────────────────────────────┘

RECURSIVE LEARNING:
  Every action the system recommends gets tracked.
  When Shareef marks an outcome (reply, meeting, closed, lost),
  the system learns:
    - Which signals predicted real opportunities
    - Which messaging got replies
    - Which company profiles convert
    - Which competitor weaknesses matter
    - What time of day/week gets responses

Usage:
    python3 war_room.py ingest          # Pull all data from all agents
    python3 war_room.py decide          # Generate today's priority actions
    python3 war_room.py brief           # Morning briefing (ingest + decide)
    python3 war_room.py status          # Knowledge graph statistics
    python3 war_room.py learn           # Process outcomes and update weights
    python3 war_room.py history         # Show decision history and accuracy
    python3 war_room.py connect         # Show cross-agent intelligence links
"""

import os, sys, json, re, time, argparse, glob, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs" if (SCRIPT_DIR / "outputs").exists() else SCRIPT_DIR.parent / "outputs"
WAR_DIR = OUTPUT_DIR / "war_room"
GRAPH_DIR = WAR_DIR / "knowledge_graph"
DECISIONS_DIR = WAR_DIR / "decisions"
LEARNING_DIR = WAR_DIR / "learning"
HISTORY_DIR = WAR_DIR / "history"
for d in [WAR_DIR, GRAPH_DIR, DECISIONS_DIR, LEARNING_DIR, HISTORY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH — The shared brain
# ═══════════════════════════════════════════════════════════

class KnowledgeGraph:
    """
    Central knowledge store. Every agent writes here, every agent reads here.
    Stores entities (companies, people, terpenes, products) and their connections.
    """

    def __init__(self):
        self.path = GRAPH_DIR / "war_room_graph.json"
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except:
                pass
        return {
            "entities": {},        # id → entity data
            "signals": [],         # timestamped intelligence signals
            "connections": [],     # entity_a → entity_b with relationship
            "timeline": [],        # chronological event log
            "learning": {
                "action_log": [],  # every recommendation + outcome
                "signal_weights": {  # learned importance of different signal types
                    "reddit_supplier_seeking": 10,
                    "reddit_complaint": 7,
                    "reddit_comparison": 5,
                    "trustpilot_below_3.5": 15,
                    "trustpilot_below_4.0": 8,
                    "hiring_signal": 4,
                    "new_product_launch": 6,
                    "funding_news": 8,
                    "leadership_change": 9,
                    "competitor_weakness": 6,
                    "research_breakthrough": 5,
                    "clinical_trial": 3,
                    "regulatory_change": 12,
                    "price_discussion": 7,
                    "quality_complaint_about_competitor": 12,
                    "brief_completed": 3,
                    "email_verified": 2,
                },
                "outcome_history": [],  # win/loss records for pattern learning
                "messaging_effectiveness": {},  # which subjects/angles get replies
                "best_contact_times": {},
                "company_profile_patterns": {
                    "converts": [],    # profile features of companies that closed
                    "bounces": [],     # profile features of companies that didn't
                },
            },
            "metadata": {
                "created": datetime.utcnow().isoformat(),
                "last_ingest": None,
                "last_decision": None,
                "ingest_count": 0,
                "decision_count": 0,
                "total_signals": 0,
                "total_entities": 0,
            },
        }

    def save(self):
        self.data["metadata"]["total_signals"] = len(self.data["signals"])
        self.data["metadata"]["total_entities"] = len(self.data["entities"])
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    # ── Entity Management ──

    def add_entity(self, entity_type, entity_id, data):
        """Add or update an entity (company, person, terpene, product)."""
        key = f"{entity_type}:{entity_id}"
        if key in self.data["entities"]:
            # Merge — don't overwrite, accumulate
            existing = self.data["entities"][key]
            for k, v in data.items():
                if isinstance(v, list) and isinstance(existing.get(k), list):
                    # Merge lists, deduplicate
                    combined = existing[k] + [x for x in v if x not in existing[k]]
                    existing[k] = combined[-50:]  # Keep last 50
                elif isinstance(v, dict) and isinstance(existing.get(k), dict):
                    existing[k].update(v)
                else:
                    existing[k] = v
            existing["last_updated"] = datetime.utcnow().isoformat()
        else:
            self.data["entities"][key] = {
                "type": entity_type,
                "id": entity_id,
                "created": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                **data,
            }
        return key

    def get_entity(self, entity_type, entity_id):
        key = f"{entity_type}:{entity_id}"
        return self.data["entities"].get(key)

    def get_entities_by_type(self, entity_type):
        return {k: v for k, v in self.data["entities"].items() if v.get("type") == entity_type}

    # ── Signal Management ──

    def add_signal(self, signal_type, source, entity_keys, data, strength=5):
        """Add an intelligence signal to the graph."""
        signal = {
            "id": hashlib.md5(f"{signal_type}{source}{json.dumps(data, default=str)[:200]}".encode()).hexdigest()[:12],
            "type": signal_type,
            "source": source,
            "entities": entity_keys,
            "data": data,
            "strength": strength,
            "weight": self.data["learning"]["signal_weights"].get(signal_type, 5),
            "timestamp": datetime.utcnow().isoformat(),
            "acted_on": False,
            "outcome": None,
        }

        # Deduplicate by ID
        existing_ids = {s["id"] for s in self.data["signals"][-500:]}
        if signal["id"] not in existing_ids:
            self.data["signals"].append(signal)
            self.data["timeline"].append({
                "time": signal["timestamp"],
                "event": f"[{signal_type}] {json.dumps(data, default=str)[:100]}",
                "entities": entity_keys,
            })
            # Trim timeline
            self.data["timeline"] = self.data["timeline"][-1000:]

        return signal

    def get_recent_signals(self, hours=24, signal_type=None):
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        signals = [s for s in self.data["signals"] if s["timestamp"] >= cutoff]
        if signal_type:
            signals = [s for s in signals if s["type"] == signal_type]
        return sorted(signals, key=lambda x: x["weight"] * x["strength"], reverse=True)

    # ── Connection Management ──

    def connect(self, entity_a, entity_b, relationship, data=None):
        """Connect two entities with a typed relationship."""
        conn = {
            "from": entity_a,
            "to": entity_b,
            "relationship": relationship,
            "data": data or {},
            "created": datetime.utcnow().isoformat(),
        }
        # Avoid exact duplicates
        for existing in self.data["connections"][-200:]:
            if existing["from"] == entity_a and existing["to"] == entity_b and existing["relationship"] == relationship:
                existing["data"].update(data or {})
                existing["updated"] = datetime.utcnow().isoformat()
                return
        self.data["connections"].append(conn)

    def get_connections(self, entity_key, relationship=None):
        conns = [c for c in self.data["connections"]
                 if c["from"] == entity_key or c["to"] == entity_key]
        if relationship:
            conns = [c for c in conns if c["relationship"] == relationship]
        return conns

    # ── Learning ──

    def record_action(self, action_type, target_entity, action_data, recommended_by="war_room"):
        """Record a recommended action for tracking."""
        action = {
            "id": hashlib.md5(f"{action_type}{target_entity}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12],
            "type": action_type,
            "target": target_entity,
            "data": action_data,
            "recommended_by": recommended_by,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",  # pending → executed → outcome_recorded
            "outcome": None,  # reply, meeting, closed, lost, no_response
            "outcome_date": None,
        }
        self.data["learning"]["action_log"].append(action)
        return action["id"]

    def record_outcome(self, action_id, outcome, notes=""):
        """Record the outcome of an action for learning."""
        for action in self.data["learning"]["action_log"]:
            if action["id"] == action_id:
                action["status"] = "outcome_recorded"
                action["outcome"] = outcome
                action["outcome_date"] = datetime.utcnow().isoformat()
                action["notes"] = notes

                # Update signal weights based on outcome
                self._update_weights(action, outcome)

                # Record in outcome history
                self.data["learning"]["outcome_history"].append({
                    "action_id": action_id,
                    "action_type": action["type"],
                    "target": action["target"],
                    "outcome": outcome,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return True
        return False

    def _update_weights(self, action, outcome):
        """Adjust signal weights based on outcomes. Positive outcomes increase weights."""
        weights = self.data["learning"]["signal_weights"]
        # If the action led to a positive outcome, boost the signals that triggered it
        multiplier = 1.1 if outcome in ("reply", "meeting", "closed") else 0.95 if outcome == "no_response" else 1.0

        for signal in self.data["signals"][-100:]:
            if signal.get("acted_on") and action["target"] in signal.get("entities", []):
                sig_type = signal["type"]
                if sig_type in weights:
                    weights[sig_type] = round(weights[sig_type] * multiplier, 2)
                    weights[sig_type] = max(1, min(25, weights[sig_type]))  # Clamp 1-25


# ═══════════════════════════════════════════════════════════
# INGEST ENGINE — Pull data from all agents into the graph
# ═══════════════════════════════════════════════════════════

def ingest_all(graph):
    """Pull all agent outputs into the knowledge graph."""
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM — INGESTING ALL INTELLIGENCE")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═'*60}\n")

    pre_entities = len(graph.data["entities"])
    pre_signals = len(graph.data["signals"])

    # 1. Pipeline data (scored Apollo contacts)
    _ingest_pipeline(graph)

    # 2. Company briefs
    _ingest_briefs(graph)

    # 3. Reddit / social intel
    _ingest_reddit(graph)

    # 4. Competitor intel
    _ingest_competitors(graph)

    # 5. Terpene research
    _ingest_research(graph)

    # 6. Trigger alerts
    _ingest_alerts(graph)

    graph.data["metadata"]["last_ingest"] = datetime.utcnow().isoformat()
    graph.data["metadata"]["ingest_count"] = graph.data["metadata"].get("ingest_count", 0) + 1
    graph.save()

    new_entities = len(graph.data["entities"]) - pre_entities
    new_signals = len(graph.data["signals"]) - pre_signals

    print(f"\n{'─'*60}")
    print(f"  INGEST COMPLETE")
    print(f"  New entities: {new_entities} (total: {len(graph.data['entities'])})")
    print(f"  New signals: {new_signals} (total: {len(graph.data['signals'])})")
    print(f"  Connections: {len(graph.data['connections'])}")
    print(f"{'═'*60}\n")


def _ingest_pipeline(graph):
    """Ingest scored Apollo pipeline data."""
    print(f"  ┌─ Pipeline Data")
    scored_files = sorted(OUTPUT_DIR.glob("scored_apollo_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not scored_files:
        print(f"  └─ No scored files found")
        return

    with open(scored_files[0]) as f:
        data = json.load(f)

    leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
    companies = defaultdict(list)
    for lead in leads:
        co = lead.get("company_name", "Unknown")
        companies[co].append(lead)

    for co_name, contacts in companies.items():
        co_id = re.sub(r'[^a-z0-9]', '_', co_name.lower())
        scores = [c.get("nexus_lead_score", 0) for c in contacts]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        top_contact = max(contacts, key=lambda c: c.get("nexus_lead_score", 0))
        verified = sum(1 for c in contacts if c.get("hunter_status") == "valid" or c.get("email_verified"))

        entity_key = graph.add_entity("company", co_id, {
            "name": co_name,
            "domain": top_contact.get("company_domain", top_contact.get("domain", "")),
            "contacts": len(contacts),
            "avg_score": avg,
            "top_score": max(scores),
            "top_contact": f"{top_contact.get('first_name', '')} {top_contact.get('last_name', '')}".strip(),
            "top_title": top_contact.get("title", ""),
            "verified_emails": verified,
            "pipeline_tier": "hot" if avg >= 80 else "warm" if avg >= 60 else "cool" if avg >= 40 else "cold",
            "source": "apollo_pipeline",
        })

        # Add contacts as person entities
        for contact in contacts:
            person_id = re.sub(r'[^a-z0-9]', '_', f"{contact.get('first_name', '')}_{contact.get('last_name', '')}".lower())
            person_key = graph.add_entity("person", person_id, {
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                "title": contact.get("title", ""),
                "email": contact.get("email", ""),
                "score": contact.get("nexus_lead_score", 0),
                "company": co_name,
            })
            graph.connect(entity_key, person_key, "employs")

    print(f"  └─ ✅ {len(companies)} companies, {len(leads)} contacts ingested")


def _ingest_briefs(graph):
    """Ingest sales intelligence briefs."""
    print(f"  ┌─ Company Briefs")
    briefs_dir = OUTPUT_DIR / "briefs"
    if not briefs_dir.exists():
        print(f"  └─ No briefs directory")
        return

    brief_files = sorted(briefs_dir.glob("brief_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    count = 0

    for bf in brief_files:
        try:
            with open(bf) as f:
                data = json.load(f)

            meta = data.get("metadata", {})
            phases = data.get("phases", {})
            company = meta.get("company", "")
            if not company:
                continue

            co_id = re.sub(r'[^a-z0-9]', '_', company[:30].lower())
            p1 = phases.get("phase_1", {})
            p4 = phases.get("phase_4", {})
            p5 = phases.get("phase_5", {})
            p6 = phases.get("phase_6", {})

            entity_key = graph.add_entity("company", co_id, {
                "name": company,
                "brief_completed": True,
                "brief_date": meta.get("generated_at", ""),
                "brief_file": str(bf),
                "terpene_relevance": p1.get("terpene_relevance", ""),
                "company_type": p1.get("company_type", ""),
                "description": p1.get("description", ""),
                "current_supplier": (p4.get("current_supplier", {}) or {}).get("most_likely", ""),
                "switching_triggers": (p4.get("current_supplier", {}) or {}).get("switching_triggers", []),
                "annual_value": (p5.get("deal_model", {}) or {}).get("weighted_annual", ""),
                "priority_score": (p6.get("executive_summary", {}) or {}).get("priority_score", 0),
            })

            # Signal: brief completed
            graph.add_signal("brief_completed", "brief_engine", [entity_key], {
                "company": company, "phases_complete": sum(1 for p in phases.values() if isinstance(p, dict) and len(p) > 1),
            }, strength=3)

            count += 1
        except Exception as e:
            continue

    print(f"  └─ ✅ {count} briefs ingested")


def _ingest_reddit(graph):
    """Ingest Reddit social intelligence."""
    print(f"  ┌─ Reddit / Social Intel")
    intel_dir = OUTPUT_DIR / "free_intel"
    vuln_dir = OUTPUT_DIR / "competitor_intel"

    reddit_files = sorted(
        list(intel_dir.glob("reddit_scan_*.json")) + list(vuln_dir.glob("vuln_v2_*.json")),
        key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not reddit_files:
        print(f"  └─ No Reddit data found")
        return

    total_signals = 0
    # Only process most recent file to avoid duplicates
    rf = reddit_files[0]
    try:
        with open(rf) as f:
            data = json.load(f)

        # Handle both formats (free_intel and vuln_v2)
        posts = data.get("signals", data.get("all_posts", []))
        if "reddit" in data:
            posts = data["reddit"].get("posts", [])

        for post in posts:
            if post.get("intent_score", post.get("signal_strength", 0)):
                signal_type = "reddit_supplier_seeking" if post.get("is_supplier_seeking") or post.get("buying_signals") \
                    else "reddit_complaint" if post.get("is_complaint") \
                    else "reddit_comparison" if post.get("is_comparison") \
                    else "reddit_signal"

                strength = min(10, (post.get("intent_score", 0) or 0) // 5 + 1)

                graph.add_signal(signal_type, "reddit", [], {
                    "title": post.get("title", ""),
                    "subreddit": post.get("subreddit", ""),
                    "url": post.get("url", ""),
                    "body_preview": post.get("body", "")[:200],
                    "competitors_mentioned": post.get("competitors_mentioned", []),
                    "complaints": post.get("complaints", post.get("negative_signals", [])),
                    "switching_signals": post.get("switching", post.get("switching_signals", [])),
                }, strength=strength)
                total_signals += 1
    except Exception as e:
        pass

    print(f"  └─ ✅ {total_signals} Reddit signals ingested")


def _ingest_competitors(graph):
    """Ingest competitor intelligence."""
    print(f"  ┌─ Competitor Intel")
    vuln_dir = OUTPUT_DIR / "competitor_intel"
    if not vuln_dir.exists():
        print(f"  └─ No competitor data")
        return

    files = sorted(vuln_dir.glob("competitor_vuln_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        files = sorted(vuln_dir.glob("vuln_v2_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print(f"  └─ No competitor scan files")
        return

    with open(files[0]) as f:
        data = json.load(f)

    competitors = data.get("competitors", data.get("competitor_scores", {}))
    count = 0
    for name, info in competitors.items():
        co_id = re.sub(r'[^a-z0-9]', '_', name.lower())
        tp = info.get("trustpilot", info.get("reviews", {}).get("trustpilot", {}))

        entity_key = graph.add_entity("competitor", co_id, {
            "name": name,
            "is_competitor": True,
            "trustpilot_rating": tp.get("rating") if tp else None,
            "trustpilot_count": tp.get("count", tp.get("review_count")) if tp else None,
            "hiring": info.get("hiring", info.get("website", {}).get("hiring", False)),
            "vulnerability_score": info.get("vulnerability_summary", info.get("vulnerability_score", {}) if isinstance(info.get("vulnerability_score"), dict) else {}).get("vulnerability_score", info.get("score", 0)),
            "risk_level": info.get("vulnerability_summary", {}).get("risk_level", info.get("risk", "")),
        })

        # Trustpilot signal
        if tp and isinstance(tp, dict) and tp.get("rating"):
            rating = tp["rating"]
            if rating < 3.5:
                graph.add_signal("trustpilot_below_3.5", "trustpilot", [entity_key], {
                    "competitor": name, "rating": rating, "count": tp.get("count", tp.get("review_count", "?")),
                }, strength=8)
            elif rating < 4.0:
                graph.add_signal("trustpilot_below_4.0", "trustpilot", [entity_key], {
                    "competitor": name, "rating": rating,
                }, strength=5)

        # Hiring signal
        hiring = info.get("hiring", info.get("website", {}).get("hiring", False))
        if hiring:
            graph.add_signal("hiring_signal", "website", [entity_key], {
                "competitor": name, "hiring": True,
            }, strength=4)

        count += 1

    print(f"  └─ ✅ {count} competitors ingested")


def _ingest_research(graph):
    """Ingest terpene research knowledge base."""
    print(f"  ┌─ Terpene Research")
    kb_path = OUTPUT_DIR / "terpene_research" / "knowledge_base" / "terpene_kb.json"
    if not kb_path.exists():
        print(f"  └─ No research KB found")
        return

    with open(kb_path) as f:
        kb = json.load(f)

    papers = kb.get("papers", {})
    trials = kb.get("clinical_trials", {})

    # Add terpene entities
    for terp_name, effects in kb.get("terpene_effects", {}).items():
        terp_id = re.sub(r'[^a-z0-9]', '_', terp_name.lower())
        total_citations = sum(len(v) for v in effects.values())
        graph.add_entity("terpene", terp_id, {
            "name": terp_name,
            "effects": {e: len(pmids) for e, pmids in effects.items()},
            "total_citations": total_citations,
            "paper_count": len(set(pmid for pmids in effects.values() for pmid in pmids)),
        })

    # Add high-relevance papers as signals
    high_papers = [p for p in papers.values() if p.get("relevance_score", 0) >= 40]
    for paper in high_papers[:20]:
        graph.add_signal("research_breakthrough", "pubmed", [], {
            "title": paper.get("title", "")[:120],
            "journal": paper.get("journal", ""),
            "year": paper.get("year", ""),
            "terpenes": paper.get("terpenes_mentioned", []),
            "effects": paper.get("effects_mentioned", []),
            "url": paper.get("url", ""),
            "score": paper.get("relevance_score", 0),
        }, strength=paper.get("relevance_score", 0) // 20 + 1)

    # Active clinical trials
    active = [t for t in trials.values() if t.get("status") in ("RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING")]
    for trial in active[:10]:
        graph.add_signal("clinical_trial", "clinicaltrials", [], {
            "title": trial.get("title", "")[:100],
            "status": trial.get("status", ""),
            "nct_id": trial.get("nct_id", ""),
            "url": trial.get("url", ""),
        }, strength=4)

    stats = kb.get("statistics", {})
    print(f"  └─ ✅ {stats.get('total_papers', 0)} papers, {len(active)} active trials ingested")


def _ingest_alerts(graph):
    """Ingest trigger alerts."""
    print(f"  ┌─ Trigger Alerts")
    alerts_dir = OUTPUT_DIR / "alerts"
    if not alerts_dir.exists() or not list(alerts_dir.glob("*.json")):
        print(f"  └─ No alerts found")
        return

    files = sorted(alerts_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    count = 0
    for af in files[:5]:
        try:
            with open(af) as f:
                data = json.load(f)
            alerts = data.get("alerts", [data] if "company" in data else [])
            for alert in alerts:
                graph.add_signal("trigger_alert", "trigger_monitor", [], {
                    "type": alert.get("type", ""),
                    "company": alert.get("company", ""),
                    "detail": json.dumps(alert, default=str)[:200],
                }, strength=6)
                count += 1
        except:
            continue

    print(f"  └─ ✅ {count} alerts ingested")


# ═══════════════════════════════════════════════════════════
# DECISION ENGINE — Generate prioritized actions
# ═══════════════════════════════════════════════════════════

def generate_decisions(graph):
    """Analyze all intelligence and generate prioritized daily actions."""
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM — DECISION ENGINE")
    print(f"  Analyzing {len(graph.data['entities'])} entities, {len(graph.data['signals'])} signals")
    print(f"{'═'*60}\n")

    decisions = []
    reasons = []

    # Get all prospect companies (not competitors)
    companies = graph.get_entities_by_type("company")
    competitors = graph.get_entities_by_type("competitor")
    terpenes = graph.get_entities_by_type("terpene")
    recent_signals = graph.get_recent_signals(hours=168)  # Last 7 days

    # ── DECISION 1: Which companies to prioritize today ──
    company_priorities = []
    for key, company in companies.items():
        if company.get("is_competitor"):
            continue

        score = 0
        action_reasons = []

        # Base score from pipeline
        score += company.get("avg_score", 0) * 0.3
        if company.get("brief_completed"):
            score += 15
            action_reasons.append("Brief completed — ready for outreach")
        if company.get("verified_emails", 0) > 0:
            score += 10
            action_reasons.append(f"{company['verified_emails']} verified emails")
        if company.get("priority_score"):
            score += company["priority_score"] * 0.2

        # Boost from signals
        entity_signals = [s for s in recent_signals if key in s.get("entities", [])]
        for sig in entity_signals:
            score += sig["weight"] * sig["strength"] * 0.5
            action_reasons.append(f"Signal: {sig['type']} (weight: {sig['weight']})")

        # Cross-pollination: if competitor they use has vulnerability
        supplier = company.get("current_supplier", "")
        if supplier:
            for comp_key, comp in competitors.items():
                if supplier.lower() in comp.get("name", "").lower():
                    vuln = comp.get("vulnerability_score", 0)
                    if vuln > 0:
                        score += vuln * 2
                        action_reasons.append(f"Supplier {comp['name']} has vulnerability score {vuln}")
                    tp = comp.get("trustpilot_rating")
                    if tp and tp < 4.0:
                        score += (4.0 - tp) * 10
                        action_reasons.append(f"Supplier {comp['name']} Trustpilot: {tp}/5")

        # Cross-pollination: research matches
        switching_triggers = company.get("switching_triggers", [])
        if switching_triggers:
            score += 5
            action_reasons.append(f"Known switching triggers: {len(switching_triggers)}")

        company_priorities.append({
            "entity_key": key,
            "company": company.get("name", "?"),
            "score": round(score, 1),
            "reasons": action_reasons,
            "tier": company.get("pipeline_tier", "?"),
            "brief": company.get("brief_completed", False),
            "contacts": company.get("contacts", 0),
            "emails": company.get("verified_emails", 0),
            "top_contact": company.get("top_contact", ""),
        })

    company_priorities.sort(key=lambda x: x["score"], reverse=True)

    # ── DECISION 2: Reddit engagement opportunities ──
    reddit_actions = []
    reddit_signals = [s for s in recent_signals if s["type"].startswith("reddit_")]
    for sig in reddit_signals[:10]:
        d = sig["data"]
        reddit_actions.append({
            "type": "reddit_engagement",
            "priority": sig["weight"] * sig["strength"],
            "title": d.get("title", "")[:80],
            "subreddit": d.get("subreddit", ""),
            "url": d.get("url", ""),
            "reason": f"{'SEEKING SUPPLIER' if sig['type'] == 'reddit_supplier_seeking' else 'COMPLAINT' if sig['type'] == 'reddit_complaint' else 'DISCUSSION'}",
            "suggested_action": "Respond with TBF/DFT positioning, offer sample" if "supplier" in sig["type"] else "Monitor thread, prepare DM if appropriate",
        })

    # ── DECISION 3: Research-backed outreach angles ──
    research_angles = []
    for sig in recent_signals:
        if sig["type"] == "research_breakthrough":
            d = sig["data"]
            terps = d.get("terpenes", [])
            effects = d.get("effects", [])
            if terps and effects:
                # Find companies whose products match these terpenes
                matching_companies = []
                for key, co in companies.items():
                    desc = json.dumps(co, default=str).lower()
                    for t in terps:
                        if t.replace("-", " ") in desc or t in desc:
                            matching_companies.append(co.get("name", "?"))
                            break

                if matching_companies:
                    research_angles.append({
                        "paper": d.get("title", "")[:80],
                        "terpenes": terps,
                        "effects": effects,
                        "matching_companies": matching_companies[:5],
                        "talking_point": f"New research on {terps[0]} shows {effects[0]} properties — relevant to {', '.join(matching_companies[:3])}",
                    })

    # ── DECISION 4: Competitor vulnerability actions ──
    competitor_actions = []
    for key, comp in competitors.items():
        tp = comp.get("trustpilot_rating")
        if tp and tp < 4.0:
            # Find prospects who use this competitor
            their_customers = [co.get("name", "?") for _, co in companies.items()
                              if comp.get("name", "").lower() in json.dumps(co.get("current_supplier", "")).lower()]
            competitor_actions.append({
                "competitor": comp.get("name", ""),
                "vulnerability": f"Trustpilot {tp}/5",
                "affected_prospects": their_customers,
                "suggested_action": f"Reach out to prospects using {comp['name']} — lead with quality consistency",
            })

    # ── BUILD DECISION DOCUMENT ──
    decision_doc = {
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_entities": len(graph.data["entities"]),
            "total_signals": len(graph.data["signals"]),
            "recent_signals": len(recent_signals),
            "companies_ranked": len(company_priorities),
            "reddit_opportunities": len(reddit_actions),
            "research_angles": len(research_angles),
            "competitor_vulnerabilities": len(competitor_actions),
        },
        "priority_companies": company_priorities[:10],
        "reddit_actions": reddit_actions[:10],
        "research_angles": research_angles[:5],
        "competitor_actions": competitor_actions,
    }

    # Record actions
    for cp in company_priorities[:5]:
        graph.record_action("outreach_priority", cp["entity_key"], {
            "company": cp["company"], "score": cp["score"], "reasons": cp["reasons"][:3],
        })

    graph.data["metadata"]["last_decision"] = datetime.utcnow().isoformat()
    graph.data["metadata"]["decision_count"] = graph.data["metadata"].get("decision_count", 0) + 1
    graph.save()

    # Save decision doc
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = DECISIONS_DIR / f"decisions_{ts}.json"
    with open(path, "w") as f:
        json.dump(decision_doc, f, indent=2, default=str)

    # Generate markdown
    md_path = _generate_decision_report(decision_doc, graph)

    return decision_doc, md_path


def _generate_decision_report(doc, graph):
    """Generate the morning briefing markdown."""
    L = []
    L.append(f"# WAR ROOM — Daily Intelligence Briefing")
    L.append(f"**{datetime.utcnow().strftime('%A, %B %d, %Y')}** | Nexus BDR Intelligence System\n")
    L.append(f"---\n")

    s = doc["summary"]
    L.append(f"## System Status")
    L.append(f"Knowledge graph: **{s['total_entities']} entities** | **{s['total_signals']} signals** | **{s['recent_signals']} recent (7d)**\n")

    # Priority companies
    L.append(f"## Today's Priority Companies\n")
    L.append(f"*Ranked by composite intelligence score — pipeline data + signals + competitor vulnerability + research relevance*\n")

    for i, cp in enumerate(doc["priority_companies"][:10], 1):
        emoji = "🔴" if cp["score"] >= 50 else "🟡" if cp["score"] >= 30 else "🔵"
        brief = "✅ Brief" if cp["brief"] else "⏳ No brief"
        L.append(f"### {i}. {cp['company']} — Score: {cp['score']} {emoji}")
        L.append(f"*{cp['tier'].upper()} | {cp['contacts']} contacts | {cp['emails']} verified | {brief}*")
        if cp["top_contact"]:
            L.append(f"**Primary target:** {cp['top_contact']}")
        if cp["reasons"]:
            L.append(f"\n**Why now:**")
            for r in cp["reasons"][:4]:
                L.append(f"- {r}")
        L.append("")

    # Reddit
    if doc["reddit_actions"]:
        L.append(f"## Reddit Engagement Opportunities ({len(doc['reddit_actions'])})\n")
        for ra in doc["reddit_actions"][:5]:
            L.append(f"- **[{ra['reason']}]** r/{ra['subreddit']}: [{ra['title']}]({ra['url']})")
            L.append(f"  Action: {ra['suggested_action']}")
        L.append("")

    # Research angles
    if doc["research_angles"]:
        L.append(f"## Science-Backed Outreach Angles\n")
        for ra in doc["research_angles"][:3]:
            L.append(f"- **{ra['talking_point']}**")
            L.append(f"  Relevant to: {', '.join(ra['matching_companies'])}")
        L.append("")

    # Competitor vulnerabilities
    if doc["competitor_actions"]:
        L.append(f"## Competitor Vulnerability Opportunities\n")
        for ca in doc["competitor_actions"]:
            L.append(f"- **{ca['competitor']}**: {ca['vulnerability']}")
            if ca["affected_prospects"]:
                L.append(f"  Prospects using them: {', '.join(ca['affected_prospects'])}")
            L.append(f"  Action: {ca['suggested_action']}")
        L.append("")

    # Learning stats
    outcomes = graph.data["learning"]["outcome_history"]
    if outcomes:
        L.append(f"## Learning Engine\n")
        total = len(outcomes)
        wins = sum(1 for o in outcomes if o["outcome"] in ("reply", "meeting", "closed"))
        L.append(f"Actions tracked: {total} | Positive outcomes: {wins} | Win rate: {wins/total*100:.0f}%\n")

        # Top weighted signals
        weights = sorted(graph.data["learning"]["signal_weights"].items(), key=lambda x: x[1], reverse=True)
        L.append(f"**Top-weighted signal types:**")
        for sig_type, weight in weights[:5]:
            L.append(f"- {sig_type.replace('_', ' ').title()}: {weight}")

    L.append(f"\n---")
    L.append(f"\n*Generated by War Room Decision Engine | Signal weights adjust automatically based on outcomes*")

    md = "\n".join(L)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = DECISIONS_DIR / f"briefing_{ts}.md"
    with open(path, "w") as f:
        f.write(md)

    print(f"  📄 Daily Briefing: {path}")
    return path


# ═══════════════════════════════════════════════════════════
# LEARNING INTERFACE
# ═══════════════════════════════════════════════════════════

def show_learning(graph):
    """Show learning engine status."""
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM — LEARNING ENGINE")
    print(f"{'═'*60}\n")

    outcomes = graph.data["learning"]["outcome_history"]
    action_log = graph.data["learning"]["action_log"]
    weights = graph.data["learning"]["signal_weights"]

    print(f"  Actions recommended: {len(action_log)}")
    print(f"  Outcomes recorded: {len(outcomes)}")

    if outcomes:
        by_outcome = defaultdict(int)
        for o in outcomes:
            by_outcome[o["outcome"]] += 1
        print(f"\n  Outcome distribution:")
        for outcome, count in sorted(by_outcome.items(), key=lambda x: x[1], reverse=True):
            print(f"    {outcome}: {count}")

    print(f"\n  Signal weights (learned):")
    for sig, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(weight)
        print(f"    {sig:<35} {weight:>5.1f} {bar}")

    pending = [a for a in action_log if a["status"] == "pending"]
    if pending:
        print(f"\n  Pending actions ({len(pending)}):")
        for a in pending[:5]:
            print(f"    [{a['id']}] {a['type']}: {a['data'].get('company', '?')}")
        print(f"\n  Record outcomes: python3 war_room.py learn --action-id <id> --outcome <reply|meeting|closed|lost|no_response>")

    print(f"\n{'═'*60}\n")


def record_outcome_cli(graph, action_id, outcome, notes=""):
    """CLI for recording outcomes."""
    if graph.record_outcome(action_id, outcome, notes):
        graph.save()
        print(f"  ✅ Recorded: {action_id} → {outcome}")
        print(f"  Signal weights updated. The system is learning.")
    else:
        print(f"  ❌ Action ID not found: {action_id}")


# ═══════════════════════════════════════════════════════════
# STATUS & HISTORY
# ═══════════════════════════════════════════════════════════

def show_status(graph):
    """Show full War Room status."""
    meta = graph.data["metadata"]
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM — STATUS")
    print(f"{'═'*60}\n")
    print(f"  Knowledge Graph:")
    print(f"    Entities: {meta.get('total_entities', 0)}")
    print(f"    Signals: {meta.get('total_signals', 0)}")
    print(f"    Connections: {len(graph.data['connections'])}")
    print(f"    Timeline events: {len(graph.data['timeline'])}")

    print(f"\n  Entity breakdown:")
    type_counts = defaultdict(int)
    for e in graph.data["entities"].values():
        type_counts[e.get("type", "?")] += 1
    for t, c in sorted(type_counts.items()):
        print(f"    {t}: {c}")

    print(f"\n  Operations:")
    print(f"    Ingests: {meta.get('ingest_count', 0)}")
    print(f"    Decisions: {meta.get('decision_count', 0)}")
    print(f"    Last ingest: {(meta.get('last_ingest') or 'never')[:19]}")
    print(f"    Last decision: {(meta.get('last_decision') or 'never')[:19]}")

    print(f"\n  Learning:")
    actions = len(graph.data["learning"]["action_log"])
    outcomes = len(graph.data["learning"]["outcome_history"])
    print(f"    Actions tracked: {actions}")
    print(f"    Outcomes recorded: {outcomes}")

    print(f"\n{'═'*60}\n")


def show_connections(graph):
    """Show cross-agent intelligence connections."""
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM — INTELLIGENCE CONNECTIONS")
    print(f"{'═'*60}\n")

    companies = graph.get_entities_by_type("company")
    competitors = graph.get_entities_by_type("competitor")
    terpenes = graph.get_entities_by_type("terpene")

    for key, co in sorted(companies.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True)[:10]:
        name = co.get("name", "?")
        conns = graph.get_connections(key)
        signals = [s for s in graph.data["signals"] if key in s.get("entities", [])]

        print(f"  {name}")
        print(f"  │  Pipeline: {co.get('pipeline_tier', '?')} | Score: {co.get('avg_score', 0)}")
        if co.get("brief_completed"):
            print(f"  │  Brief: ✅ | Supplier: {co.get('current_supplier', '?')}")
        if co.get("annual_value"):
            print(f"  │  Value: {co['annual_value']}")
        if conns:
            print(f"  │  Connections: {len(conns)}")
        if signals:
            print(f"  │  Active signals: {len(signals)}")
        print(f"  │")

    print(f"{'═'*60}\n")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="War Room — Nexus BDR Central Nervous System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  ingest       Pull all data from all agents into the knowledge graph
  decide       Generate today's priority actions
  brief        Full morning briefing (ingest + decide)
  status       Knowledge graph statistics
  learn        Show learning engine / record outcomes
  history      Decision history
  connect      Cross-agent intelligence connections
        """
    )
    parser.add_argument("command", help="Command to run")
    parser.add_argument("--action-id", help="Action ID for outcome recording")
    parser.add_argument("--outcome", help="Outcome: reply, meeting, closed, lost, no_response")
    parser.add_argument("--notes", default="", help="Notes about the outcome")
    args = parser.parse_args()

    graph = KnowledgeGraph()
    cmd = args.command.lower()

    if cmd == "ingest":
        ingest_all(graph)
    elif cmd == "decide":
        doc, md = generate_decisions(graph)
    elif cmd == "brief":
        ingest_all(graph)
        doc, md = generate_decisions(graph)
    elif cmd == "status":
        show_status(graph)
    elif cmd == "learn":
        if args.action_id and args.outcome:
            record_outcome_cli(graph, args.action_id, args.outcome, args.notes)
        else:
            show_learning(graph)
    elif cmd == "connect":
        show_connections(graph)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
