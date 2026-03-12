#!/usr/bin/env python3
"""
Merge v1 terpene_kb.json into v2 kb.json — one-time migration.
Run from the nexus-bdr-agent directory:
    python3 scripts/merge_research_kb.py
"""
import json, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
KB_DIR = SCRIPT_DIR / "outputs" / "terpene_research" / "knowledge_base"

v1_path = KB_DIR / "terpene_kb.json"
v2_path = KB_DIR / "kb.json"

if not v2_path.exists():
    print("No kb.json found. Nothing to merge into.")
    sys.exit(1)

v2 = json.loads(v2_path.read_text())
v2_papers = v2.get("papers", {})
before = len(v2_papers)

if v1_path.exists():
    v1 = json.loads(v1_path.read_text())
    v1_papers = v1.get("papers", {})
    merged = 0
    for pmid, paper in v1_papers.items():
        pid = f"pmid:{pmid}" if not pmid.startswith("pmid:") else pmid
        if pid not in v2_papers:
            # Add v1 paper with basic fields if missing from v2
            paper["id"] = pid
            paper.setdefault("evidence_grade", "D")
            paper.setdefault("evidence_weight", 0.2)
            paper.setdefault("study_type", "unknown")
            paper.setdefault("mechanisms_extracted", [])
            paper.setdefault("commercial_tags", [])
            paper.setdefault("dose_info", [])
            paper.setdefault("model_organism", "unknown")
            paper.setdefault("outcome_direction", "unknown")
            v2_papers[pid] = paper
            merged += 1

    v2["papers"] = v2_papers
    v2_path.write_text(json.dumps(v2, indent=2))
    print(f"Merged {merged} v1 papers into kb.json")
    print(f"Before: {before} | After: {len(v2_papers)}")

    # Rename v1 file so it doesn't get re-merged
    v1_path.rename(KB_DIR / "terpene_kb_v1_archived.json")
    print(f"Archived v1 file as terpene_kb_v1_archived.json")
else:
    print("No terpene_kb.json found. Nothing to merge.")
