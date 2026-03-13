"""
NEXUS ONTOLOGY — Company-Wide Object Model
═══════════════════════════════════════════

Inspired by Palantir's Ontology: a unified layer of typed objects,
links, actions, and department views that lets every team operate
on a shared reality.

Objects  = the nouns  (Company, Contact, Terpene, Paper, Product, …)
Links    = relationships between objects
Actions  = the verbs  (outreach, formulate, test, campaign, …)
Views    = department-specific projections of the same objects
"""

import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ═══════════════════════════════════════════════════════════
# SCHEMA DEFINITIONS — Object Types, Properties, Link Types
# ═══════════════════════════════════════════════════════════

ONTOLOGY_VERSION = "1.0"

# Every object type and its expected properties + which departments care about it
OBJECT_TYPES = {
    "company": {
        "label": "Company",
        "properties": [
            "name", "domain", "industry", "state", "size",
            "current_supplier", "temperature", "avg_score",
        ],
        "departments": ["bdr", "marketing", "ops", "executive"],
    },
    "contact": {
        "label": "Contact",
        "properties": [
            "name", "email", "title", "company_id", "verified",
            "linkedin", "phone",
        ],
        "departments": ["bdr", "marketing"],
    },
    "competitor": {
        "label": "Competitor",
        "properties": [
            "name", "trustpilot", "risk", "vulnerability_score",
            "hiring", "vulnerability_summary",
        ],
        "departments": ["bdr", "marketing", "executive"],
    },
    "terpene": {
        "label": "Terpene",
        "properties": [
            "name", "paper_count", "top_effects", "evidence_grade",
            "velocity", "commercial_potential",
        ],
        "departments": ["rd", "bdr", "marketing", "compliance"],
    },
    "paper": {
        "label": "Research Paper",
        "properties": [
            "title", "journal", "year", "url", "relevance_score",
            "evidence_grade", "study_type", "terpenes", "effects",
            "mechanisms", "model_organism", "outcome_direction",
        ],
        "departments": ["rd", "compliance"],
    },
    "product": {
        "label": "Product",
        "properties": [
            "name", "sku", "terpene_profile", "status",
            "formulation_date", "batch_count",
        ],
        "departments": ["rd", "ops", "marketing", "bdr"],
    },
    "signal": {
        "label": "Signal",
        "properties": [
            "type", "category", "source", "summary", "timestamp",
            "raw_strength", "decayed_score", "reliability_prior",
            "acted_on",
        ],
        "departments": ["bdr", "marketing", "executive"],
    },
    "regulation": {
        "label": "Regulation",
        "properties": [
            "title", "jurisdiction", "status", "effective_date",
            "terpenes_affected", "impact_level", "summary",
        ],
        "departments": ["compliance", "rd", "executive"],
    },
    "action": {
        "label": "Action",
        "properties": [
            "action_type", "department", "actor", "status",
            "target_ids", "created_at", "completed_at", "notes",
        ],
        "departments": ["bdr", "rd", "marketing", "ops", "compliance", "executive"],
    },
}

# Relationship types between objects
LINK_TYPES = {
    "has_contact":       {"from": "company",    "to": "contact",    "label": "has contact"},
    "competes_with":     {"from": "company",    "to": "competitor", "label": "competes with"},
    "studied_in":        {"from": "terpene",    "to": "paper",      "label": "studied in"},
    "mentions_effect":   {"from": "paper",      "to": "terpene",    "label": "mentions effect of"},
    "contains_terpene":  {"from": "product",    "to": "terpene",    "label": "contains"},
    "targets_company":   {"from": "signal",     "to": "company",    "label": "targets"},
    "targets_terpene":   {"from": "signal",     "to": "terpene",    "label": "relates to"},
    "regulates":         {"from": "regulation", "to": "terpene",    "label": "regulates"},
    "acts_on":           {"from": "action",     "to": "company",    "label": "acts on"},
    "acts_on_terpene":   {"from": "action",     "to": "terpene",    "label": "acts on"},
    "ordered_by":        {"from": "product",    "to": "company",    "label": "ordered by"},
}

# Department definitions
DEPARTMENTS = {
    "bdr": {
        "label": "Business Development",
        "description": "Sales prospecting, outreach, pipeline management",
        "color": "#00E09A",
    },
    "rd": {
        "label": "Research & Development",
        "description": "Terpene research, formulation, product development",
        "color": "#00D4FF",
    },
    "marketing": {
        "label": "Marketing",
        "description": "Campaigns, content, positioning, brand",
        "color": "#C5A55A",
    },
    "ops": {
        "label": "Operations",
        "description": "Orders, batches, inventory, fulfillment",
        "color": "#FF6B6B",
    },
    "compliance": {
        "label": "Compliance & Regulatory",
        "description": "Regulatory monitoring, claims review, documentation",
        "color": "#B388FF",
    },
    "executive": {
        "label": "Executive",
        "description": "Cross-department dashboards, KPIs, strategic view",
        "color": "#FFFFFF",
    },
}

