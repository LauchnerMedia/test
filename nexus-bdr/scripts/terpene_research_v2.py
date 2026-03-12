#!/usr/bin/env python3
"""
Terpene Research Intelligence Engine v2 — PhD-Grade Analysis
============================================================
Not just retrieval — synthesis, evidence grading, trend detection,
effect-profile optimization, gap analysis, regulatory radar, and reports.

Design goals:
  - Zero LLM/API cost beyond public scientific endpoints (NCBI eutils)
  - Deterministic, file-backed knowledge base that compounds over time
  - Actionable synthesis (convergence + contradictions) instead of raw retrieval

Outputs (under outputs/terpene_research/):
  - knowledge_base/kb.json
  - insights/{trends,synthesis,gaps,regulatory,effect_profile_*}.json
  - reports/{digest.md,digest.json,executive_brief.md,talking_points.md,terpene_effect_matrix.json,kb_stats.json}

Usage:
    python3 scripts/terpene_research_v2.py --harvest --days 30
    python3 scripts/terpene_research_v2.py --full --days 90
    python3 scripts/terpene_research_v2.py --synthesize --days 45
    python3 scripts/terpene_research_v2.py --trends
    python3 scripts/terpene_research_v2.py --profile "sleep"
    python3 scripts/terpene_research_v2.py --gaps
    python3 scripts/terpene_research_v2.py --regulatory
    python3 scripts/terpene_research_v2.py --digest --days 60
    python3 scripts/terpene_research_v2.py --matrix
    python3 scripts/terpene_research_v2.py --talking-points --profile "pain"
    python3 scripts/terpene_research_v2.py --executive-brief --days 60
    python3 scripts/terpene_research_v2.py --stats
"""

import os, sys, json, re, time, argparse, hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs" if (SCRIPT_DIR / "outputs").exists() else SCRIPT_DIR.parent / "outputs"
RESEARCH_DIR = OUTPUT_DIR / "terpene_research"
KB_DIR = RESEARCH_DIR / "knowledge_base"
REPORTS_DIR = RESEARCH_DIR / "reports"
INSIGHTS_DIR = RESEARCH_DIR / "insights"
for d in [RESEARCH_DIR, KB_DIR, REPORTS_DIR, INSIGHTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "NexusBDR/2.0 (terpene-research@nexusbdr.com; scientific research tool)"}
NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


# ───────────────────────────────────────────────────────────
# TAXONOMY (pragmatic: extend over time)
# ───────────────────────────────────────────────────────────

TERPENES = {
    "myrcene": {"class": "monoterpene", "known_effects": ["sedative", "analgesic", "anti-inflammatory"], "tbf_products": ["Sleep formulations"]},
    "limonene": {"class": "monoterpene", "known_effects": ["anxiolytic", "antidepressant", "anti-inflammatory"], "tbf_products": ["Mood formulations"]},
    "alpha-pinene": {"class": "monoterpene", "known_effects": ["alertness", "anti-inflammatory"], "tbf_products": ["Focus blends"]},
    "beta-pinene": {"class": "monoterpene", "known_effects": ["anti-inflammatory"], "tbf_products": ["Hybrid blends"]},
    "linalool": {"class": "monoterpene", "known_effects": ["anxiolytic", "sedative"], "tbf_products": ["Relaxation formulations", "Topicals"]},
    "terpinolene": {"class": "monoterpene", "known_effects": ["antioxidant", "sedative"], "tbf_products": ["Sativa blends"]},
    "ocimene": {"class": "monoterpene", "known_effects": ["antifungal", "anti-inflammatory"], "tbf_products": ["Sativa blends"]},
    "camphene": {"class": "monoterpene", "known_effects": ["analgesic"], "tbf_products": ["Wellness blends"]},
    "delta-3-carene": {"class": "monoterpene", "known_effects": ["anti-inflammatory"], "tbf_products": ["CDT profiles"]},
    "alpha-terpineol": {"class": "monoterpene", "known_effects": ["sedative"], "tbf_products": ["Sleep blends"]},
    "beta-caryophyllene": {"class": "sesquiterpene", "known_effects": ["anti-inflammatory", "analgesic"], "tbf_products": ["Pain blends", "Topicals"], "competitive_moat": "Only dietary terpene broadly described as CB2-active; strong differentiator for inflammation/pain positioning."},
    "humulene": {"class": "sesquiterpene", "known_effects": ["anti-inflammatory"], "tbf_products": ["Appetite management blends"]},
    "bisabolol": {"class": "sesquiterpene", "known_effects": ["anti-irritant", "wound_healing"], "tbf_products": ["Topicals", "Skincare formulations"]},
    "nerolidol": {"class": "sesquiterpene", "known_effects": ["sedative", "skin_permeation"], "tbf_products": ["Topicals", "Transdermal formulations"]},
}

