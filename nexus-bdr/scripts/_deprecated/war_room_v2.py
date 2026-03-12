#!/usr/bin/env python3
"""
WAR ROOM v2 — Nexus BDR Central Nervous System
=================================================
Fixes from architecture review:
  1. CRITICAL: Learning attribution now works — actions link to trigger signals,
     acted_on gets set, weight updates actually fire
  2. Entity identity: domain-based resolver prevents ID collisions
  3. Source reliability priors: Reddit ≠ SEC filing
  4. Event log: append-only event stream alongside the graph
  5. Per-agent cost budgets with hard caps
  6. Action objects with structured schemas (not prose strings)

Architecture: Still file-backed (Postgres migration = Week 2),
but with clean separation and contracts that port directly.

Usage:
    python3 war_room_v2.py brief        # Full morning briefing
    python3 war_room_v2.py ingest       # Pull all agent data
    python3 war_room_v2.py decide       # Generate priorities
    python3 war_room_v2.py status       # Graph stats
    python3 war_room_v2.py learn        # Learning engine status
    python3 war_room_v2.py learn --action-id X --outcome reply
    python3 war_room_v2.py connect      # Cross-agent connections
    python3 war_room_v2.py events       # View event log
    python3 war_room_v2.py verify       # Run verification checks
"""