# Action types per department
ACTION_TYPES = {
    "bdr": [
        {"id": "outreach", "label": "Send Outreach", "targets": ["company", "contact"]},
        {"id": "run_brief", "label": "Generate Brief", "targets": ["company"]},
        {"id": "schedule_demo", "label": "Schedule Demo", "targets": ["company", "contact"]},
        {"id": "update_stage", "label": "Update Pipeline Stage", "targets": ["company"]},
        {"id": "log_call", "label": "Log Call", "targets": ["contact"]},
    ],
    "rd": [
        {"id": "request_formulation", "label": "Request Formulation", "targets": ["terpene", "product"]},
        {"id": "run_stability_test", "label": "Run Stability Test", "targets": ["product"]},
        {"id": "publish_finding", "label": "Publish Finding", "targets": ["terpene", "paper"]},
        {"id": "update_profile", "label": "Update Terpene Profile", "targets": ["terpene"]},
    ],
    "marketing": [
        {"id": "launch_campaign", "label": "Launch Campaign", "targets": ["company", "terpene"]},
        {"id": "create_content", "label": "Create Content", "targets": ["terpene", "product"]},
        {"id": "update_positioning", "label": "Update Positioning", "targets": ["product"]},
    ],
    "ops": [
        {"id": "create_order", "label": "Create Order", "targets": ["company", "product"]},
        {"id": "schedule_batch", "label": "Schedule Batch", "targets": ["product"]},
        {"id": "update_inventory", "label": "Update Inventory", "targets": ["terpene"]},
    ],
    "compliance": [
        {"id": "flag_regulatory", "label": "Flag Regulatory Issue", "targets": ["regulation", "terpene"]},
        {"id": "request_review", "label": "Request Claim Review", "targets": ["product", "terpene"]},
        {"id": "approve_claim", "label": "Approve Claim", "targets": ["product"]},
    ],
}


# ═══════════════════════════════════════════════════════════
# OBJECT REGISTRY — In-Memory Store + File Persistence
# ═══════════════════════════════════════════════════════════

class OntologyObject:
    """A single typed object in the ontology."""
    __slots__ = ("id", "type", "properties", "links", "created_at", "updated_at", "source")

    def __init__(self, obj_id, obj_type, properties=None, source="system"):
        self.id = obj_id
        self.type = obj_type
        self.properties = properties or {}
        self.links = []  # [{link_type, target_id, target_type, metadata}]
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.source = source

    def add_link(self, link_type, target_id, target_type, metadata=None):
        self.links.append({
            "link_type": link_type,
            "target_id": target_id,
            "target_type": target_type,
            "metadata": metadata or {},
        })

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "links": self.links,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
        }

    def project(self, department):
        """Return a department-specific view of this object."""
        type_def = OBJECT_TYPES.get(self.type, {})
        if department not in type_def.get("departments", []):
            return None  # This department doesn't have access

        view = {
            "id": self.id,
            "type": self.type,
            "label": type_def.get("label", self.type),
            "properties": self.properties,
            "links": self.links,
            "department": department,
        }

        # Add department-specific computed fields
        if self.type == "company":
            if department == "bdr":
                view["actions"] = ["outreach", "run_brief", "schedule_demo", "update_stage"]
                view["priority_fields"] = ["temperature", "avg_score", "current_supplier"]
            elif department == "marketing":
                view["actions"] = ["launch_campaign", "create_content"]
                view["priority_fields"] = ["industry", "size"]
            elif department == "ops":
                view["actions"] = ["create_order"]
                view["priority_fields"] = ["name", "domain"]
            elif department == "executive":
                view["actions"] = []
                view["priority_fields"] = ["temperature", "avg_score", "industry"]

        elif self.type == "terpene":
            if department == "rd":
                view["actions"] = ["request_formulation", "update_profile", "publish_finding"]
                view["priority_fields"] = ["paper_count", "top_effects", "evidence_grade", "velocity"]
            elif department == "bdr":
                view["actions"] = []
                view["priority_fields"] = ["name", "commercial_potential"]
            elif department == "compliance":
                view["actions"] = ["flag_regulatory", "request_review"]
                view["priority_fields"] = ["name", "top_effects"]
            elif department == "marketing":
                view["actions"] = ["create_content"]
                view["priority_fields"] = ["name", "commercial_potential", "top_effects"]

        elif self.type == "paper":
            if department == "rd":
                view["actions"] = ["publish_finding"]
                view["priority_fields"] = ["title", "evidence_grade", "study_type", "mechanisms"]
            elif department == "compliance":
                view["actions"] = ["request_review"]
                view["priority_fields"] = ["title", "evidence_grade", "effects"]

        return view