EFFECT_ONTOLOGY = {
    "anti-inflammatory": {"terms": ["anti-inflammatory", "antiinflammatory", "inflammation", "NF-kB", "TNF"], "category": "pain_inflammation"},
    "analgesic": {"terms": ["analgesic", "pain", "antinociceptive", "allodynia"], "category": "pain_inflammation"},
    "anxiolytic": {"terms": ["anxiolytic", "anxiety", "anti-anxiety", "panic"], "category": "sleep_relaxation"},
    "sedative": {"terms": ["sedative", "sleep", "insomnia", "GABA"], "category": "sleep_relaxation"},
    "antidepressant": {"terms": ["antidepressant", "depression", "mood", "serotonin", "5-HT"], "category": "mental_health"},
    "bioavailability": {"terms": ["bioavailability", "absorption", "pharmacokinetic", "Cmax", "AUC"], "category": "formulation"},
    "skin_permeation": {"terms": ["transdermal", "skin permeation", "topical", "percutaneous", "stratum corneum"], "category": "formulation"},
    "entourage_effect": {"terms": ["entourage", "synerg", "terpene-cannabinoid"], "category": "cannabis_science"},
}

STUDY_TYPE_PATTERNS = {
    "meta-analysis": {"terms": ["meta-analysis", "pooled analysis"], "evidence_grade": "A", "weight": 1.0},
    "systematic_review": {"terms": ["systematic review", "PRISMA"], "evidence_grade": "A", "weight": 0.95},
    "rct": {"terms": ["randomized controlled", "double-blind", "placebo-controlled", "clinical trial"], "evidence_grade": "A", "weight": 0.9},
    "cohort": {"terms": ["cohort", "prospective", "observational"], "evidence_grade": "B", "weight": 0.7},
    "animal_in_vivo": {"terms": ["in vivo", "mice", "rats", "murine", "rodent"], "evidence_grade": "C", "weight": 0.4},
    "in_vitro": {"terms": ["in vitro", "cell line", "cell culture"], "evidence_grade": "C", "weight": 0.35},
    "review": {"terms": ["review", "perspective"], "evidence_grade": "D", "weight": 0.2},
}

COMMERCIAL_CATEGORIES = {
    "vape_formulation": ["vape", "e-liquid", "inhalation"],
    "edible_formulation": ["edible", "oral", "gummy", "beverage"],
    "topical_formulation": ["topical", "cream", "lotion", "transdermal", "patch"],
    "stability": ["stability", "degradation", "shelf life"],
    "quality_control": ["GC-MS", "HPLC", "standardization"],
    "sensory": ["sensory", "flavor", "aroma"],
}

RESEARCH_TOPICS = [
    "cannabis terpene", "terpene entourage effect", "beta-caryophyllene CB2", "linalool anxiolytic",
    "myrcene sedative", "limonene anxiety", "terpene skin permeation transdermal", "terpene bioavailability",
    "terpene stability storage degradation", "terpene formulation vaporization",
]


# ───────────────────────────────────────────────────────────
# Harvest / PubMed parsing
# ───────────────────────────────────────────────────────────

def search_pubmed(query, max_results=20, days_back=90):
    date_filter = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    search_url = f"{NCBI_BASE}/esearch.fcgi"
    params = {
        "db": "pubmed", "term": query, "retmax": max_results, "sort": "date",
        "mindate": date_filter, "maxdate": datetime.utcnow().strftime("%Y/%m/%d"),
        "retmode": "json", "datetype": "pdat",
    }
    try:
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        time.sleep(0.4)
        fetch_url = f"{NCBI_BASE}/efetch.fcgi"
        resp2 = requests.get(fetch_url, params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}, headers=HEADERS, timeout=20)
        if resp2.status_code != 200:
            return []
        return parse_pubmed_xml(resp2.text)
    except Exception as e:
        print(f"    ⚠️  PubMed: {str(e)[:120]}")
        return []