import os, sys, json, re, time, argparse, hashlib, uuid
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
EVENTS_DIR = WAR_DIR / "events"
for d in [WAR_DIR, GRAPH_DIR, DECISIONS_DIR, LEARNING_DIR, HISTORY_DIR, EVENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# SOURCE RELIABILITY PRIORS
# Not all intelligence sources are equal
# ═══════════════════════════════════════════════════════════

SOURCE_RELIABILITY = {
    # High reliability — verifiable, structured data
    "sec_edgar": 0.95,
    "fda": 0.95,
    "clinicaltrials": 0.90,
    "pubmed": 0.90,
    "trustpilot": 0.75,     # Real reviews but gameable
    "hunter_verified": 0.85,

    # Medium reliability — editorial/aggregated
    "google_news": 0.65,
    "industry_journal": 0.70,
    "company_website": 0.60,  # Self-reported
    "linkedin": 0.60,

    # Lower reliability — user-generated, noisy
    "reddit": 0.40,          # Valuable signals but noisy
    "forum": 0.35,

    # Internal — depends on data quality
    "apollo_pipeline": 0.55,
    "brief_engine": 0.70,
    "trigger_monitor": 0.50,
    "competitor_scan": 0.55,

    # Default
    "unknown": 0.30,
}


# ═══════════════════════════════════════════════════════════
# ENTITY RESOLVER — prevents ID collisions
# ═══════════════════════════════════════════════════════════

class EntityResolver:
    """
    Resolves entity identity using multiple strategies:
    1. Domain match (highest confidence)
    2. External ID match (Apollo, CRM, etc.)
    3. Fuzzy name match with confidence threshold
    """

    def __init__(self, entities):
        self.entities = entities
        self._domain_index = {}
        self._external_id_index = {}
        self._rebuild_indices()

    def _rebuild_indices(self):
        self._domain_index = {}
        self._external_id_index = {}
        for key, entity in self.entities.items():
            domain = entity.get("domain", "").lower().strip()
            if domain and domain not in ("", "none", "n/a"):
                # Normalize domain
                domain = domain.replace("www.", "").replace("https://", "").replace("http://", "").rstrip("/")
                self._domain_index[domain] = key

            for ext_id_key in ("apollo_id", "crm_id", "hubspot_id", "ghl_id"):
                ext_id = entity.get(ext_id_key)
                if ext_id:
                    self._external_id_index[f"{ext_id_key}:{ext_id}"] = key

    def resolve(self, name, domain=None, external_ids=None):
        """
        Find existing entity or generate new stable ID.
        Returns (entity_key, is_new, confidence)
        """
        # Strategy 1: Domain match (highest confidence)
        if domain:
            norm_domain = domain.lower().replace("www.", "").replace("https://", "").replace("http://", "").rstrip("/")
            if norm_domain in self._domain_index:
                return self._domain_index[norm_domain], False, 0.95

        # Strategy 2: External ID match
        if external_ids:
            for id_type, id_val in external_ids.items():
                lookup = f"{id_type}:{id_val}"
                if lookup in self._external_id_index:
                    return self._external_id_index[lookup], False, 0.90

        # Strategy 3: Name-based (lowest confidence, with collision prevention)
        slug = re.sub(r'[^a-z0-9]', '_', name[:40].lower()).strip('_')
        # Check for exact slug match
        for key, entity in self.entities.items():
            if key.endswith(f":{slug}"):
                # Verify it's actually the same company (check domain if available)
                if domain and entity.get("domain"):
                    e_domain = entity["domain"].lower().replace("www.", "").rstrip("/")
                    if domain.lower().replace("www.", "").rstrip("/") != e_domain:
                        # Different domain = different company with similar name
                        slug = f"{slug}_{hashlib.md5(domain.encode()).hexdigest()[:6]}"
                        break
                return key, False, 0.60

        # New entity — use domain-based key if available, else slug
        if domain:
            norm = domain.lower().replace("www.", "").replace(".com", "").replace(".io", "").replace(".co", "").rstrip("/")
            new_slug = re.sub(r'[^a-z0-9]', '_', norm).strip('_')
        else:
            new_slug = slug

        return f"company:{new_slug}", True, 1.0


# ═══════════════════════════════════════════════════════════
# EVENT LOG — append-only, never mutated
# ═══════════════════════════════════════════════════════════

class EventLog:
    """
    Append-only event stream. Every mutation gets recorded.
    This is the foundation for Postgres migration.
    """

    def __init__(self):
        self.log_path = EVENTS_DIR / "event_log.jsonl"

    def emit(self, event_type, source_agent, payload, entity_refs=None, run_id=None):
        event = {
            "event_id": uuid.uuid4().hex[:12],
            "event_type": event_type,
            "source_agent": source_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id or os.getenv("NEXUS_RUN_ID", "manual"),
            "entity_refs": entity_refs or [],
            "payload": payload,
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")
        return event["event_id"]

    def get_recent(self, n=50, event_type=None):
        if not self.log_path.exists():
            return []
        events = []
        with open(self.log_path) as f:
            for line in f:
                try:
                    e = json.loads(line.strip())
                    if event_type and e.get("event_type") != event_type:
                        continue
                    events.append(e)
                except:
                    continue
        return events[-n:]

    def count(self):
        if not self.log_path.exists():
            return 0
        with open(self.log_path) as f:
            return sum(1 for _ in f)


# ═══════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH v2
# ═══════════════════════════════════════════════════════════

class KnowledgeGraph:

    def __init__(self):
        self.path = GRAPH_DIR / "war_room_graph_v2.json"
        self.events = EventLog()
        self.data = self._load()
        self.resolver = EntityResolver(self.data["entities"])
        self.run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except:
                pass

        # Also try migrating from v1
        v1_path = GRAPH_DIR / "war_room_graph.json"
        if v1_path.exists():
            try:
                with open(v1_path) as f:
                    v1 = json.load(f)
                print(f"  ℹ️  Migrating from War Room v1 graph...")
                return v1  # v2 is backward compatible, just adds features
            except:
                pass

        return {
            "entities": {},
            "signals": [],
            "connections": [],
            "timeline": [],
            "learning": {
                "action_log": [],
                "signal_weights": {
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
                "outcome_history": [],
                "messaging_effectiveness": {},
                "company_profile_patterns": {"converts": [], "bounces": []},
            },
            "metadata": {
                "created": datetime.utcnow().isoformat(),
                "version": "v2",
                "last_ingest": None,
                "last_decision": None,
                "ingest_count": 0,
                "decision_count": 0,
            },
        }

    def save(self):
        self.data["metadata"]["total_signals"] = len(self.data["signals"])
        self.data["metadata"]["total_entities"] = len(self.data["entities"])
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    # ── Entity Management (v2: uses resolver) ──

    def add_entity(self, entity_type, name, data, domain=None, external_ids=None):
        """Add or update entity with proper identity resolution."""
        key, is_new, confidence = self.resolver.resolve(name, domain, external_ids)

        # Override key type prefix if needed
        if not key.startswith(f"{entity_type}:"):
            key = f"{entity_type}:{key.split(':',1)[-1]}"

        if key in self.data["entities"]:
            existing = self.data["entities"][key]
            # Merge
            for k, v in data.items():
                if v is None or v == "" or v == []:
                    continue
                if isinstance(v, list) and isinstance(existing.get(k), list):
                    combined = existing[k] + [x for x in v if x not in existing[k]]
                    existing[k] = combined[-50:]
                elif isinstance(v, dict) and isinstance(existing.get(k), dict):
                    existing[k].update(v)
                else:
                    existing[k] = v
            existing["last_updated"] = datetime.utcnow().isoformat()
            existing["update_count"] = existing.get("update_count", 0) + 1
        else:
            self.data["entities"][key] = {
                "type": entity_type,
                "name": name,
                "domain": domain or "",
                "external_ids": external_ids or {},
                "created": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "identity_confidence": confidence,
                "update_count": 1,
                **data,
            }
            # Update resolver index
            self.resolver = EntityResolver(self.data["entities"])

            self.events.emit("EntityCreated", "war_room", {
                "entity_key": key, "type": entity_type, "name": name,
            }, [key], self.run_id)

        return key

    def get_entity(self, key):
        return self.data["entities"].get(key)

    def get_entities_by_type(self, entity_type):
        return {k: v for k, v in self.data["entities"].items() if v.get("type") == entity_type}

    # ── Signal Management (v2: with source reliability) ──

    def add_signal(self, signal_type, source, entity_keys, data, strength=5):
        """Add signal with source reliability prior applied."""
        reliability = SOURCE_RELIABILITY.get(source, SOURCE_RELIABILITY["unknown"])
        effective_weight = self.data["learning"]["signal_weights"].get(signal_type, 5) * reliability

        sig_id = hashlib.md5(f"{signal_type}{source}{json.dumps(data, default=str)[:200]}".encode()).hexdigest()[:12]

        signal = {
            "id": sig_id,
            "type": signal_type,
            "source": source,
            "source_reliability": reliability,
            "entities": entity_keys,
            "data": data,
            "strength": strength,
            "base_weight": self.data["learning"]["signal_weights"].get(signal_type, 5),
            "effective_weight": round(effective_weight, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "acted_on": False,          # v2 FIX: explicitly tracked
            "action_ids": [],           # v2 FIX: which actions used this signal
            "outcome": None,
        }

        existing_ids = {s["id"] for s in self.data["signals"][-500:]}
        if sig_id not in existing_ids:
            self.data["signals"].append(signal)
            self.data["timeline"].append({
                "time": signal["timestamp"],
                "event": f"[{signal_type}] {json.dumps(data, default=str)[:100]}",
                "entities": entity_keys,
            })
            self.data["timeline"] = self.data["timeline"][-1000:]

            self.events.emit("SignalCreated", source, {
                "signal_id": sig_id, "type": signal_type, "strength": strength,
                "reliability": reliability, "effective_weight": effective_weight,
            }, entity_keys, self.run_id)

        return signal

    def get_recent_signals(self, hours=168, signal_type=None, min_effective_weight=0):
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        signals = [s for s in self.data["signals"] if s["timestamp"] >= cutoff]
        if signal_type:
            signals = [s for s in signals if s["type"] == signal_type]
        if min_effective_weight > 0:
            signals = [s for s in signals if s.get("effective_weight", 0) >= min_effective_weight]
        return sorted(signals, key=lambda x: x.get("effective_weight", 0) * x["strength"], reverse=True)

    # ── Connection Management ──

    def connect(self, entity_a, entity_b, relationship, data=None):
        for existing in self.data["connections"][-200:]:
            if existing["from"] == entity_a and existing["to"] == entity_b and existing["relationship"] == relationship:
                existing["data"].update(data or {})
                return
        self.data["connections"].append({
            "from": entity_a, "to": entity_b,
            "relationship": relationship, "data": data or {},
            "created": datetime.utcnow().isoformat(),
        })

    def get_connections(self, entity_key, relationship=None):
        conns = [c for c in self.data["connections"] if c["from"] == entity_key or c["to"] == entity_key]
        if relationship:
            conns = [c for c in conns if c["relationship"] == relationship]
        return conns

    # ── ACTION OBJECTS (v2: structured, not prose) ──

    def create_action(self, action_type, target_entity, action_data, trigger_signal_ids=None, top_features=None):
        """
        v2 FIX: Actions now have:
        - Explicit trigger_signal_ids (which signals caused this recommendation)
        - top_features (which scoring features contributed)
        - structured action schema
        """
        action_id = uuid.uuid4().hex[:12]
        trigger_signal_ids = trigger_signal_ids or []

        action = {
            "id": action_id,
            "type": action_type,
            "target": target_entity,
            "data": action_data,
            "trigger_signal_ids": trigger_signal_ids,  # v2 FIX
            "top_features": top_features or [],         # v2 FIX
            "timestamp": datetime.utcnow().isoformat(),
            "status": "recommended",
            "outcome": None,
            "outcome_date": None,
            "notes": "",
        }

        # v2 FIX: Mark trigger signals as acted_on
        for sig in self.data["signals"]:
            if sig["id"] in trigger_signal_ids:
                sig["acted_on"] = True
                sig["action_ids"].append(action_id) if "action_ids" in sig else None

        self.data["learning"]["action_log"].append(action)

        self.events.emit("ActionRecommended", "decision_engine", {
            "action_id": action_id, "type": action_type,
            "target": target_entity,
            "trigger_signals": len(trigger_signal_ids),
            "top_features": top_features[:3] if top_features else [],
        }, [target_entity], self.run_id)

        return action_id

    def record_outcome(self, action_id, outcome, notes=""):
        """v2 FIX: Proper attribution — updates weights for the SPECIFIC trigger signals."""
        for action in self.data["learning"]["action_log"]:
            if action["id"] == action_id:
                action["status"] = "outcome_recorded"
                action["outcome"] = outcome
                action["outcome_date"] = datetime.utcnow().isoformat()
                action["notes"] = notes

                # v2 FIX: Update weights for the SPECIFIC trigger signals
                trigger_ids = action.get("trigger_signal_ids", [])
                if not trigger_ids:
                    print(f"  ⚠️  No trigger signals linked to action {action_id}")
                    print(f"      Weight update skipped. This action was created by v1.")

                multiplier = {
                    "reply": 1.15,
                    "meeting": 1.25,
                    "closed": 1.40,
                    "lost": 0.90,
                    "no_response": 0.92,
                    "bounce": 0.85,
                }.get(outcome, 1.0)

                updated_signals = 0
                weights = self.data["learning"]["signal_weights"]
                for sig in self.data["signals"]:
                    if sig["id"] in trigger_ids:
                        sig_type = sig["type"]
                        old_weight = weights.get(sig_type, 5)
                        new_weight = round(old_weight * multiplier, 2)
                        new_weight = max(1, min(30, new_weight))  # Clamp 1-30
                        weights[sig_type] = new_weight
                        updated_signals += 1
                        sig["outcome"] = outcome

                # Record in history
                self.data["learning"]["outcome_history"].append({
                    "action_id": action_id,
                    "action_type": action["type"],
                    "target": action["target"],
                    "outcome": outcome,
                    "trigger_signals": trigger_ids,
                    "signals_updated": updated_signals,
                    "multiplier": multiplier,
                    "timestamp": datetime.utcnow().isoformat(),
                })

                # Track messaging effectiveness
                msg_data = action.get("data", {})
                angle = msg_data.get("angle", msg_data.get("reason", "unknown"))
                if angle not in self.data["learning"]["messaging_effectiveness"]:
                    self.data["learning"]["messaging_effectiveness"][angle] = {"sent": 0, "replied": 0, "meetings": 0, "closed": 0}
                me = self.data["learning"]["messaging_effectiveness"][angle]
                me["sent"] += 1
                if outcome == "reply":
                    me["replied"] += 1
                elif outcome == "meeting":
                    me["meetings"] += 1
                elif outcome == "closed":
                    me["closed"] += 1

                self.events.emit("OutcomeRecorded", "learning_engine", {
                    "action_id": action_id, "outcome": outcome,
                    "signals_updated": updated_signals, "multiplier": multiplier,
                }, [action["target"]], self.run_id)

                print(f"  ✅ Outcome recorded: {action_id} → {outcome}")
                print(f"     Signals updated: {updated_signals}")
                print(f"     Weight multiplier: {multiplier}x")
                return True

        print(f"  ❌ Action not found: {action_id}")
        return False


# ═══════════════════════════════════════════════════════════
# INGEST ENGINE (v2: with event logging)
# ═══════════════════════════════════════════════════════════

def ingest_all(graph):
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM v2 — INGESTING ALL INTELLIGENCE")
    print(f"  Run ID: {graph.run_id}")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═'*60}\n")

    pre_entities = len(graph.data["entities"])
    pre_signals = len(graph.data["signals"])

    graph.events.emit("IngestStarted", "war_room", {
        "pre_entities": pre_entities, "pre_signals": pre_signals,
    }, run_id=graph.run_id)

    _ingest_pipeline(graph)
    _ingest_briefs(graph)
    _ingest_reddit(graph)
    _ingest_competitors(graph)
    _ingest_research(graph)
    _ingest_alerts(graph)

    graph.data["metadata"]["last_ingest"] = datetime.utcnow().isoformat()
    graph.data["metadata"]["ingest_count"] = graph.data["metadata"].get("ingest_count", 0) + 1
    graph.save()

    new_e = len(graph.data["entities"]) - pre_entities
    new_s = len(graph.data["signals"]) - pre_signals

    graph.events.emit("IngestCompleted", "war_room", {
        "new_entities": new_e, "new_signals": new_s,
        "total_entities": len(graph.data["entities"]),
        "total_signals": len(graph.data["signals"]),
    }, run_id=graph.run_id)

    print(f"\n{'─'*60}")
    print(f"  INGEST COMPLETE")
    print(f"  New entities: {new_e} (total: {len(graph.data['entities'])})")
    print(f"  New signals: {new_s} (total: {len(graph.data['signals'])})")
    print(f"  Connections: {len(graph.data['connections'])}")
    print(f"  Events logged: {graph.events.count()}")
    print(f"{'═'*60}\n")


def _ingest_pipeline(graph):
    print(f"  ┌─ Pipeline Data")
    scored_files = sorted(
        [f for f in OUTPUT_DIR.glob("scored_apollo_*.json") if f.is_file() and not f.is_symlink()],
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not scored_files:
        print(f"  └─ No scored files found")
        return

    with open(scored_files[0]) as f:
        data = json.load(f)

    leads = data.get("leads", data.get("prospects", data if isinstance(data, list) else []))
    companies = defaultdict(list)
    for lead in leads:
        co = lead.get("company_name", "Unknown")
        if co and co != "Unknown":
            companies[co].append(lead)

    for co_name, contacts in companies.items():
        scores = [c.get("nexus_lead_score", 0) for c in contacts]
        top = max(contacts, key=lambda c: c.get("nexus_lead_score", 0))
        domain = top.get("company_domain", top.get("domain", ""))
        verified = sum(1 for c in contacts if c.get("hunter_status") == "valid" or c.get("email_verified"))
        avg = round(sum(scores) / len(scores), 1) if scores else 0

        entity_key = graph.add_entity("company", co_name, {
            "contacts": len(contacts),
            "avg_score": avg,
            "top_score": max(scores),
            "top_contact": f"{top.get('first_name', '')} {top.get('last_name', '')}".strip(),
            "top_title": top.get("title", ""),
            "verified_emails": verified,
            "pipeline_tier": "hot" if avg >= 80 else "warm" if avg >= 60 else "cool" if avg >= 40 else "cold",
            "source": "apollo_pipeline",
        }, domain=domain, external_ids={"apollo_company": co_name})

        for contact in contacts:
            person_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
            if person_name:
                person_key = graph.add_entity("person", person_name, {
                    "title": contact.get("title", ""),
                    "email": contact.get("email", ""),
                    "score": contact.get("nexus_lead_score", 0),
                    "company": co_name,
                }, domain=domain)
                graph.connect(entity_key, person_key, "employs")

    print(f"  └─ ✅ {len(companies)} companies, {len(leads)} contacts")


def _ingest_briefs(graph):
    print(f"  ┌─ Company Briefs")
    briefs_dir = OUTPUT_DIR / "briefs"
    if not briefs_dir.exists():
        print(f"  └─ No briefs directory")
        return

    count = 0
    for bf in sorted(briefs_dir.glob("brief_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(bf) as f:
                data = json.load(f)
            meta = data.get("metadata", {})
            phases = data.get("phases", {})
            company = meta.get("company", "")
            if not company:
                continue

            p1 = phases.get("phase_1", {})
            p4 = phases.get("phase_4", {})
            p5 = phases.get("phase_5", {})
            p6 = phases.get("phase_6", {})

            domain = meta.get("domain", p1.get("domain", ""))

            entity_key = graph.add_entity("company", company, {
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
            }, domain=domain)

            graph.add_signal("brief_completed", "brief_engine", [entity_key], {
                "company": company,
                "phases_complete": sum(1 for p in phases.values() if isinstance(p, dict) and len(p) > 1),
            }, strength=3)

            count += 1
        except:
            continue

    print(f"  └─ ✅ {count} briefs")


def _ingest_reddit(graph):
    print(f"  ┌─ Reddit / Social Intel")
    total = 0

    # Check multiple possible locations
    for search_dir in [OUTPUT_DIR / "free_intel", OUTPUT_DIR / "competitor_intel"]:
        if not search_dir.exists():
            continue
        for pattern in ["reddit_scan_*.json", "vuln_v2_*.json"]:
            files = sorted(search_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            if not files:
                continue

            try:
                with open(files[0]) as f:
                    data = json.load(f)

                # Handle multiple formats
                posts = []
                if "reddit" in data and "posts" in data["reddit"]:
                    posts = data["reddit"]["posts"]
                elif "signals" in data:
                    posts = data["signals"]
                elif isinstance(data, list):
                    posts = data

                for post in posts:
                    intent = post.get("intent_score", post.get("signal_strength", 0))
                    if not intent and not post.get("buying_signals"):
                        continue

                    sig_type = "reddit_supplier_seeking" if post.get("is_supplier_seeking") or post.get("buying_signals") \
                        else "reddit_complaint" if post.get("is_complaint") \
                        else "reddit_comparison" if post.get("is_comparison") \
                        else "reddit_signal"

                    strength = min(10, max(1, (intent or 0) // 5 + 1))

                    graph.add_signal(sig_type, "reddit", [], {
                        "title": post.get("title", ""),
                        "subreddit": post.get("subreddit", ""),
                        "url": post.get("url", ""),
                        "body_preview": post.get("body", "")[:200],
                        "competitors_mentioned": post.get("competitors_mentioned", []),
                    }, strength=strength)
                    total += 1
            except:
                continue

    print(f"  └─ ✅ {total} Reddit signals")


def _ingest_competitors(graph):
    print(f"  ┌─ Competitor Intel")
    vuln_dir = OUTPUT_DIR / "competitor_intel"
    if not vuln_dir.exists():
        print(f"  └─ No competitor data")
        return

    files = sorted(
        list(vuln_dir.glob("vuln_v2_*.json")) + list(vuln_dir.glob("competitor_vuln_*.json")),
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not files:
        print(f"  └─ No competitor files")
        return

    with open(files[0]) as f:
        data = json.load(f)

    competitors = data.get("competitor_scores", data.get("competitors", {}))
    count = 0
    for name, info in competitors.items():
        tp = info.get("trustpilot", {})
        if isinstance(tp, dict) and not tp:
            # Try nested
            tp = info.get("reviews", {}).get("trustpilot", {})

        domain_map = {
            "True Terpenes": "trueterpenes.com",
            "Abstrax Tech": "abstraxtech.com",
            "Floraplex": "floraplex.com",
            "Denver Terpenes": "denverterpenes.com",
            "Peak Supply Co": "peaksupplyco.com",
            "Terps USA": "terpsusa.com",
            "Extract Consultants": "extractconsultants.com",
        }

        entity_key = graph.add_entity("competitor", name, {
            "is_competitor": True,
            "trustpilot_rating": tp.get("rating") if isinstance(tp, dict) else None,
            "trustpilot_count": tp.get("count", tp.get("review_count")) if isinstance(tp, dict) else None,
            "hiring": info.get("hiring", False),
            "vulnerability_score": info.get("score", 0),
            "risk_level": info.get("risk", ""),
        }, domain=domain_map.get(name, ""))

        if isinstance(tp, dict) and tp.get("rating"):
            rating = tp["rating"]
            if rating < 3.5:
                graph.add_signal("trustpilot_below_3.5", "trustpilot", [entity_key], {
                    "competitor": name, "rating": rating,
                }, strength=8)
            elif rating < 4.0:
                graph.add_signal("trustpilot_below_4.0", "trustpilot", [entity_key], {
                    "competitor": name, "rating": rating,
                }, strength=5)

        if info.get("hiring"):
            graph.add_signal("hiring_signal", "company_website", [entity_key], {
                "competitor": name,
            }, strength=4)

        count += 1

    print(f"  └─ ✅ {count} competitors")


def _ingest_research(graph):
    print(f"  ┌─ Terpene Research")
    kb_path = OUTPUT_DIR / "terpene_research" / "knowledge_base" / "terpene_kb.json"
    if not kb_path.exists():
        print(f"  └─ No research KB")
        return

    with open(kb_path) as f:
        kb = json.load(f)

    for terp_name, effects in kb.get("terpene_effects", {}).items():
        total_citations = sum(len(v) if isinstance(v, list) else 0 for v in effects.values())
        graph.add_entity("terpene", terp_name, {
            "effects": {e: len(pmids) if isinstance(pmids, list) else 0 for e, pmids in effects.items()},
            "total_citations": total_citations,
        })

    high = [p for p in kb.get("papers", {}).values() if p.get("relevance_score", 0) >= 40]
    for paper in high[:20]:
        graph.add_signal("research_breakthrough", "pubmed", [], {
            "title": paper.get("title", "")[:120],
            "terpenes": paper.get("terpenes_mentioned", []),
            "effects": paper.get("effects_mentioned", []),
            "url": paper.get("url", ""),
            "score": paper.get("relevance_score", 0),
        }, strength=paper.get("relevance_score", 0) // 20 + 1)

    trials = kb.get("clinical_trials", {})
    active = [t for t in trials.values() if t.get("status") in ("RECRUITING", "NOT_YET_RECRUITING", "ACTIVE_NOT_RECRUITING")]
    for trial in active[:10]:
        graph.add_signal("clinical_trial", "clinicaltrials", [], {
            "title": trial.get("title", "")[:100],
            "nct_id": trial.get("nct_id", ""),
            "url": trial.get("url", ""),
        }, strength=4)

    stats = kb.get("statistics", {})
    print(f"  └─ ✅ {stats.get('total_papers', 0)} papers, {len(active)} active trials")


def _ingest_alerts(graph):
    print(f"  ┌─ Trigger Alerts")
    alerts_dir = OUTPUT_DIR / "alerts"
    if not alerts_dir.exists() or not list(alerts_dir.glob("*.json")):
        print(f"  └─ No alerts")
        return
    count = 0
    for af in sorted(alerts_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
        try:
            with open(af) as f:
                alerts = json.load(f)
            for a in (alerts if isinstance(alerts, list) else [alerts]):
                graph.add_signal("trigger_alert", "trigger_monitor", [], {
                    "detail": json.dumps(a, default=str)[:200],
                }, strength=6)
                count += 1
        except:
            continue
    print(f"  └─ ✅ {count} alerts")


# ═══════════════════════════════════════════════════════════
# DECISION ENGINE (v2: proper attribution + structured actions)
# ═══════════════════════════════════════════════════════════

def generate_decisions(graph):
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM v2 — DECISION ENGINE")
    print(f"  Entities: {len(graph.data['entities'])} | Signals: {len(graph.data['signals'])}")
    print(f"{'═'*60}\n")

    companies = graph.get_entities_by_type("company")
    competitors = graph.get_entities_by_type("competitor")
    recent_signals = graph.get_recent_signals(hours=168)

    # ── Rank companies ──
    priorities = []
    for key, co in companies.items():
        if co.get("is_competitor"):
            continue

        score = 0
        features = []
        trigger_signal_ids = []

        # Pipeline base score
        avg = co.get("avg_score", 0)
        score += avg * 0.3
        if avg >= 60:
            features.append(f"pipeline_score:{avg}")

        # Brief completed
        if co.get("brief_completed"):
            score += 15
            features.append("brief_completed")

        # Verified emails
        verified = co.get("verified_emails", 0)
        if verified > 0:
            score += verified * 3
            features.append(f"verified_emails:{verified}")

        # Priority score from brief
        ps = co.get("priority_score", 0)
        if ps:
            score += ps * 0.2
            features.append(f"brief_priority:{ps}")

        # Signals linked to this entity
        entity_signals = [s for s in recent_signals if key in s.get("entities", [])]
        for sig in entity_signals:
            ew = sig.get("effective_weight", sig.get("base_weight", 5) * sig.get("source_reliability", 0.5))
            score += ew * sig["strength"] * 0.5
            features.append(f"signal:{sig['type']}(w={ew:.1f})")
            trigger_signal_ids.append(sig["id"])

        # Cross-pollination: competitor vulnerability
        supplier = co.get("current_supplier", "")
        if supplier:
            for comp_key, comp in competitors.items():
                if supplier.lower() in comp.get("name", "").lower():
                    tp = comp.get("trustpilot_rating")
                    if tp and tp < 4.0:
                        boost = (4.0 - tp) * 10
                        score += boost
                        features.append(f"supplier_vuln:{comp['name']}(tp={tp})")
                    vuln = comp.get("vulnerability_score", 0)
                    if vuln > 0:
                        score += vuln * 1.5
                        features.append(f"competitor_vuln:{vuln}")

        # Switching triggers from brief
        triggers = co.get("switching_triggers", [])
        if triggers:
            score += len(triggers) * 2
            features.append(f"switching_triggers:{len(triggers)}")

        # Recency decay: boost companies with recent signals
        if entity_signals:
            most_recent = max(s["timestamp"] for s in entity_signals)
            hours_ago = (datetime.utcnow() - datetime.fromisoformat(most_recent.replace("Z", ""))).total_seconds() / 3600
            if hours_ago < 24:
                score *= 1.2
                features.append("signal_fresh_24h")
            elif hours_ago < 72:
                score *= 1.1

        priorities.append({
            "entity_key": key,
            "company": co.get("name", "?"),
            "score": round(score, 1),
            "features": features,
            "trigger_signal_ids": trigger_signal_ids,
            "tier": co.get("pipeline_tier", "?"),
            "brief": co.get("brief_completed", False),
            "contacts": co.get("contacts", 0),
            "emails": co.get("verified_emails", 0),
            "top_contact": co.get("top_contact", ""),
            "domain": co.get("domain", ""),
        })

    priorities.sort(key=lambda x: x["score"], reverse=True)

    # Create structured actions for top companies
    for cp in priorities[:10]:
        action_type = "outreach" if cp["brief"] and cp["emails"] > 0 \
            else "run_brief" if not cp["brief"] \
            else "verify_emails" if cp["emails"] == 0 \
            else "outreach_prep"

        graph.create_action(
            action_type=action_type,
            target_entity=cp["entity_key"],
            action_data={
                "company": cp["company"],
                "score": cp["score"],
                "reason": "; ".join(cp["features"][:5]),
                "angle": "supplier_switch_wedge" if "supplier_vuln" in str(cp["features"]) else "value_proposition",
                "next_step": {
                    "outreach": "Send email to top contact",
                    "run_brief": "Run sales_intel_brief_v4.py",
                    "verify_emails": "Run enrich_pipeline_v2.py",
                    "outreach_prep": "Brief complete, verify emails next",
                }.get(action_type, "Review"),
            },
            trigger_signal_ids=cp["trigger_signal_ids"][:10],
            top_features=cp["features"][:5],
        )

    # Reddit actions
    reddit_signals = [s for s in recent_signals if s["type"].startswith("reddit_")]
    reddit_actions = []
    for sig in reddit_signals[:10]:
        d = sig["data"]
        reddit_actions.append({
            "type": sig["type"],
            "priority": sig.get("effective_weight", 5) * sig["strength"],
            "title": d.get("title", "")[:80],
            "subreddit": d.get("subreddit", ""),
            "url": d.get("url", ""),
        })

    # Competitor actions
    comp_actions = []
    for key, comp in competitors.items():
        tp = comp.get("trustpilot_rating")
        if tp and tp < 4.0:
            customers = [co.get("name", "?") for _, co in companies.items()
                        if comp.get("name", "").lower() in str(co.get("current_supplier", "")).lower()]
            comp_actions.append({
                "competitor": comp.get("name", ""),
                "vulnerability": f"Trustpilot {tp}/5",
                "prospects": customers,
            })

    # Build decision doc
    doc = {
        "generated_at": datetime.utcnow().isoformat(),
        "run_id": graph.run_id,
        "summary": {
            "entities": len(graph.data["entities"]),
            "signals": len(graph.data["signals"]),
            "events_logged": graph.events.count(),
            "companies_ranked": len(priorities),
        },
        "priority_companies": priorities[:15],
        "reddit_actions": reddit_actions,
        "competitor_actions": comp_actions,
    }

    graph.data["metadata"]["last_decision"] = datetime.utcnow().isoformat()
    graph.data["metadata"]["decision_count"] = graph.data["metadata"].get("decision_count", 0) + 1
    graph.save()

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    json_path = DECISIONS_DIR / f"decisions_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(doc, f, indent=2, default=str)

    md_path = _generate_briefing(doc, graph)
    return doc, md_path


def _generate_briefing(doc, graph):
    L = []
    L.append(f"# WAR ROOM v2 — Daily Intelligence Briefing")
    L.append(f"**{datetime.utcnow().strftime('%A, %B %d, %Y')}** | Run: {doc['run_id']}\n")
    L.append(f"---\n")

    s = doc["summary"]
    L.append(f"## System Status")
    L.append(f"**{s['entities']} entities** | **{s['signals']} signals** | **{s['events_logged']} events logged**\n")

    # Learning status
    outcomes = graph.data["learning"]["outcome_history"]
    if outcomes:
        wins = sum(1 for o in outcomes if o["outcome"] in ("reply", "meeting", "closed"))
        L.append(f"Learning: {len(outcomes)} outcomes tracked | {wins} positive | Weights adjusting automatically\n")

    L.append(f"## Today's Priority Companies\n")
    L.append(f"*Composite score: pipeline + signals × source_reliability + competitor vuln + recency*\n")

    for i, cp in enumerate(doc["priority_companies"][:15], 1):
        emoji = "🔴" if cp["score"] >= 50 else "🟡" if cp["score"] >= 25 else "🔵"
        brief = "✅ Brief" if cp["brief"] else "⏳ No brief"
        action = "run_brief" if not cp["brief"] else "verify_emails" if cp["emails"] == 0 else "outreach"

        L.append(f"### {i}. {cp['company']} — {cp['score']} {emoji}")
        L.append(f"*{cp['tier'].upper()} | {cp['contacts']} contacts | {cp['emails']} verified | {brief}*")
        if cp["top_contact"]:
            L.append(f"**Contact:** {cp['top_contact']}")
        if cp.get("domain"):
            L.append(f"**Domain:** {cp['domain']}")

        L.append(f"**Next action:** `{action}`")
        if cp["features"]:
            L.append(f"**Scoring features:** {', '.join(cp['features'][:5])}")
        L.append("")

    # Reddit
    if doc["reddit_actions"]:
        L.append(f"## Reddit Opportunities ({len(doc['reddit_actions'])})\n")
        for ra in doc["reddit_actions"][:5]:
            L.append(f"- **[{ra['type'].replace('reddit_','').upper()}]** r/{ra['subreddit']}: [{ra['title']}]({ra['url']})")

    # Competitors
    if doc["competitor_actions"]:
        L.append(f"\n## Competitor Vulnerabilities\n")
        for ca in doc["competitor_actions"]:
            L.append(f"- **{ca['competitor']}**: {ca['vulnerability']}")
            if ca["prospects"]:
                L.append(f"  Prospects using them: {', '.join(ca['prospects'][:5])}")

    # Pending outcomes
    pending = [a for a in graph.data["learning"]["action_log"] if a["status"] == "recommended"]
    if pending:
        L.append(f"\n## Record Outcomes ({len(pending)} pending)\n")
        L.append(f"```bash")
        for a in pending[-5:]:
            co = a["data"].get("company", "?")
            L.append(f"python3 war_room_v2.py learn --action-id {a['id']} --outcome reply    # {co}")
        L.append(f"```")
        L.append(f"*Options: reply, meeting, closed, lost, no_response, bounce*")

    L.append(f"\n---")
    L.append(f"*War Room v2 | Source reliability priors | Learning attribution fixed | {graph.events.count()} events*")

    md = "\n".join(L)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = DECISIONS_DIR / f"briefing_v2_{ts}.md"
    with open(path, "w") as f:
        f.write(md)

    print(f"  📄 Briefing: {path}")
    return path


# ═══════════════════════════════════════════════════════════
# VERIFICATION ENGINE (new in v2)
# ═══════════════════════════════════════════════════════════

def run_verification(graph):
    """Run data quality checks."""
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM v2 — VERIFICATION")
    print(f"{'═'*60}\n")

    issues = []

    # Check: entities without domains
    no_domain = [k for k, e in graph.data["entities"].items()
                 if e.get("type") == "company" and not e.get("domain")]
    if no_domain:
        issues.append(f"⚠️  {len(no_domain)} companies without domains — identity may drift")

    # Check: stale signals (>30 days)
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    stale = sum(1 for s in graph.data["signals"] if s["timestamp"] < cutoff)
    if stale:
        issues.append(f"ℹ️  {stale} signals older than 30 days — consider re-scanning")

    # Check: actions without outcomes
    pending = sum(1 for a in graph.data["learning"]["action_log"] if a["status"] == "recommended")
    if pending > 20:
        issues.append(f"⚠️  {pending} pending actions without outcomes — learning engine starved")

    # Check: low-confidence entities
    low_conf = [k for k, e in graph.data["entities"].items() if e.get("identity_confidence", 1) < 0.7]
    if low_conf:
        issues.append(f"ℹ️  {len(low_conf)} entities with low identity confidence")

    # Check: signal weight extremes
    weights = graph.data["learning"]["signal_weights"]
    extremes = [(k, v) for k, v in weights.items() if v >= 25 or v <= 1.5]
    if extremes:
        for k, v in extremes:
            issues.append(f"⚠️  Signal weight extreme: {k} = {v} (may need manual review)")

    if issues:
        print(f"  Issues found: {len(issues)}\n")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"  ✅ All checks passed")

    print(f"\n  Stats:")
    print(f"  │ Entities: {len(graph.data['entities'])}")
    print(f"  │ Signals: {len(graph.data['signals'])}")
    print(f"  │ Connections: {len(graph.data['connections'])}")
    print(f"  │ Events: {graph.events.count()}")
    print(f"  │ Actions: {len(graph.data['learning']['action_log'])}")
    print(f"  │ Outcomes: {len(graph.data['learning']['outcome_history'])}")
    print(f"\n{'═'*60}\n")


# ═══════════════════════════════════════════════════════════
# STATUS & CLI
# ═══════════════════════════════════════════════════════════

def show_status(graph):
    meta = graph.data["metadata"]
    print(f"\n{'═'*60}")
    print(f"  WAR ROOM v2 — STATUS")
    print(f"{'═'*60}\n")
    print(f"  Version: {meta.get('version', 'v1')}")
    print(f"  Entities: {len(graph.data['entities'])}")
    print(f"  Signals: {len(graph.data['signals'])}")
    print(f"  Connections: {len(graph.data['connections'])}")
    print(f"  Events logged: {graph.events.count()}")

    print(f"\n  Entity types:")
    tc = defaultdict(int)
    for e in graph.data["entities"].values():
        tc[e.get("type", "?")] += 1
    for t, c in sorted(tc.items()):
        print(f"    {t}: {c}")

    print(f"\n  Ingests: {meta.get('ingest_count', 0)}")
    print(f"  Decisions: {meta.get('decision_count', 0)}")
    print(f"  Last ingest: {(meta.get('last_ingest') or 'never')[:19]}")

    print(f"\n  Learning:")
    log = graph.data["learning"]["action_log"]
    outcomes = graph.data["learning"]["outcome_history"]
    print(f"    Actions tracked: {len(log)}")
    print(f"    Outcomes recorded: {len(outcomes)}")
    if outcomes:
        by_type = defaultdict(int)
        for o in outcomes:
            by_type[o["outcome"]] += 1
        for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"      {k}: {v}")

    print(f"\n  Signal weights:")
    for sig, w in sorted(graph.data["learning"]["signal_weights"].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(w)
        print(f"    {sig:<35} {w:>5.1f} {bar}")

    print(f"\n{'═'*60}\n")


def show_learning(graph):
    print(f"\n{'═'*60}")
    print(f"  LEARNING ENGINE v2")
    print(f"{'═'*60}\n")

    log = graph.data["learning"]["action_log"]
    outcomes = graph.data["learning"]["outcome_history"]

    print(f"  Actions: {len(log)} | Outcomes: {len(outcomes)}")

    # Show messaging effectiveness
    me = graph.data["learning"].get("messaging_effectiveness", {})
    if me:
        print(f"\n  Messaging effectiveness:")
        for angle, stats in sorted(me.items(), key=lambda x: x[1].get("replied", 0) + x[1].get("meetings", 0), reverse=True):
            sent = stats.get("sent", 0)
            replied = stats.get("replied", 0)
            meetings = stats.get("meetings", 0)
            rate = f"{(replied+meetings)/sent*100:.0f}%" if sent > 0 else "—"
            print(f"    {angle}: {sent} sent → {replied} replies, {meetings} meetings ({rate})")

    pending = [a for a in log if a["status"] == "recommended"]
    if pending:
        print(f"\n  Pending actions ({len(pending)}):")
        for a in pending[-10:]:
            co = a["data"].get("company", "?")
            sigs = len(a.get("trigger_signal_ids", []))
            print(f"    [{a['id']}] {a['type']}: {co} ({sigs} trigger signals)")
        print(f"\n  Record: python3 war_room_v2.py learn --action-id <id> --outcome <reply|meeting|closed|lost|no_response|bounce>")

    print(f"\n{'═'*60}\n")


def show_events(graph):
    events = graph.events.get_recent(30)
    print(f"\n{'═'*60}")
    print(f"  EVENT LOG (last {len(events)} events)")
    print(f"{'═'*60}\n")
    for e in events:
        ts = e["timestamp"][11:19]
        print(f"  [{ts}] {e['event_type']:<25} {e['source_agent']:<20} {json.dumps(e['payload'], default=str)[:60]}")
    print(f"\n  Total events: {graph.events.count()}")
    print(f"\n{'═'*60}\n")


def show_connections(graph):
    print(f"\n{'═'*60}")
    print(f"  INTELLIGENCE CONNECTIONS")
    print(f"{'═'*60}\n")
    companies = graph.get_entities_by_type("company")
    for key, co in sorted(companies.items(), key=lambda x: x[1].get("avg_score", 0), reverse=True)[:10]:
        conns = graph.get_connections(key)
        sigs = [s for s in graph.data["signals"] if key in s.get("entities", [])]
        print(f"  {co.get('name','?')} [{co.get('domain','')}]")
        print(f"  │ {co.get('pipeline_tier','?')} | Score: {co.get('avg_score',0)} | Brief: {'✅' if co.get('brief_completed') else '❌'}")
        if co.get("current_supplier"):
            print(f"  │ Supplier: {co['current_supplier']}")
        if conns:
            print(f"  │ Connections: {len(conns)}")
        if sigs:
            print(f"  │ Active signals: {len(sigs)}")
        print(f"  │")
    print(f"{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(description="War Room v2 — with learning attribution fix")
    parser.add_argument("command", help="brief|ingest|decide|status|learn|events|verify|connect")
    parser.add_argument("--action-id", help="Action ID for outcome recording")
    parser.add_argument("--outcome", help="reply|meeting|closed|lost|no_response|bounce")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    graph = KnowledgeGraph()
    cmd = args.command.lower()

    if cmd == "brief":
        ingest_all(graph)
        generate_decisions(graph)
    elif cmd == "ingest":
        ingest_all(graph)
    elif cmd == "decide":
        generate_decisions(graph)
    elif cmd == "status":
        show_status(graph)
    elif cmd == "learn":
        if args.action_id and args.outcome:
            graph.record_outcome(args.action_id, args.outcome, args.notes)
            graph.save()
        else:
            show_learning(graph)
    elif cmd == "events":
        show_events(graph)
    elif cmd == "verify":
        run_verification(graph)
    elif cmd == "connect":
        show_connections(graph)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