class ObjectRegistry:
    """
    Central registry for all ontology objects. Indexes from existing
    data sources (war room, research KB, pipeline) into typed objects.
    """

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.objects = {}       # id → OntologyObject
        self.by_type = defaultdict(dict)   # type → {id: OntologyObject}
        self.actions = []       # action log
        self._persistence_path = self.output_dir / "ontology" / "registry.json"

    def _make_id(self, obj_type, name_or_key):
        """Deterministic ID from type + key."""
        raw = f"{obj_type}:{name_or_key}".lower().strip()
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def register(self, obj_type, key, properties, source="system"):
        """Register or update an object. Returns the object."""
        obj_id = self._make_id(obj_type, key)
        if obj_id in self.objects:
            obj = self.objects[obj_id]
            obj.properties.update(properties)
            obj.updated_at = datetime.utcnow().isoformat()
        else:
            obj = OntologyObject(obj_id, obj_type, properties, source)
            self.objects[obj_id] = obj
            self.by_type[obj_type][obj_id] = obj
        return obj

    def link(self, from_id, link_type, to_id):
        """Create a link between two objects."""
        if from_id in self.objects and to_id in self.objects:
            target = self.objects[to_id]
            # Avoid duplicate links
            for existing in self.objects[from_id].links:
                if existing["target_id"] == to_id and existing["link_type"] == link_type:
                    return
            self.objects[from_id].add_link(link_type, to_id, target.type)

    def get(self, obj_id):
        """Get an object by ID."""
        return self.objects.get(obj_id)

    def get_by_type(self, obj_type, department=None):
        """Get all objects of a type, optionally projected for a department."""
        objects = list(self.by_type.get(obj_type, {}).values())
        if department:
            return [o.project(department) for o in objects if o.project(department)]
        return [o.to_dict() for o in objects]

    def search(self, query, obj_type=None, department=None, limit=50):
        """Search objects by name/property substring."""
        query_lower = query.lower()
        results = []
        source = self.objects.values()
        if obj_type:
            source = self.by_type.get(obj_type, {}).values()

        for obj in source:
            # Check department access
            if department:
                type_def = OBJECT_TYPES.get(obj.type, {})
                if department not in type_def.get("departments", []):
                    continue

            # Search across key properties
            name = obj.properties.get("name", obj.properties.get("title", ""))
            if query_lower in str(name).lower():
                results.append(obj)
                continue
            # Search other string properties
            for v in obj.properties.values():
                if isinstance(v, str) and query_lower in v.lower():
                    results.append(obj)
                    break

            if len(results) >= limit:
                break

        if department:
            return [o.project(department) for o in results if o.project(department)]
        return [o.to_dict() for o in results]

    def get_linked(self, obj_id, link_type=None, department=None):
        """Get all objects linked from a given object."""
        obj = self.objects.get(obj_id)
        if not obj:
            return []
        results = []
        for link in obj.links:
            if link_type and link["link_type"] != link_type:
                continue
            target = self.objects.get(link["target_id"])
            if target:
                if department:
                    proj = target.project(department)
                    if proj:
                        proj["_link_type"] = link["link_type"]
                        results.append(proj)
                else:
                    d = target.to_dict()
                    d["_link_type"] = link["link_type"]
                    results.append(d)
        return results

    def record_action(self, action_type, department, actor, target_ids, notes=""):
        """Record a cross-department action."""
        action = {
            "id": hashlib.md5(f"{action_type}{time.time()}".encode()).hexdigest()[:12],
            "action_type": action_type,
            "department": department,
            "actor": actor,
            "target_ids": target_ids,
            "status": "pending",
            "notes": notes,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }
        self.actions.append(action)

        # Also register as an ontology object so it's searchable
        self.register("action", action["id"], action, source=department)
        return action

    def get_actions(self, department=None, status=None, limit=50):
        """Get actions, optionally filtered."""
        results = self.actions
        if department:
            results = [a for a in results if a["department"] == department]
        if status:
            results = [a for a in results if a["status"] == status]
        return results[-limit:]

    def stats(self):
        """Summary statistics for the ontology."""
        type_counts = {t: len(objs) for t, objs in self.by_type.items() if objs}
        total_links = sum(len(o.links) for o in self.objects.values())
        return {
            "version": ONTOLOGY_VERSION,
            "total_objects": len(self.objects),
            "total_links": total_links,
            "total_actions": len(self.actions),
            "by_type": type_counts,
            "departments": list(DEPARTMENTS.keys()),
            "object_types": list(OBJECT_TYPES.keys()),
        }

    def department_summary(self, department):
        """Get a department-level summary of relevant objects."""
        summary = {
            "department": department,
            "meta": DEPARTMENTS.get(department, {}),
            "available_actions": ACTION_TYPES.get(department, []),
            "object_counts": {},
            "recent_actions": self.get_actions(department=department, limit=10),
        }
        for obj_type, type_def in OBJECT_TYPES.items():
            if department in type_def.get("departments", []):
                summary["object_counts"][obj_type] = len(self.by_type.get(obj_type, {}))
        return summary

    # ── Persistence ──

    def save(self):
        """Persist the registry to disk."""
        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": ONTOLOGY_VERSION,
            "saved_at": datetime.utcnow().isoformat(),
            "objects": {oid: o.to_dict() for oid, o in self.objects.items()},
            "actions": self.actions,
        }
        self._persistence_path.write_text(json.dumps(data, default=str, indent=2))

    def load(self):
        """Load persisted registry from disk."""
        if not self._persistence_path.exists():
            return False
        try:
            data = json.loads(self._persistence_path.read_text())
            for oid, odata in data.get("objects", {}).items():
                obj = OntologyObject(odata["id"], odata["type"], odata.get("properties", {}), odata.get("source", "system"))
                obj.links = odata.get("links", [])
                obj.created_at = odata.get("created_at", "")
                obj.updated_at = odata.get("updated_at", "")
                self.objects[oid] = obj
                self.by_type[obj.type][oid] = obj
            self.actions = data.get("actions", [])
            return True
        except Exception as e:
            print(f"  Warning: ontology load failed: {e}")
            return False