def parse_pubmed_xml(xml_text):
    papers = []
    try:
        root = ET.fromstring(xml_text)
        for article in root.findall('.//PubmedArticle'):
            medline = article.find('.//MedlineCitation')
            if medline is None:
                continue
            pmid = medline.findtext('.//PMID', '')
            art = medline.find('.//Article')
            if art is None:
                continue
            title = art.findtext('.//ArticleTitle', '')
            abstract_parts = []
            for at in art.findall('.//Abstract/AbstractText'):
                label = at.get('Label', '')
                text = at.text or ''
                abstract_parts.append(f"{label}: {text}" if label else text)
            abstract = " ".join([a for a in abstract_parts if a])

            authors = []
            for auth in art.findall('.//AuthorList/Author'):
                last = auth.findtext('LastName', '')
                first = auth.findtext('ForeName', '')
                if last:
                    authors.append(f"{last} {first[0] if first else ''}".strip())

            journal = art.findtext('.//Journal/Title', '')
            year = art.findtext('.//Journal/JournalIssue/PubDate/Year', '')
            month = art.findtext('.//Journal/JournalIssue/PubDate/Month', '')

            doi = ""
            for eid in article.findall('.//ArticleIdList/ArticleId'):
                if eid.get('IdType') == 'doi':
                    doi = eid.text or ''
                    break

            full_text = f"{title} {abstract}"
            paper = {
                "pmid": pmid, "doi": doi,
                "title": title, "abstract": abstract[:3000],
                "authors": authors[:8], "journal": journal,
                "year": year, "month": month,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "terpenes_mentioned": detect_terpenes(full_text),
                "effects_mentioned": detect_effects(full_text),
                "study_type": classify_study_type(full_text),
                "mechanisms_extracted": extract_mechanisms(full_text),
                "commercial_tags": detect_commercial_relevance(full_text),
                "dose_info": extract_dose_info(abstract),
                "model_organism": detect_model_organism(full_text),
                "outcome_direction": detect_outcome_direction(abstract),
                "harvested_at": datetime.utcnow().isoformat(),
            }
            paper["evidence_grade"] = STUDY_TYPE_PATTERNS.get(paper["study_type"], {}).get("evidence_grade", "D")
            paper["evidence_weight"] = STUDY_TYPE_PATTERNS.get(paper["study_type"], {}).get("weight", 0.2)
            paper["relevance_score"] = score_relevance_v2(paper)
            papers.append(paper)
    except ET.ParseError as e:
        print(f"    ⚠️  XML parse error: {str(e)[:120]}")
    return papers


# ───────────────────────────────────────────────────────────
# Subagents: grading + abstract analyzers
# ───────────────────────────────────────────────────────────

def classify_study_type(text):
    tl = (text or "").lower()
    for st, info in STUDY_TYPE_PATTERNS.items():
        for term in info["terms"]:
            if term.lower() in tl:
                return st
    return "unknown"


def detect_model_organism(text):
    tl = (text or "").lower()
    models = {
        "human": ["human", "patient", "participant", "clinical"],
        "mouse": ["mouse", "mice", "murine"],
        "rat": ["rat", "rats"],
        "in_vitro": ["in vitro", "cell line", "cell culture"],
        "computational": ["in silico", "molecular docking", "computational"],
    }
    for k, terms in models.items():
        if any(t in tl for t in terms):
            return k
    return "unknown"


def detect_outcome_direction(abstract):
    if not abstract:
        return "unknown"
    text = abstract.lower()
    positive = ["significant", "effective", "improved", "reduced", "inhibited", "attenuated", "enhanced", "promising"]
    negative = ["no significant", "not effective", "failed", "no effect", "no difference", "ineffective", "did not"]
    neg_count = sum(1 for t in negative if t in text)
    pos_count = sum(1 for t in positive if t in text)
    if neg_count > pos_count:
        return "negative"
    if pos_count > 0:
        return "positive"
    return "neutral"


def extract_mechanisms(text):
    tl = (text or "").lower()
    mechanisms = {
        "CB2_activation": ["cb2 receptor", "cannabinoid receptor 2"],
        "NF-kB_suppression": ["nf-kb", "nf-κb"],
        "GABA_modulation": ["gaba", "gaba_a"],
        "transdermal_enhancement": ["transdermal", "skin permeation", "stratum corneum"],
    }
    found = []
    for mech, terms in mechanisms.items():
        if any(t in tl for t in terms):
            found.append(mech)
    return found


def extract_dose_info(abstract):
    if not abstract:
        return []
    doses = []
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(mg/kg|µg/mL|μg/mL|mg/mL|µM|μM|mM|nM|%|ppm|mg|g/L)\b',
        r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(mg/kg|µM|μM|mM|nM|%)\b',
    ]
    for p in patterns:
        for match in re.finditer(p, abstract):
            doses.append(match.group(0))
    return doses[:5]


def detect_commercial_relevance(text):
    tl = (text or "").lower()
    tags = []
    for cat, terms in COMMERCIAL_CATEGORIES.items():
        if any(term.lower() in tl for term in terms):
            tags.append(cat)
    return tags


def detect_terpenes(text):
    tl = (text or "").lower()
    found = []
    for terp in TERPENES.keys():
        variants = [terp, terp.replace('-', ' '), terp.replace('-', '')]
        if terp.startswith('alpha-'):
            variants.extend([f"α-{terp[6:]}", f"a-{terp[6:]}"])
        if terp.startswith('beta-'):
            variants.extend([f"β-{terp[5:]}", f"b-{terp[5:]}"])
        for v in variants:
            if v.lower() in tl:
                found.append(terp)
                break
    return sorted(set(found))


def detect_effects(text):
    tl = (text or "").lower()
    found = []
    for eff, info in EFFECT_ONTOLOGY.items():
        if any(term.lower() in tl for term in info["terms"]):
            found.append(eff)
    return sorted(set(found))


def score_relevance_v2(paper):
    score = 0.0
    terps = paper.get("terpenes_mentioned", []) or []
    effects = paper.get("effects_mentioned", []) or []
    study_type = paper.get("study_type", "unknown")
    ew = float(paper.get("evidence_weight", 0.2) or 0.2)

    score += len(terps) * 10 * ew
    score += len(effects) * 6 * ew

    if study_type in ("meta-analysis", "systematic_review"):
        score += 25
    elif study_type == "rct":
        score += 20
    elif study_type in ("cohort",):
        score += 10

    if paper.get("model_organism") == "human":
        score += 15

    mechs = paper.get("mechanisms_extracted", []) or []
    score += len(mechs) * 3
    if "CB2_activation" in mechs:
        score += 12
    if "transdermal_enhancement" in mechs:
        score += 10

    score += len(paper.get("commercial_tags", []) or []) * 4
    if paper.get("outcome_direction") == "positive":
        score += 5

    return round(score, 1)


# ───────────────────────────────────────────────────────────
# KB layer
# ───────────────────────────────────────────────────────────

def _hash_id(*parts):
    h = hashlib.md5("::".join([p or "" for p in parts]).encode("utf-8")).hexdigest()
    return h[:16]


class ResearchKB:
    def __init__(self, path=KB_DIR / "kb.json"):
        self.path = Path(path)
        self.data = {"papers": {}, "indexes": {"terpene": {}, "effect": {}, "mechanism": {}}, "meta": {}}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {"papers": {}, "indexes": {"terpene": {}, "effect": {}, "mechanism": {}}, "meta": {}}
        self.data.setdefault("papers", {})
        self.data.setdefault("indexes", {"terpene": {}, "effect": {}, "mechanism": {}})
        self.data.setdefault("meta", {})

    def save(self):
        self.data["meta"]["saved_at"] = datetime.utcnow().isoformat()
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def paper_id(self, paper):
        pmid = paper.get("pmid") or ""
        doi = paper.get("doi") or ""
        title = (paper.get("title") or "")[:200]
        if pmid:
            return f"pmid:{pmid}"
        if doi:
            return f"doi:{doi}"
        return f"hash:{_hash_id(title, paper.get('journal',''), paper.get('year',''))}"

    def upsert_papers(self, papers):
        added = 0
        updated = 0
        for p in papers:
            pid = self.paper_id(p)
            p["id"] = pid
            existing = self.data["papers"].get(pid)
            if existing:
                merged = dict(existing)
                merged.update({k: v for k, v in p.items() if v not in (None, "", [], {})})
                for lk in ["terpenes_mentioned", "effects_mentioned", "mechanisms_extracted", "commercial_tags"]:
                    merged[lk] = sorted(set((existing.get(lk) or []) + (p.get(lk) or [])))
                self.data["papers"][pid] = merged
                updated += 1
            else:
                self.data["papers"][pid] = p
                added += 1

        self.rebuild_indexes()
        return {"added": added, "updated": updated, "total": len(self.data["papers"]) }

    def rebuild_indexes(self):
        idx = {"terpene": defaultdict(set), "effect": defaultdict(set), "mechanism": defaultdict(set)}
        for pid, p in self.data["papers"].items():
            for t in p.get("terpenes_mentioned", []) or []:
                idx["terpene"][t].add(pid)
            for e in p.get("effects_mentioned", []) or []:
                idx["effect"][e].add(pid)
            for m in p.get("mechanisms_extracted", []) or []:
                idx["mechanism"][m].add(pid)
        self.data["indexes"] = {
            "terpene": {k: sorted(list(v)) for k, v in idx["terpene"].items()},
            "effect": {k: sorted(list(v)) for k, v in idx["effect"].items()},
            "mechanism": {k: sorted(list(v)) for k, v in idx["mechanism"].items()},
        }

    def get_papers(self, terpene=None, effect=None, mechanism=None, limit=200):
        ids = None
        if terpene:
            ids = set(self.data["indexes"]["terpene"].get(terpene, []))
        if effect:
            eids = set(self.data["indexes"]["effect"].get(effect, []))
            ids = eids if ids is None else ids & eids
        if mechanism:
            mids = set(self.data["indexes"]["mechanism"].get(mechanism, []))
            ids = mids if ids is None else ids & mids
        if ids is None:
            papers = list(self.data["papers"].values())
        else:
            papers = [self.data["papers"][pid] for pid in ids if pid in self.data["papers"]]
        papers.sort(key=lambda p: (p.get("relevance_score", 0), p.get("harvested_at", "")), reverse=True)
        return papers[:limit]

    def stats(self):
        papers = list(self.data["papers"].values())
        return {
            "papers_total": len(papers),
            "top_terpenes": Counter([t for p in papers for t in (p.get("terpenes_mentioned", []) or [])]).most_common(10),
            "top_effects": Counter([e for p in papers for e in (p.get("effects_mentioned", []) or [])]).most_common(10),
            "top_mechanisms": Counter([m for p in papers for m in (p.get("mechanisms_extracted", []) or [])]).most_common(10),
            "study_types": Counter([p.get("study_type", "unknown") for p in papers]).most_common(10),
        }