# ═══════════════════════════════════════════════════════════
# INDEXER — Populate ontology from existing Nexus data files
# ═══════════════════════════════════════════════════════════

def index_from_existing_data(registry, output_dir):
    """
    Walk all existing Nexus data sources and register them as
    ontology objects with proper links. This is the bridge between
    the old per-file data model and the new unified ontology.
    """
    output_dir = Path(output_dir)
    counts = defaultdict(int)

    # ── Companies + Contacts (from war room decisions) ──
    decisions_dir = output_dir / "war_room" / "decisions"
    if decisions_dir.exists():
        files = sorted(decisions_dir.glob("decisions_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if files:
            try:
                d = json.loads(files[0].read_text())
                for cp in d.get("priority_companies", d.get("top_priorities", [])):
                    company_name = cp.get("company", cp.get("name", ""))
                    if not company_name:
                        continue
                    co = registry.register("company", company_name, {
                        "name": company_name,
                        "domain": cp.get("domain", ""),
                        "current_supplier": cp.get("current_supplier", ""),
                        "temperature": cp.get("tier", "warm"),
                        "avg_score": cp.get("composite_score", cp.get("score", 0)),
                        "contacts": cp.get("contacts", 0),
                        "verified_emails": int(cp.get("emails", cp.get("verified", 0)) or 0),
                        "top_contact": cp.get("top_contact", ""),
                        "top_title": cp.get("top_title", ""),
                        "playbook": cp.get("playbook", ""),
                        "why_now": cp.get("why_now", ""),
                    }, source="war_room")
                    counts["company"] += 1
            except Exception as e:
                print(f"  Ontology: decisions index error: {e}")

    # ── Competitors (from war room graph) ──
    graph_path = output_dir / "war_room" / "knowledge_graph" / "war_room_graph.json"
    if graph_path.exists():
        try:
            g = json.loads(graph_path.read_text())
            entities = g.get("entities", {})

            for eid, ent in entities.items():
                if ent.get("type") == "competitor":
                    data = ent.get("data", {})
                    comp = registry.register("competitor", ent.get("name", eid), {
                        "name": ent.get("name", eid),
                        "trustpilot": data.get("trustpilot_score"),
                        "risk": data.get("risk_level", "LOW"),
                        "vulnerability_score": data.get("vulnerability_score", 0),
                        "hiring": data.get("hiring", False),
                        "vulnerability_summary": data.get("vulnerability_summary", ""),
                    }, source="war_room")
                    counts["competitor"] += 1

                    # Link companies that compete with this competitor
                    for co_id, co_obj in registry.by_type.get("company", {}).items():
                        registry.link(co_id, "competes_with", comp.id)

            # ── Signals (from war room graph) ──
            for s in g.get("signals", [])[-200:]:
                sig = registry.register("signal", s.get("id", str(time.time())), {
                    "type": s.get("type", "unknown"),
                    "source": s.get("source", ""),
                    "summary": s.get("data", {}).get("summary", s.get("data", {}).get("title", "")),
                    "timestamp": s.get("timestamp", ""),
                    "raw_strength": s.get("strength", 5),
                    "acted_on": s.get("acted_on", False),
                }, source="war_room")
                counts["signal"] += 1

                # Link signals to companies they mention
                for entity_name in s.get("entities", []):
                    for co_id, co_obj in registry.by_type.get("company", {}).items():
                        if entity_name.lower() in co_obj.properties.get("name", "").lower():
                            registry.link(sig.id, "targets_company", co_id)

        except Exception as e:
            print(f"  Ontology: graph index error: {e}")

    # ── Research Papers + Terpenes (from KB) ──
    kb_path = output_dir / "terpene_research" / "kb" / "kb.json"
    if kb_path.exists():
        try:
            kb = json.loads(kb_path.read_text())
            terpene_papers = defaultdict(list)

            for pid, p in kb.get("papers", {}).items():
                paper = registry.register("paper", pid, {
                    "title": p.get("title", ""),
                    "journal": p.get("journal", ""),
                    "year": p.get("year", ""),
                    "url": p.get("url", ""),
                    "relevance_score": p.get("relevance_score", 0),
                    "evidence_grade": p.get("evidence_grade", "D"),
                    "study_type": p.get("study_type", "unknown"),
                    "terpenes": p.get("terpenes_mentioned", []),
                    "effects": p.get("effects_mentioned", []),
                    "mechanisms": p.get("mechanisms_extracted", []),
                    "model_organism": p.get("model_organism", "unknown"),
                    "outcome_direction": p.get("outcome_direction", "unknown"),
                    "commercial_tags": p.get("commercial_tags", []),
                }, source="research_kb")
                counts["paper"] += 1

                for t in p.get("terpenes_mentioned", []):
                    terpene_papers[t.lower()].append(paper.id)

            # Build terpene objects from aggregated paper data
            for terp_name, paper_ids in terpene_papers.items():
                terp = registry.register("terpene", terp_name, {
                    "name": terp_name,
                    "paper_count": len(paper_ids),
                }, source="research_kb")
                counts["terpene"] += 1

                # Link terpene ↔ papers
                for paper_id in paper_ids:
                    registry.link(terp.id, "studied_in", paper_id)

        except Exception as e:
            print(f"  Ontology: KB index error: {e}")

    # ── Enrich terpenes with matrix data ──
    matrix_path = output_dir / "terpene_research" / "reports" / "terpene_effect_matrix.json"
    if matrix_path.exists():
        try:
            mdata = json.loads(matrix_path.read_text())
            rows = mdata.get("matrix", mdata) if isinstance(mdata, dict) else mdata
            if isinstance(rows, list):
                for row in rows:
                    terp_name = row.get("terpene", "")
                    if not terp_name:
                        continue
                    effects = {k: v for k, v in row.items() if k != "terpene" and isinstance(v, (int, float))}
                    top_effects = sorted(effects.items(), key=lambda x: x[1], reverse=True)[:5]
                    terp = registry.register("terpene", terp_name, {
                        "name": terp_name,
                        "top_effects": [e[0] for e in top_effects],
                        "effect_scores": effects,
                    }, source="research_matrix")
        except Exception as e:
            print(f"  Ontology: matrix index error: {e}")

    # ── Regulatory hits → Regulation objects ──
    reg_path = output_dir / "terpene_research" / "insights" / "regulatory.json"
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text())
            for hit in reg.get("regulatory_hits", []):
                r = registry.register("regulation", hit.get("title", str(time.time())), {
                    "title": hit.get("title", ""),
                    "jurisdiction": hit.get("jurisdiction", ""),
                    "status": hit.get("status", ""),
                    "summary": hit.get("summary", ""),
                    "terpenes_affected": hit.get("terpenes", []),
                    "impact_level": hit.get("impact", "low"),
                }, source="regulatory")
                counts["regulation"] += 1

                # Link to terpenes
                for t in hit.get("terpenes", []):
                    for tid, tobj in registry.by_type.get("terpene", {}).items():
                        if tobj.properties.get("name", "").lower() == t.lower():
                            registry.link(r.id, "regulates", tid)
        except Exception as e:
            print(f"  Ontology: regulatory index error: {e}")

    return dict(counts)