# ───────────────────────────────────────────────────────────
# PhD-ish intelligence: trends + synthesis + profiles + gaps
# ───────────────────────────────────────────────────────────

def detect_trends(kb: ResearchKB):
    papers = list(kb.data.get("papers", {}).values())
    if len(papers) < 10:
        return {"error": "Need at least 10 papers for trend analysis"}
    now = datetime.utcnow()
    recent_cutoff = (now - timedelta(days=90)).isoformat()
    older_cutoff = (now - timedelta(days=365)).isoformat()
    recent = [p for p in papers if p.get("harvested_at", "") >= recent_cutoff]
    older = [p for p in papers if older_cutoff <= p.get("harvested_at", "") < recent_cutoff]
    recent_norm = len(recent) or 1
    older_norm = len(older) or 1

    def _velocity(counter_recent, counter_older):
        out = {}
        keys = set(counter_recent) | set(counter_older)
        for k in keys:
            r = counter_recent.get(k, 0) / recent_norm
            o = counter_older.get(k, 0) / older_norm
            v = (r - o) / o if o > 0 else (1.0 if r > 0 else 0.0)
            out[k] = {"recent": counter_recent.get(k, 0), "older": counter_older.get(k, 0), "velocity": round(v, 2)}
        return out

    rt = Counter([t for p in recent for t in (p.get("terpenes_mentioned", []) or [])])
    ot = Counter([t for p in older for t in (p.get("terpenes_mentioned", []) or [])])
    re = Counter([e for p in recent for e in (p.get("effects_mentioned", []) or [])])
    oe = Counter([e for p in older for e in (p.get("effects_mentioned", []) or [])])

    tv = _velocity(rt, ot)
    ev = _velocity(re, oe)

    recent_human = sum(1 for p in recent if p.get("model_organism") == "human")
    older_human = sum(1 for p in older if p.get("model_organism") == "human")
    human_rate_change = (recent_human / recent_norm) - (older_human / older_norm)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"recent_days": 90, "papers_recent": len(recent), "papers_older": len(older)},
        "terpene_velocity_top": dict(sorted(tv.items(), key=lambda x: x[1]["velocity"], reverse=True)[:15]),
        "effect_velocity_top": dict(sorted(ev.items(), key=lambda x: x[1]["velocity"], reverse=True)[:15]),
        "rigor": {"human_rate_change": round(human_rate_change, 3)},
    }


def _evidence_numeric(grade):
    return {"A": 4, "B": 3, "C": 2, "D": 1}.get(grade or "D", 1)


def synthesize(kb: ResearchKB, days_back=30, min_cluster_size=2):
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
    papers = [p for p in kb.data["papers"].values() if p.get("harvested_at", "") >= cutoff]
    clusters = defaultdict(list)
    for p in papers:
        terps = p.get("terpenes_mentioned", []) or []
        effs = p.get("effects_mentioned", []) or []
        mechs = p.get("mechanisms_extracted", []) or []
        if not terps or not effs:
            continue
        for t in terps:
            for e in effs:
                cat = EFFECT_ONTOLOGY.get(e, {}).get("category", "other")
                if mechs:
                    for m in mechs:
                        clusters[(t, cat, m)].append(p)
                else:
                    clusters[(t, cat, "unknown_mechanism")].append(p)

    insights = []
    for (t, cat, m), items in clusters.items():
        if len(items) < min_cluster_size:
            continue
        pos = [p for p in items if p.get("outcome_direction") == "positive"]
        neg = [p for p in items if p.get("outcome_direction") == "negative"]
        human = sum(1 for p in items if p.get("model_organism") == "human")
        best_grade = max((_evidence_numeric(p.get("evidence_grade")) for p in items), default=1)
        diversity = len(set(p.get("study_type", "unknown") for p in items))
        confidence = min(6, best_grade + (1 if human else 0) + (1 if len(items) >= 3 else 0) + (1 if diversity >= 2 else 0))
        contradiction = True if (pos and neg) else False
        citations = [{"id": p["id"], "title": p.get("title", ""), "url": p.get("url", ""), "grade": p.get("evidence_grade", "D")} for p in items[:6]]
        insights.append({
            "terpene": t,
            "effect_category": cat,
            "mechanism": m,
            "paper_count": len(items),
            "human_count": human,
            "positive": len(pos),
            "negative": len(neg),
            "confidence_1to6": confidence,
            "contradiction": contradiction,
            "statement": f"{t} shows {cat.replace('_',' ')} signals via {m.replace('_',' ')} across {len(items)} recent papers.",
            "citations": citations,
        })
    insights.sort(key=lambda x: (x["confidence_1to6"], x["paper_count"]), reverse=True)
    return {"generated_at": datetime.utcnow().isoformat(), "days_back": days_back, "insights": insights[:50]}


EFFECT_TO_ONTOLOGY_KEYS = {
    "sleep": ["sedative", "anxiolytic"],
    "pain": ["analgesic", "anti-inflammatory"],
    "calm": ["anxiolytic", "sedative"],
    "uplift": ["antidepressant"],
    "topical_delivery": ["skin_permeation", "bioavailability"],
}


def build_effect_profile(kb: ResearchKB, target: str, max_components=5):
    target = (target or "").strip().lower()
    ontology = EFFECT_TO_ONTOLOGY_KEYS.get(target, [])
    if target in EFFECT_ONTOLOGY:
        ontology = [target]

    terp_scores = defaultdict(float)
    terp_support = defaultdict(list)
    for ok in ontology:
        for p in kb.get_papers(effect=ok, limit=500):
            for t in p.get("terpenes_mentioned", []) or []:
                w = (p.get("relevance_score", 0) / 100.0) * (float(p.get("evidence_weight", 0.2)) * 2.0)
                if p.get("model_organism") == "human":
                    w *= 1.25
                if p.get("outcome_direction") == "negative":
                    w *= -0.6
                terp_scores[t] += w
                terp_support[t].append(p["id"])

    ranked = sorted(terp_scores.items(), key=lambda x: x[1], reverse=True)[:max_components]
    blend = []
    for t, score in ranked:
        blend.append({
            "terpene": t,
            "score": round(score, 3),
            "supporting_papers": terp_support[t][:8],
            "known_effects": TERPENES.get(t, {}).get("known_effects", []),
        })
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "target": target,
        "blend_recommendation": blend,
        "notes": [
            "Evidence-weighted ranking from abstracts/metadata; validate with formulation tests.",
            "Use compliance-safe framing externally; avoid disease/therapeutic claims.",
        ],
    }


def gap_analysis(kb: ResearchKB):
    papers = list(kb.data["papers"].values())
    evidence_counts = Counter([t for p in papers for t in (p.get("terpenes_mentioned", []) or [])])
    tbf_focus = Counter({t: len(meta.get("tbf_products", []) or []) for t, meta in TERPENES.items()})
    gaps = []
    for t, ev_ct in evidence_counts.items():
        focus = tbf_focus.get(t, 0)
        gap = (ev_ct / max(1, sum(evidence_counts.values()))) - (focus / max(1, sum(tbf_focus.values())))
        gaps.append({"terpene": t, "evidence_count": ev_ct, "focus_units": focus, "gap_score": round(gap, 4)})
    gaps.sort(key=lambda x: x["gap_score"], reverse=True)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "underweighted_by_tbf": gaps[:15],
        "overweighted_by_tbf": sorted(gaps, key=lambda x: x["gap_score"])[:15],
    }


REGULATORY_WATCHLIST = [
    {"topic": "inhalation_toxicology", "terms": ["inhalation toxicity", "respiratory irritation", "diacetyl", "vitamin e acetate"]},
    {"topic": "food_additive", "terms": ["food additive", "GRAS", "FEMA"]},
    {"topic": "claims_enforcement", "terms": ["warning letter", "unsubstantiated claims", "treat", "cure"]},
]


def regulatory_radar(kb: ResearchKB):
    hits = []
    for p in list(kb.data["papers"].values())[:1000]:
        text = f"{p.get('title','')} {p.get('abstract','')}".lower()
        matched = []
        for rule in REGULATORY_WATCHLIST:
            if any(term.lower() in text for term in rule["terms"]):
                matched.append(rule["topic"])
        if matched:
            hits.append({"paper_id": p["id"], "title": p.get("title", ""), "url": p.get("url", ""), "topics": sorted(set(matched))})
    return {"generated_at": datetime.utcnow().isoformat(), "regulatory_hits": hits[:50]}


def competitive_intel(kb: ResearchKB):
    claims = []
    for t, meta in TERPENES.items():
        moat = meta.get("competitive_moat")
        if not moat:
            continue
        supporting = kb.get_papers(terpene=t, limit=50)
        grades = Counter([p.get("evidence_grade", "D") for p in supporting])
        claims.append({
            "terpene": t,
            "claim": moat,
            "supporting_evidence": dict(grades),
            "top_papers": [{"id": p["id"], "url": p.get("url", ""), "grade": p.get("evidence_grade", "D")} for p in supporting[:5]],
        })
    return {"generated_at": datetime.utcnow().isoformat(), "claims": claims}


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def write_md(path: Path, lines):
    path.write_text("\n".join(lines), encoding="utf-8")


def build_matrix(kb: ResearchKB, top_n=12):
    st = kb.stats()
    top_terps = [t for t, _ in st["top_terpenes"][:top_n]]
    top_effects = [e for e, _ in st["top_effects"][:top_n]]
    matrix = []
    for t in top_terps:
        row = {"terpene": t}
        for e in top_effects:
            ids = set(kb.data["indexes"]["terpene"].get(t, [])) & set(kb.data["indexes"]["effect"].get(e, []))
            row[e] = len(ids)
        matrix.append(row)
    return {"generated_at": datetime.utcnow().isoformat(), "top_terpenes": top_terps, "top_effects": top_effects, "matrix": matrix}


def build_digest(kb: ResearchKB, days_back=30):
    syn = synthesize(kb, days_back=days_back)
    lines = [
        "# Terpene Research Digest",
        f"_Generated: {datetime.utcnow().isoformat()}Z | Window: last {days_back} days_",
        "",
    ]
    for i, ins in enumerate(syn["insights"][:10], 1):
        lines.append(f"## {i}. {ins['terpene']} — {ins['effect_category'].replace('_',' ')} ({ins['mechanism']})")
        lines.append(f"- Confidence (1–6): **{ins['confidence_1to6']}** | Papers: **{ins['paper_count']}** | Human: **{ins['human_count']}**")
        if ins["contradiction"]:
            lines.append("- ⚠️ Mixed outcomes detected; treat as hypothesis.")
        lines.append("**Citations:**")
        for c in ins["citations"]:
            lines.append(f"- [{c['grade']}] {c['title'][:160]} — {c['url']}")
        lines.append("")
    return {"markdown": "\n".join(lines), "data": syn}


def build_executive_brief(kb: ResearchKB, days_back=30):
    trends = detect_trends(kb)
    syn = synthesize(kb, days_back=days_back)
    gaps = gap_analysis(kb)
    lines = [
        "# Executive Brief — Terpene Research Intelligence",
        f"_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
        "## What changed recently",
    ]
    if "error" not in trends:
        tv = list(trends["terpene_velocity_top"].items())[:5]
        ev = list(trends["effect_velocity_top"].items())[:5]
        lines.append("**Accelerating terpenes:** " + ", ".join([f"{t} ({v['velocity']:+.2f})" for t, v in tv]))
        lines.append("**Accelerating effects:** " + ", ".join([f"{e} ({v['velocity']:+.2f})" for e, v in ev]))
        lines.append(f"**Rigor trend:** human evidence rate change = {trends['rigor']['human_rate_change']:+.3f}")
    else:
        lines.append("Not enough papers for trend analysis yet.")
    lines += ["", "## Top convergences (synthesis)"]
    for ins in syn["insights"][:5]:
        lines.append(f"- **{ins['terpene']}** in **{ins['effect_category'].replace('_',' ')}** via **{ins['mechanism']}** — confidence {ins['confidence_1to6']}/6")
    lines += ["", "## Gaps (evidence vs TBF focus heuristic)"]
    for g in gaps["underweighted_by_tbf"][:5]:
        lines.append(f"- {g['terpene']}: evidence_count={g['evidence_count']} vs focus_units={g['focus_units']} (gap={g['gap_score']})")
    lines += [
        "",
        "## Compliance-safe commercialization notes",
        "- Use formulation advantages + sensory descriptors + consumer-perceived effect language externally.",
        "- Avoid therapeutic/disease claims; keep internal research claims behind validation plans.",
        "",
    ]
    return "\n".join(lines)


def build_talking_points(kb: ResearchKB, target="pain"):
    prof = build_effect_profile(kb, target)
    lines = [
        f"# Talking Points — {target.title()} (Evidence-Weighted)",
        f"_Generated: {datetime.utcnow().isoformat()}Z_",
        "",
    ]
    for item in prof["blend_recommendation"]:
        lines.append(f"## {item['terpene']}")
        lines.append(f"- Evidence score: **{item['score']}** | Supporting papers: **{len(item['supporting_papers'])}**")
        lines.append("- Safe framing: formulation/sensory/consumer-perceived effect language (no therapeutic claims).")
        lines.append("")
    return "\n".join(lines)


def harvest(days=90, max_results=25):
    all_papers = []
    for q in RESEARCH_TOPICS:
        all_papers.extend(search_pubmed(q, max_results=max_results, days_back=days))
    return all_papers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--max-results", type=int, default=20)
    ap.add_argument("--harvest", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--synthesize", action="store_true")
    ap.add_argument("--trends", action="store_true")
    ap.add_argument("--profile", type=str, default="")
    ap.add_argument("--gaps", action="store_true")
    ap.add_argument("--regulatory", action="store_true")
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--matrix", action="store_true")
    ap.add_argument("--talking-points", action="store_true")
    ap.add_argument("--executive-brief", action="store_true")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    kb = ResearchKB()
    did = False

    if args.harvest or args.full:
        did = True
        print(f"\n🔎 Harvesting PubMed (days={args.days}, max_results/topic={args.max_results}) ...")
        papers = harvest(days=args.days, max_results=args.max_results)
        print(f"  Pulled {len(papers)} raw papers")
        res = kb.upsert_papers(papers)
        kb.save()
        print(f"  KB updated: {res}")

    if args.stats:
        did = True
        write_json(REPORTS_DIR / "kb_stats.json", kb.stats())

    if args.trends or args.full:
        did = True
        write_json(INSIGHTS_DIR / "trends.json", detect_trends(kb))

    if args.synthesize or args.full:
        did = True
        write_json(INSIGHTS_DIR / "synthesis.json", synthesize(kb, days_back=min(args.days, 60)))

    if args.profile:
        did = True
        safe = re.sub(r"[^a-z0-9]+", "_", args.profile.lower()).strip("_")
        write_json(INSIGHTS_DIR / f"effect_profile_{safe}.json", build_effect_profile(kb, args.profile))

    if args.gaps or args.full:
        did = True
        write_json(INSIGHTS_DIR / "gaps.json", gap_analysis(kb))

    if args.regulatory or args.full:
        did = True
        write_json(INSIGHTS_DIR / "regulatory.json", regulatory_radar(kb))

    if args.matrix or args.full:
        did = True
        write_json(REPORTS_DIR / "terpene_effect_matrix.json", build_matrix(kb))

    if args.digest or args.full:
        did = True
        d = build_digest(kb, days_back=min(args.days, 60))
        write_md(REPORTS_DIR / "digest.md", d["markdown"].splitlines())
        write_json(REPORTS_DIR / "digest.json", d["data"])

    if args.talking_points:
        did = True
        tp = build_talking_points(kb, target=args.profile or "pain")
        write_md(REPORTS_DIR / "talking_points.md", tp.splitlines())

    if args.executive_brief or args.full:
        did = True
        eb = build_executive_brief(kb, days_back=min(args.days, 60))
        write_md(REPORTS_DIR / "executive_brief.md", eb.splitlines())

    if args.full:
        did = True
        write_json(INSIGHTS_DIR / "competitive.json", competitive_intel(kb))

    if not did:
        ap.print_help()
        print("\nTip: run --full --days 90 to generate everything.\n")


if __name__ == "__main__":
    main()
