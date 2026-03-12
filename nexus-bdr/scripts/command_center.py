#!/usr/bin/env python3
"""
NEXUS COMMAND CENTER — Server + Dashboard
==========================================
Local server that:
  1. Serves the interactive dashboard UI
  2. Reads actual pipeline data from outputs/
  3. Scans agent scripts and their metadata
  4. Proxies Claude API for the PM chat interface
  5. Can dispatch agent runs from the UI

Usage:
    python3 command_center.py
    python3 command_center.py --port 8888

Then open: http://localhost:3141
"""

import os, sys, json, glob, time, subprocess, threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse

try:
    import requests
except ImportError:
    requests = None

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-5-20250929"

SKILL_DIR = Path(__file__).parent.resolve().parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
OUTPUT_DIR = SKILL_DIR / "outputs"
REFS_DIR = SKILL_DIR / "references"
CONFIG_DIR = SKILL_DIR / "config"

# Terpene research intelligence outputs
RESEARCH_DIR = OUTPUT_DIR / "terpene_research"
RESEARCH_REPORTS_DIR = RESEARCH_DIR / "reports"
RESEARCH_INSIGHTS_DIR = RESEARCH_DIR / "insights"

# ─── DATA LOADERS ─────────────────────────────────────────

def load_pipeline_data():
    """Load the most recent scored Apollo data."""
    scored_files = sorted(glob.glob(str(OUTPUT_DIR / "scored_apollo_*.json")), reverse=True)
    if scored_files:
        with open(scored_files[0]) as f:
            data = json.load(f)
        return data.get("leads", []), scored_files[0]

    # Fallback to enriched or imported
    for pattern in ["enriched_*.json", "imported_*.json"]:
        files = sorted(glob.glob(str(OUTPUT_DIR / pattern)), reverse=True)
        if files:
            with open(files[0]) as f:
                data = json.load(f)
            return data.get("leads", data.get("prospects", [])), files[0]
    return [], None


def load_agent_registry():
    """Scan scripts directory for all agents."""
    agents = []
    if not SCRIPTS_DIR.exists():
        return agents
    for py in sorted(SCRIPTS_DIR.glob("*.py")):
        with open(py) as f:
            first_lines = f.read(2000)
        # Extract docstring
        desc = ""
        if '"""' in first_lines:
            parts = first_lines.split('"""')
            if len(parts) >= 2:
                desc = parts[1].strip().split("\n")[0]
        # Version detection
        version = "v1"
        for line in first_lines.split("\n"):
            if "version" in line.lower() or "v2" in line.lower() or "v3" in line.lower():
                for v in ["v5", "v4", "v3", "v2"]:
                    if v in line.lower():
                        version = v
                        break

        stat = py.stat()
        agents.append({
            "id": py.stem,
            "file": py.name,
            "path": str(py),
            "description": desc[:120],
            "version": version,
            "size_kb": round(stat.st_size / 1024, 1),
            "lines": sum(1 for _ in open(py)),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return agents


def load_recent_outputs():
    """Load recent output files as activity log."""
    activities = []
    if not OUTPUT_DIR.exists():
        return activities
    for f in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.is_file() and f.suffix == ".json":
            stat = f.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)

            # Determine type
            ftype = "data"
            if "scored" in f.name: ftype = "scored_pipeline"
            elif "enriched" in f.name: ftype = "enriched_data"
            elif "imported" in f.name: ftype = "import"
            elif "brief" in f.name: ftype = "sales_brief"
            elif "digest" in f.name: ftype = "digest"
            elif "scan" in f.name: ftype = "social_scan"
            elif "dashboard" in f.name: continue

            # Try to extract summary
            summary = ""
            try:
                with open(f) as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    meta = data.get("metadata", {})
                    if meta.get("total"):
                        summary = f"{meta['total']} leads"
                    if meta.get("hot"):
                        summary += f" | {meta['hot']} hot, {meta.get('warm',0)} warm"
            except:
                pass

            activities.append({
                "file": f.name,
                "path": str(f),
                "type": ftype,
                "size_kb": round(size / 1024, 1),
                "modified": modified.strftime("%Y-%m-%d %H:%M"),
                "modified_ts": stat.st_mtime,
                "summary": summary,
            })
    return activities[:30]


def load_research_intel():
    """Load latest terpene research outputs (v1/v2 engines)."""
    payload = {
        "paths": {
            "research_dir": str(RESEARCH_DIR),
            "reports_dir": str(RESEARCH_REPORTS_DIR),
            "insights_dir": str(RESEARCH_INSIGHTS_DIR),
        },
        "reports": {},
        "insights": {},
        "listing": {"reports": [], "insights": []},
        "available": False,
        "top_papers": [],
        "kb_stats": None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if not RESEARCH_DIR.exists():
        return payload

    payload["available"] = True

    def _read_text(p: Path, max_chars=20000):
        try:
            return p.read_text(encoding="utf-8")[:max_chars]
        except Exception:
            return ""

    def _read_json(p: Path):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    report_files = {
        "digest_md": RESEARCH_REPORTS_DIR / "digest.md",
        "executive_brief_md": RESEARCH_REPORTS_DIR / "executive_brief.md",
        "talking_points_md": RESEARCH_REPORTS_DIR / "talking_points.md",
        "matrix_json": RESEARCH_REPORTS_DIR / "terpene_effect_matrix.json",
        "kb_stats_json": RESEARCH_REPORTS_DIR / "kb_stats.json",
        "digest_json": RESEARCH_REPORTS_DIR / "digest.json",
    }
    for k, p in report_files.items():
        
        if p.exists():
            payload["reports"][k] = {
                "path": str(p),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "content": _read_text(p) if p.suffix in (".md", ".txt") else _read_json(p),
            }

    # Convenience: expose kb_stats_json content directly
    if payload["reports"].get("kb_stats_json") and isinstance(payload["reports"]["kb_stats_json"].get("content"), dict):
        payload["kb_stats"] = payload["reports"]["kb_stats_json"]["content"]

    # Try to compute top papers by relevance from KB (if present)
    kb_path = RESEARCH_DIR / "knowledge_base" / "kb.json"
    if kb_path.exists():
        kb_obj = _read_json(kb_path)
        if kb_obj and isinstance(kb_obj, dict):
            papers = list((kb_obj.get("papers") or {}).values())
            papers.sort(key=lambda p: (p.get("relevance_score", 0), p.get("harvested_at", "")), reverse=True)
            top = []
            for p in papers[:25]:
                top.append({
                    "title": p.get("title",""),
                    "journal": p.get("journal",""),
                    "year": p.get("year",""),
                    "evidenceGrade": p.get("evidence_grade","D"),
                    "studyType": p.get("study_type",""),
                    "modelOrganism": p.get("model_organism",""),
                    "outcomeDirection": p.get("outcome_direction",""),
                    "score": int(p.get("relevance_score", 0) or 0),
                    "url": p.get("url",""),
                    "terpenes": p.get("terpenes_mentioned", []) or [],
                    "mechanisms": p.get("mechanisms_extracted", []) or [],
                    "commercialTags": p.get("commercial_tags", []) or [],
                })
            payload["top_papers"] = top

    insight_files = {
        "trends": RESEARCH_INSIGHTS_DIR / "trends.json",
        "synthesis": RESEARCH_INSIGHTS_DIR / "synthesis.json",
        "gaps": RESEARCH_INSIGHTS_DIR / "gaps.json",
        "regulatory": RESEARCH_INSIGHTS_DIR / "regulatory.json",
        "competitive": RESEARCH_INSIGHTS_DIR / "competitive.json",
    }
    for k, p in insight_files.items():
        if p.exists():
            payload["insights"][k] = {
                "path": str(p),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "data": _read_json(p),
            }

    def _list_dir(d: Path):
        if not d.exists():
            return []
        out = []
        for f in sorted(d.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file() and f.suffix in (".md", ".json"):
                out.append({
                    "file": f.name,
                    "path": str(f),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
        return out[:50]

    payload["listing"] = {
        "reports": _list_dir(RESEARCH_REPORTS_DIR),
        "insights": _list_dir(RESEARCH_INSIGHTS_DIR),
    }

    return payload


def load_references():
    """Load reference docs."""
    refs = []
    if not REFS_DIR.exists():
        return refs
    for f in REFS_DIR.iterdir():
        if f.is_file():
            refs.append({
                "file": f.name,
                "path": str(f),
                "size_kb": round(f.stat().st_size / 1024, 1),
            })
    return refs


def compute_pipeline_stats(leads):
    """Compute summary stats from leads."""
    if not leads:
        return {}

    scores = [l.get("nexus_lead_score", 0) for l in leads]
    hot = sum(1 for s in scores if s >= 80)
    warm = sum(1 for s in scores if 60 <= s < 80)
    cool = sum(1 for s in scores if 40 <= s < 60)
    cold = sum(1 for s in scores if s < 40)
    tbf = sum(1 for l in leads if l.get("nexus_brand") == "TBF")
    dft = sum(1 for l in leads if l.get("nexus_brand") == "DFT")
    has_email = sum(1 for l in leads if l.get("email"))
    verified = sum(1 for l in leads if isinstance(l.get("email_verification"), dict) and l["email_verification"].get("status") == "valid")
    invalid = sum(1 for l in leads if isinstance(l.get("email_verification"), dict) and l["email_verification"].get("status") == "invalid")

    # Group by company
    companies = {}
    for l in leads:
        co = l.get("company_name", "Unknown")
        if co not in companies:
            companies[co] = {"name": co, "contacts": 0, "scores": [], "brand": l.get("nexus_brand", "?"), "state": l.get("state", ""), "emails": 0, "top_score": 0, "top_person": ""}
        companies[co]["contacts"] += 1
        companies[co]["scores"].append(l.get("nexus_lead_score", 0))
        if l.get("email"):
            companies[co]["emails"] += 1
        if l.get("nexus_lead_score", 0) > companies[co]["top_score"]:
            companies[co]["top_score"] = l.get("nexus_lead_score", 0)
            companies[co]["top_person"] = l.get("contact_name", "")

    company_list = []
    for co in companies.values():
        co["avg_score"] = round(sum(co["scores"]) / len(co["scores"])) if co["scores"] else 0
        del co["scores"]
        company_list.append(co)
    company_list.sort(key=lambda x: (-x["avg_score"], -x["contacts"]))

    return {
        "total": len(leads),
        "hot": hot, "warm": warm, "cool": cool, "cold": cold,
        "tbf": tbf, "dft": dft,
        "has_email": has_email, "verified": verified, "invalid": invalid,
        "avg_score": round(sum(scores) / len(scores)) if scores else 0,
        "companies": company_list[:20],
    }


def build_system_status():
    """Check what's connected."""
    status = {
        "anthropic": {"connected": bool(ANTHROPIC_API_KEY), "has_credits": False},
        "ghl": {"connected": bool(os.getenv("GHL_API_TOKEN")), "token_set": bool(os.getenv("GHL_API_TOKEN"))},
        "hunter": {"connected": bool(os.getenv("HUNTER_API_KEY"))},
        "reddit": {"connected": True, "note": "Free public API"},
    }

    # Test Anthropic credits
    if ANTHROPIC_API_KEY and requests:
        try:
            r = requests.post("https://api.anthropic.com/v1/messages",
                headers={"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"},
                json={"model":MODEL,"max_tokens":5,"messages":[{"role":"user","content":"hi"}]},
                timeout=10)
            status["anthropic"]["has_credits"] = r.status_code == 200
            if r.status_code != 200:
                try:
                    status["anthropic"]["error"] = r.json().get("error",{}).get("message","")[:100]
                except:
                    pass
        except:
            pass

    return status


# ─── CHAT ENGINE ──────────────────────────────────────────

def handle_chat(message, leads, stats, agents):
    """Process chat message — local commands or Claude API."""
    msg = message.strip()
    cmd = msg.lower()

    # Local commands that always work
    if cmd in ("/help", "help"):
        return format_help()
    if cmd in ("/agents", "agents", "list agents"):
        return format_agents(agents)
    if cmd in ("/pipeline", "pipeline", "pipeline summary"):
        return format_pipeline(stats)
    if cmd in ("/status", "status", "system status"):
        return format_status()
    if cmd.startswith("/top") or cmd.startswith("top "):
        n = 10
        parts = cmd.split()
        if len(parts) > 1:
            try: n = int(parts[1])
            except: pass
        return format_top(stats, n)
    if cmd.startswith("/company ") or cmd.startswith("company "):
        name = msg.split(" ", 1)[1] if " " in msg else ""
        return format_company(name, leads, stats)
    if cmd in ("/workflows", "workflows"):
        return format_workflows()
    if cmd.startswith("/find ") or cmd.startswith("find "):
        term = msg.split(" ", 1)[1] if " " in msg else ""
        return search_leads(term, leads)

    # Try Claude API if available
    if ANTHROPIC_API_KEY and requests:
        return ask_claude_pm(message, leads, stats, agents)

    # Fallback: try to answer common questions locally
    if "mellow" in cmd and "fellow" in cmd:
        return format_company("mellow fellow", leads, stats)
    if "what should" in cmd or "next step" in cmd or "what now" in cmd or "priority" in cmd:
        return format_priorities(stats)
    if "credit" in cmd or "api" in cmd:
        return "**Anthropic API:** No credits loaded. Add at https://console.anthropic.com/settings/billing\n\nWithout credits, these agents are offline:\n- Sales Intel Brief (6 Claude calls/brief)\n- Social Intel Claude analysis\n- Enrichment Pipeline\n\n**Still working:** Apollo Pipeline, Reddit harvest, Hunter verification, GHL sync, Dashboard"

    return "I'm in offline mode (no API credits for AI responses). Try these commands:\n\n`/pipeline` — Pipeline overview\n`/agents` — All agents\n`/top 10` — Top prospects\n`/company [name]` — Company details\n`/find [term]` — Search contacts\n`/workflows` — GHL workflow status\n`/status` — System health\n`/help` — All commands"


def ask_claude_pm(message, leads, stats, agents):
    """Send message to Claude with full pipeline context."""
    # Build context
    top_leads = sorted(leads, key=lambda l: l.get("nexus_lead_score", 0), reverse=True)[:20]
    lead_summary = "\n".join([
        f"- {l.get('company_name','?')} | {l.get('contact_name','?')} | Score:{l.get('nexus_lead_score',0)} | {l.get('nexus_brand','?')} | {l.get('email','no email')}"
        for l in top_leads
    ])

    agent_summary = "\n".join([f"- {a['file']} ({a['version']}) — {a['description'][:60]}" for a in agents])

    system = f"""You are the Nexus Project Manager — the AI brain coordinating a BDR (Business Development Representative) system for Nexus Agriscience, which sells botanical terpenes through two brands: Terpene Belt Farms (TBF, premium/enterprise) and Duty Free Terps (DFT, craft/smaller operators).

CURRENT PIPELINE STATE:
{json.dumps(stats, indent=1, default=str)[:2000]}

TOP 20 LEADS:
{lead_summary}

AGENT FLEET ({len(agents)} agents):
{agent_summary}

SYSTEM STATUS:
- GHL CRM: {'Connected' if os.getenv('GHL_API_TOKEN') else 'Not connected'}
- Hunter: {'Connected' if os.getenv('HUNTER_API_KEY') else 'Not connected'}
- Anthropic API: Connected (you're running right now)
- Reddit: Active (free API)

Be specific, actionable, and reference actual data. When suggesting commands, give the exact terminal command to run. Format responses with **bold** for headers and `code` for commands."""

    try:
        headers = {"Content-Type":"application/json","x-api-key":ANTHROPIC_API_KEY,"anthropic-version":"2023-06-01"}
        payload = {"model":MODEL,"max_tokens":1500,"system":system,"messages":[{"role":"user","content":message}]}
        resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return "\n".join(b["text"] for b in resp.json().get("content",[]) if b.get("type") == "text")
        else:
            error = ""
            try: error = resp.json().get("error",{}).get("message","")[:100]
            except: pass
            return f"API Error ({resp.status_code}): {error}\n\nFalling back to local mode. Try /help for available commands."
    except Exception as e:
        return f"Connection error: {str(e)[:100]}\n\nFalling back to local mode. Try /help for available commands."


# ─── FORMATTERS ───────────────────────────────────────────

def format_help():
    return """**Nexus PM Commands:**

`/pipeline` — Pipeline overview with stats
`/agents` — List all agents with status
`/top [n]` — Top N prospects (default 10)
`/company [name]` — Deep look at a company
`/find [term]` — Search contacts by name/email/title
`/workflows` — GHL workflow blueprint status
`/status` — System health and API connections
`/help` — This help menu

**Natural language** also works when API credits are loaded — ask anything about your pipeline, strategy, or next steps."""


def format_agents(agents):
    icons = {"orchestrator":"🎯","sales_intel_brief":"🧠","social_intel_engine":"📡","apollo_pipeline":"🚀",
             "enrich_pipeline":"🔬","csv_importer":"📋","instagram_agent":"📸","trigger_monitor":"⚡",
             "claude_researcher":"🔍","ghl_sync":"🔗","ghl_setup_properties":"🏗️","generate_dashboard":"📊",
             "command_center":"🖥️"}
    lines = [f"**Agent Fleet — {len(agents)} agents:**\n"]
    for a in agents:
        icon = icons.get(a["id"], "⚙️")
        lines.append(f"{icon} **{a['id']}** `{a['version']}` — {a['description'][:60]}")
        lines.append(f"   `{a['file']}` | {a['lines']} lines | Modified: {a['modified']}")
    return "\n".join(lines)


def format_pipeline(stats):
    if not stats:
        return "No pipeline data found. Run:\n`python3 scripts/apollo_pipeline.py --input outputs/imported_*.json`"

    lines = [
        f"**Pipeline: {stats['total']} contacts**\n",
        f"🔥 Hot: **{stats['hot']}** | 🟡 Warm: **{stats['warm']}** | 🔵 Cool: **{stats['cool']}** | ⚪ Cold: **{stats['cold']}**",
        f"🏷️ TBF: {stats['tbf']} | DFT: {stats['dft']}",
        f"📧 Has email: {stats['has_email']} | ✅ Verified: {stats['verified']} | ❌ Invalid: {stats['invalid']}",
        f"📊 Average score: {stats['avg_score']}",
        "\n**Top Accounts:**",
    ]
    for i, co in enumerate(stats.get("companies", [])[:10], 1):
        lines.append(f"{i}. **{co['name']}** — {co['contacts']} contacts, avg {co['avg_score']}, {co['brand']}, {co.get('state','?')[:2].upper()}")
    return "\n".join(lines)


def format_top(stats, n=10):
    companies = stats.get("companies", [])[:n]
    lines = [f"**Top {n} Accounts:**\n"]
    for i, co in enumerate(companies, 1):
        lines.append(f"{i}. **{co['name']}** ({co['brand']}) — {co['contacts']} contacts, avg score {co['avg_score']}, top: {co.get('top_person','?')}, {co.get('state','?')[:2].upper()}, {co['emails']} emails")
    return "\n".join(lines)


def format_company(name, leads, stats):
    matches = [l for l in leads if name.lower() in (l.get("company_name","") or "").lower()]
    if not matches:
        return f"No contacts found for \"{name}\". Try `/find {name}` for broader search."

    co_name = matches[0].get("company_name", name)
    lines = [f"**{co_name}** — {len(matches)} contacts\n"]

    scores = [m.get("nexus_lead_score", 0) for m in matches]
    lines.append(f"📊 Avg score: {round(sum(scores)/len(scores))} | Brand: {matches[0].get('nexus_brand','?')}")
    lines.append(f"📍 {matches[0].get('state','?')} | 🌐 {matches[0].get('domain','?')}\n")
    lines.append("**Contacts:**")

    matches.sort(key=lambda l: l.get("nexus_lead_score", 0), reverse=True)
    for m in matches:
        email_status = ""
        ev = m.get("email_verification")
        if isinstance(ev, dict):
            email_status = f" [{ev.get('status','?')}]"
        email = m.get("email", "no email") + email_status
        lines.append(f"- **{m.get('contact_name','?')}** | {m.get('title','?')[:30]} | Score: {m.get('nexus_lead_score',0)} | {m.get('decision_maker_level','')} | {email}")

    lines.append(f"\n**Run deep brief:**\n`python3 scripts/sales_intel_brief.py --company \"{co_name}\"`")
    return "\n".join(lines)


def search_leads(term, leads):
    term_lower = term.lower()
    matches = [l for l in leads if
        term_lower in (l.get("company_name","") or "").lower() or
        term_lower in (l.get("contact_name","") or "").lower() or
        term_lower in (l.get("email","") or "").lower() or
        term_lower in (l.get("title","") or "").lower() or
        term_lower in (l.get("state","") or "").lower()
    ]
    if not matches:
        return f"No results for \"{term}\"."
    lines = [f"**Search: \"{term}\" — {len(matches)} results:**\n"]
    for m in matches[:15]:
        lines.append(f"- **{m.get('contact_name','?')}** at {m.get('company_name','?')} | Score: {m.get('nexus_lead_score',0)} | {m.get('email','no email')}")
    return "\n".join(lines)


def format_workflows():
    bp_path = REFS_DIR / "ghl-workflow-blueprint.md"
    exists = bp_path.exists()
    return f"""**GHL Workflow Blueprint:** {'✅ Generated' if exists else '❌ Not found'}
{'📄 ' + str(bp_path) if exists else 'Run: python3 scripts/apollo_pipeline.py --blueprint-only'}

**10 Workflows to Build:**
1. Auto-Tag by Score Tier
2. TBF Outreach Sequence (4-touch)
3. DFT Outreach Sequence (4-touch)
4. Engagement Escalation
5. Reply Handler
6. Re-engagement (30-day stale)
7. Sample Follow-Up
8. Trade Show Pre-Event
9. Weekly Pipeline Report
10. Hot Lead Alert (SMS + Email)

Open blueprint: `open references/ghl-workflow-blueprint.md`"""


def format_status():
    status = build_system_status()
    lines = ["**System Status:**\n"]
    for name, s in status.items():
        if s.get("connected"):
            emoji = "✅"
            note = s.get("note", "Connected")
            if name == "anthropic":
                note = "Has credits" if s.get("has_credits") else f"No credits — {s.get('error','add at console.anthropic.com')}"
                emoji = "✅" if s.get("has_credits") else "⚠️"
        else:
            emoji = "❌"
            note = "Not configured"
        lines.append(f"{emoji} **{name.title()}**: {note}")
    return "\n".join(lines)


def format_priorities(stats):
    lines = ["**Priority Actions:**\n"]
    lines.append("1. 🔧 **Build GHL workflows** — `open references/ghl-workflow-blueprint.md`")
    lines.append("2. 💰 **Add Anthropic credits** ($20) — unlocks Sales Brief + Social Intel + Enrichment")

    companies = stats.get("companies", [])
    if companies:
        top = companies[0]
        lines.append(f"3. 🎯 **Outreach {top['name']}** — {top['contacts']} contacts, avg score {top['avg_score']}")

    lines.append("4. 🔍 **Run Hunter email finder** on hot leads missing emails")
    lines.append("5. 📡 **Test social intel** — `python3 scripts/social_intel_engine.py --quick-scan`")
    return "\n".join(lines)


# ─── HTTP SERVER ──────────────────────────────────────────

class CommandCenterHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_dashboard_html().encode())

        elif path == "/api/data":
            leads, source = load_pipeline_data()
            agents = load_agent_registry()
            outputs = load_recent_outputs()
            refs = load_references()
            stats = compute_pipeline_stats(leads)
            status = build_system_status()
            research = load_research_intel()

            payload = {
                "pipeline": {"leads": leads, "source": source, "stats": stats},
                "agents": agents,
                "outputs": outputs,
                "references": refs,
                "system": status,
                "research": research,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(payload, default=str).encode())

        elif path == "/reef" or path == "/reef/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_reef_html().encode())

        elif path == "/api/reef/snapshot":
            leads, source = load_pipeline_data()
            stats = compute_pipeline_stats(leads)
            research = load_research_intel()

            # Minimal snapshot contract for ReefMode:
            # Priorities come from top scored leads (if present)
            priorities = []
            if leads:
                # sort by nexus_lead_score descending
                ranked = sorted(leads, key=lambda x: x.get("nexus_lead_score", 0), reverse=True)[:10]
                for i, l in enumerate(ranked, 1):
                    company = l.get("company") or l.get("company_name") or l.get("name") or "Unknown"
                    domain = l.get("domain") or l.get("website") or ""
                    score = int(l.get("nexus_lead_score", 0) or 0)
                    tier = "hot" if score >= 80 else "warm" if score >= 60 else "cool" if score >= 40 else "cold"
                    priorities.append({
                        "rank": i,
                        "company": company,
                        "domain": domain,
                        "score": score,
                        "tier": tier,
                        "contacts": int(l.get("contacts", 0) or 0),
                        "verified": bool(l.get("email")),
                        "briefComplete": False,
                        "nextAction": "run_brief",
                        "actionId": None,
                        "currentSupplier": "",
                        "features": [],
                        "whyNow": "Top pipeline-ranked target based on lead score and ICP fit signals.",
                    })

            payload = {
                "systemStatus": {
                    "pipelineLeads": int(stats.get("total_leads", len(leads) if leads else 0) or 0),
                    "hotLeads": int(stats.get("hot", 0) or 0),
                    "activeSignals": 0,
                    "briefsCompleted": 0,
                    "outcomesRecordedToday": 0,
                    "lastUpdate": datetime.utcnow().isoformat(),
                    "researchPapers": (research.get("reports", {}).get("kb_stats_json", {}).get("content", {}) or {}).get("papers_total", 0),
                },
                "priorities": priorities,
                "competitors": [],
                "signals": [],
                "learning": {"signalWeights": {}},
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(payload, default=str).encode())

        elif path == "/api/reef/research":
            payload = load_research_intel()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(payload, default=str).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            message = body.get("message", "")

            leads, _ = load_pipeline_data()
            agents = load_agent_registry()
            stats = compute_pipeline_stats(leads)

            response = handle_chat(message, leads, stats, agents)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"response": response}).encode())

        elif parsed.path == "/api/run":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            command = body.get("command", "")

            # Security: only allow running scripts from our directory
            if not command.startswith("python3 scripts/"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid command"}).encode())
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "queued", "command": command, "note": "Run this in your terminal"}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ─── REEF MODE HTML ───────────────────────────────────────

def get_reef_html():
    """Serve Reef Mode UI as a single HTML page (React UMD + Babel)."""
    ui_path = (SCRIPT_DIR.parent / "reef_mode.jsx")
    jsx = ""
    if ui_path.exists():
        try:
            jsx = ui_path.read_text(encoding="utf-8")
        except Exception:
            jsx = ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>REEF MODE — NEXUS</title>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Playfair+Display:wght@600;700;800&display=swap" rel="stylesheet">
  <style>html,body,#root{{height:100%;margin:0;background:#0A0A0A;}}</style>
</head>
<body>
  <div id="root"></div>
  <script>
    window.__REEF_API__ = {{
      snapshot: "/api/reef/snapshot",
      run: "/api/reef/run",
      job: "/api/reef/job",
      outcome: "/api/reef/outcome",
      research: "/api/reef/research",
    }};
  </script>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script type="text/babel" data-presets="react">
{jsx}
  </script>
</body>
</html>'''


# ─── DASHBOARD HTML ───────────────────────────────────────

def get_dashboard_html():
    return r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NEXUS COMMAND CENTER</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#06060c;--s0:#0a0a12;--s1:#10101a;--s2:#181824;--s3:#20202e;
  --bdr:#252538;--bdr2:#30304a;
  --gold:#d4a843;--gold2:#a8832f;--gold3:#7a6020;--gg:rgba(212,168,67,0.08);--gg2:rgba(212,168,67,0.15);
  --hot:#ff3b3b;--warm:#ff9500;--cool:#3d8bff;--cold:#555570;
  --grn:#00d68f;--red:#ff3b5c;--txt:#e4e4f0;--dim:#7a7a9a;--mut:#444460;
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--txt);font-family:'Outfit',sans-serif;overflow-x:hidden}

/* ── GRID LAYOUT ── */
.shell{display:grid;grid-template-columns:260px 1fr 360px;grid-template-rows:auto 1fr;min-height:100vh;gap:0}
@media(max-width:1200px){.shell{grid-template-columns:1fr;grid-template-rows:auto auto auto}}

/* ── TOP BAR ── */
.topbar{grid-column:1/-1;background:var(--s0);border-bottom:1px solid var(--bdr);padding:14px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;backdrop-filter:blur(12px)}
.topbar-left{display:flex;align-items:center;gap:16px}
.logo{font-size:1.15rem;font-weight:900;letter-spacing:0.04em;background:linear-gradient(135deg,var(--gold),#f0d078,var(--gold2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.logo-sub{font-size:0.6rem;color:var(--mut);letter-spacing:0.12em;text-transform:uppercase;margin-top:-2px}
.topbar-stats{display:flex;gap:20px;align-items:center}
.tstat{text-align:center}
.tstat-v{font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:800}
.tstat-l{font-size:0.55rem;color:var(--mut);text-transform:uppercase;letter-spacing:0.08em}
.tstat.hot .tstat-v{color:var(--hot)}.tstat.warm .tstat-v{color:var(--warm)}.tstat.cool .tstat-v{color:var(--cool)}.tstat.cold .tstat-v{color:var(--cold)}.tstat.gold .tstat-v{color:var(--gold)}.tstat.grn .tstat-v{color:var(--grn)}.tstat.red .tstat-v{color:var(--red)}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--grn);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(0,214,143,0.4)}50%{box-shadow:0 0 0 6px rgba(0,214,143,0)}}

/* ── LEFT SIDEBAR ── */
.sidebar{background:var(--s0);border-right:1px solid var(--bdr);padding:20px 16px;overflow-y:auto;max-height:calc(100vh - 54px);position:sticky;top:54px}
@media(max-width:1200px){.sidebar{max-height:none;position:static;border-right:none;border-bottom:1px solid var(--bdr)}}
.sb-section{margin-bottom:24px}
.sb-label{font-size:0.6rem;color:var(--mut);text-transform:uppercase;letter-spacing:0.12em;font-weight:700;margin-bottom:10px;padding:0 4px}
.agent-card{padding:10px 12px;border-radius:8px;margin-bottom:4px;cursor:pointer;transition:all 0.15s;display:flex;align-items:center;gap:10px;border:1px solid transparent}
.agent-card:hover{background:var(--s2);border-color:var(--bdr)}
.agent-card .a-icon{font-size:1.1rem;width:28px;text-align:center}
.agent-card .a-name{font-size:0.78rem;font-weight:600;line-height:1.2}
.agent-card .a-ver{font-size:0.58rem;color:var(--gold2);font-family:'JetBrains Mono',monospace}
.agent-card .a-desc{font-size:0.6rem;color:var(--dim);margin-top:1px}

/* ── MAIN CONTENT ── */
.main{padding:24px;overflow-y:auto;max-height:calc(100vh - 54px)}
@media(max-width:1200px){.main{max-height:none}}

.section{margin-bottom:28px}
.section-hdr{font-size:0.68rem;color:var(--gold2);text-transform:uppercase;letter-spacing:0.12em;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.section-hdr::after{content:'';flex:1;height:1px;background:var(--bdr)}

/* ── PIPELINE BAR ── */
.pipe-bar{display:flex;height:8px;border-radius:4px;overflow:hidden;gap:1px;margin-bottom:20px}
.pipe-seg{transition:all 0.3s}
.pipe-seg.hot{background:var(--hot)}.pipe-seg.warm{background:var(--warm)}.pipe-seg.cool{background:var(--cool)}.pipe-seg.cold{background:var(--cold)}

/* ── COMPANY TABLE ── */
.co-table{width:100%;border-collapse:collapse}
.co-table th{text-align:left;padding:8px 10px;font-size:0.6rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--mut);border-bottom:1px solid var(--bdr);cursor:pointer}
.co-table th:hover{color:var(--gold)}
.co-table td{padding:9px 10px;font-size:0.78rem;border-bottom:1px solid rgba(37,37,56,0.5)}
.co-table tr:hover{background:var(--s1)}
.score-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px}
.score-dot.hot{background:var(--hot);box-shadow:0 0 6px var(--hot)}.score-dot.warm{background:var(--warm);box-shadow:0 0 4px var(--warm)}.score-dot.cool{background:var(--cool)}.score-dot.cold{background:var(--cold)}
.brand-tag{padding:1px 7px;border-radius:3px;font-size:0.6rem;font-weight:700;letter-spacing:0.04em}
.brand-tag.TBF{background:var(--gg2);color:var(--gold);border:1px solid rgba(212,168,67,0.2)}
.brand-tag.DFT{background:rgba(255,59,59,0.06);color:var(--hot);border:1px solid rgba(255,59,59,0.15)}

/* ── ACTIVITY FEED ── */
.activity-item{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid rgba(37,37,56,0.3);align-items:flex-start}
.activity-dot{width:6px;height:6px;border-radius:50%;margin-top:6px;flex-shrink:0}
.activity-dot.success{background:var(--grn)}.activity-dot.error{background:var(--red);box-shadow:0 0 6px var(--red)}.activity-dot.info{background:var(--warm)}
.activity-time{font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:var(--mut);min-width:52px;padding-top:1px}
.activity-text{font-size:0.75rem;line-height:1.4;flex:1}
.activity-file{font-size:0.58rem;color:var(--gold3);font-family:'JetBrains Mono',monospace;margin-top:2px}

/* ── RIGHT PANEL (CHAT) ── */
.chat-panel{background:var(--s0);border-left:1px solid var(--bdr);display:flex;flex-direction:column;max-height:calc(100vh - 54px);position:sticky;top:54px}
@media(max-width:1200px){.chat-panel{max-height:500px;position:static;border-left:none;border-top:1px solid var(--bdr)}}
.chat-hdr{padding:16px 18px;border-bottom:1px solid var(--bdr);display:flex;align-items:center;gap:10px}
.chat-hdr-dot{width:10px;height:10px;border-radius:50%}
.chat-hdr-dot.online{background:var(--grn);box-shadow:0 0 8px rgba(0,214,143,0.4)}
.chat-hdr-dot.offline{background:var(--red)}
.chat-hdr h3{font-size:0.82rem;font-weight:700}
.chat-hdr span{font-size:0.6rem;color:var(--dim)}
.chat-messages{flex:1;overflow-y:auto;padding:14px 16px}
.chat-msg{margin-bottom:12px;display:flex;gap:8px}
.chat-msg.user{flex-direction:row-reverse}
.chat-avatar{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.7rem;flex-shrink:0;border:1px solid var(--bdr)}
.chat-msg.system .chat-avatar{background:var(--s2)}
.chat-msg.user .chat-avatar{background:var(--gg);border-color:rgba(212,168,67,0.2)}
.chat-bubble{max-width:85%;padding:10px 14px;border-radius:10px;font-size:0.76rem;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.chat-msg.system .chat-bubble{background:var(--s1);border:1px solid var(--bdr)}
.chat-msg.user .chat-bubble{background:rgba(212,168,67,0.06);border:1px solid rgba(212,168,67,0.12)}
.chat-input-row{display:flex;gap:8px;padding:12px 16px;border-top:1px solid var(--bdr);background:var(--s0)}
.chat-input{flex:1;background:var(--s1);border:1px solid var(--bdr);border-radius:8px;padding:10px 14px;color:var(--txt);font-family:'Outfit',sans-serif;font-size:0.8rem;outline:none;resize:none}
.chat-input:focus{border-color:var(--gold)}
.chat-input::placeholder{color:var(--mut)}
.chat-send{background:var(--gold);color:#000;border:none;border-radius:8px;padding:10px 16px;font-weight:700;font-family:'Outfit',sans-serif;font-size:0.78rem;cursor:pointer;transition:all 0.15s;white-space:nowrap}
.chat-send:hover{filter:brightness(1.1);transform:translateY(-1px)}
.chat-send:disabled{opacity:0.4;cursor:not-allowed;transform:none}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--bdr2)}
</style>
</head>
<body>

<div class="shell">
  <!-- TOP BAR -->
  <div class="topbar">
    <div class="topbar-left">
      <div><div class="logo">NEXUS</div><div class="logo-sub">Command Center</div></div>
      <div class="pulse"></div>
    </div>
    <div class="topbar-stats" id="topStats"></div>
  </div>

  <!-- LEFT: AGENTS -->
  <div class="sidebar">
    <div class="sb-section">
      <div class="sb-label">Agent Fleet</div>
      <div id="agentList"></div>
    </div>
    <div class="sb-section">
      <div class="sb-label">System Status</div>
      <div id="systemStatus"></div>
    </div>
    <div class="sb-section">
      <div class="sb-label">References</div>
      <div id="refList"></div>
    </div>
  </div>

  <!-- CENTER: PIPELINE + ACTIVITY -->
  <div class="main">
    <div class="section">
      <div class="section-hdr">Pipeline Overview</div>
      <div class="pipe-bar" id="pipeBar"></div>
      <div style="overflow-x:auto">
        <table class="co-table">
          <thead><tr>
            <th>Company</th><th>Contacts</th><th>Avg Score</th><th>Brand</th><th>Top Contact</th><th>Region</th><th>Emails</th>
          </tr></thead>
          <tbody id="companyTable"></tbody>
        </table>
      </div>
    </div>
    <div class="section">
      <div class="section-hdr">Recent Activity</div>
      <div id="activityFeed"></div>
    </div>
  </div>

  <!-- RIGHT: CHAT -->
  <div class="chat-panel">
    <div class="chat-hdr">
      <div class="chat-hdr-dot" id="chatDot"></div>
      <div>
        <h3>Project Manager</h3>
        <span id="chatStatus">Initializing...</span>
      </div>
    </div>
    <div class="chat-messages" id="chatMessages"></div>
    <div class="chat-input-row">
      <input class="chat-input" id="chatInput" placeholder="Ask anything... (/help for commands)" autocomplete="off">
      <button class="chat-send" id="chatSend" onclick="sendChat()">Send</button>
    </div>
  </div>
</div>

<script>
var DATA = null;
var chatHistory = [];

function load() {
  fetch('/api/data')
    .then(function(r){return r.json()})
    .then(function(d){
      DATA = d;
      renderTopStats(d);
      renderAgents(d.agents);
      renderSystem(d.system);
      renderRefs(d.references);
      renderPipeline(d.pipeline);
      renderActivity(d.outputs);
      initChat(d);
    })
    .catch(function(e){
      document.querySelector('.main').innerHTML = '<div style="padding:40px;text-align:center;color:var(--dim)">Loading data... Make sure you have output files in the outputs/ directory.</div>';
    });
}

function renderTopStats(d) {
  var s = d.pipeline.stats || {};
  var el = document.getElementById('topStats');
  var items = [
    {v:s.total||0,l:'Total',c:'gold'},{v:s.hot||0,l:'Hot',c:'hot'},{v:s.warm||0,l:'Warm',c:'warm'},
    {v:s.cool||0,l:'Cool',c:'cool'},{v:s.cold||0,l:'Cold',c:'cold'},
    {v:s.verified||0,l:'Verified',c:'grn'},
    {v:d.agents?d.agents.length:0,l:'Agents',c:'gold'},
  ];
  el.innerHTML = items.map(function(i){return '<div class="tstat '+i.c+'"><div class="tstat-v">'+i.v+'</div><div class="tstat-l">'+i.l+'</div></div>'}).join('');
}

function renderAgents(agents) {
  var icons = {orchestrator:'\uD83C\uDFAF',sales_intel_brief:'\uD83E\uDDE0',social_intel_engine:'\uD83D\uDCE1',apollo_pipeline:'\uD83D\uDE80',enrich_pipeline:'\uD83D\uDD2C',csv_importer:'\uD83D\uDCCB',instagram_agent:'\uD83D\uDCF8',trigger_monitor:'\u26A1',claude_researcher:'\uD83D\uDD0D',ghl_sync:'\uD83D\uDD17',ghl_setup_properties:'\uD83C\uDFD7',generate_dashboard:'\uD83D\uDCCA',command_center:'\uD83D\uDDA5'};
  var el = document.getElementById('agentList');
  el.innerHTML = (agents||[]).map(function(a){
    var icon = icons[a.id] || '\u2699\uFE0F';
    return '<div class="agent-card"><div class="a-icon">'+icon+'</div><div><div class="a-name">'+a.id+' <span class="a-ver">'+a.version+'</span></div><div class="a-desc">'+a.lines+'L | '+a.modified+'</div></div></div>';
  }).join('');
}

function renderSystem(sys) {
  var el = document.getElementById('systemStatus');
  var items = [];
  for (var k in sys) {
    var s = sys[k];
    var ok = s.connected;
    var extra = '';
    if (k==='anthropic') { ok = s.has_credits; extra = s.has_credits?' (credits OK)':' (no credits)'; }
    items.push('<div style="padding:6px 8px;font-size:0.72rem;display:flex;align-items:center;gap:6px"><span style="width:6px;height:6px;border-radius:50%;background:'+(ok?'var(--grn)':'var(--red)')+'"></span>'+k.charAt(0).toUpperCase()+k.slice(1)+extra+'</div>');
  }
  el.innerHTML = items.join('');
}

function renderRefs(refs) {
  var el = document.getElementById('refList');
  el.innerHTML = (refs||[]).map(function(r){
    return '<div style="padding:5px 8px;font-size:0.68rem;color:var(--dim);font-family:JetBrains Mono,monospace">'+r.file+' ('+r.size_kb+'kb)</div>';
  }).join('');
}

function renderPipeline(p) {
  var s = p.stats || {};
  var t = s.total || 1;
  // Bar
  document.getElementById('pipeBar').innerHTML =
    '<div class="pipe-seg hot" style="width:'+(s.hot||0)/t*100+'%"></div>'+
    '<div class="pipe-seg warm" style="width:'+(s.warm||0)/t*100+'%"></div>'+
    '<div class="pipe-seg cool" style="width:'+(s.cool||0)/t*100+'%"></div>'+
    '<div class="pipe-seg cold" style="width:'+(s.cold||0)/t*100+'%"></div>';
  // Table
  var companies = s.companies || [];
  document.getElementById('companyTable').innerHTML = companies.map(function(co){
    var sc = co.avg_score>=80?'hot':co.avg_score>=60?'warm':co.avg_score>=40?'cool':'cold';
    return '<tr>'+
      '<td style="font-weight:600">'+co.name+'</td>'+
      '<td style="font-family:JetBrains Mono,monospace;font-size:0.75rem">'+co.contacts+'</td>'+
      '<td><span class="score-dot '+sc+'"></span><span style="font-family:JetBrains Mono,monospace;font-weight:700;font-size:0.78rem">'+co.avg_score+'</span></td>'+
      '<td><span class="brand-tag '+co.brand+'">'+co.brand+'</span></td>'+
      '<td style="color:var(--dim);font-size:0.72rem">'+co.top_person+'</td>'+
      '<td style="color:var(--mut);font-size:0.72rem">'+(co.state||'').substring(0,2).toUpperCase()+'</td>'+
      '<td style="font-family:JetBrains Mono,monospace;font-size:0.72rem">'+co.emails+'</td>'+
      '</tr>';
  }).join('');
}

function renderActivity(outputs) {
  var el = document.getElementById('activityFeed');
  var typeColors = {scored_pipeline:'success',enriched_data:'success',import:'success',sales_brief:'info',digest:'info',social_scan:'info',data:'info'};
  el.innerHTML = (outputs||[]).map(function(o){
    var dc = typeColors[o.type] || 'info';
    return '<div class="activity-item">'+
      '<div class="activity-dot '+dc+'"></div>'+
      '<div class="activity-time">'+o.modified+'</div>'+
      '<div style="flex:1"><div class="activity-text">'+o.type.replace(/_/g,' ')+' — '+o.file+'</div>'+
      (o.summary?'<div class="activity-file">'+o.summary+'</div>':'')+
      '<div class="activity-file">'+o.size_kb+' KB</div></div></div>';
  }).join('');
}

function initChat(d) {
  var hasCreds = d.system && d.system.anthropic && d.system.anthropic.has_credits;
  var dot = document.getElementById('chatDot');
  var status = document.getElementById('chatStatus');
  dot.className = 'chat-hdr-dot ' + (hasCreds ? 'online' : 'offline');
  status.textContent = hasCreds ? 'AI mode (Claude connected)' : 'Local mode (type /help)';

  addChatMsg('system', 'Nexus PM online. ' + (d.pipeline.stats ? d.pipeline.stats.total + ' contacts in pipeline, ' + d.pipeline.stats.hot + ' hot leads.' : 'No pipeline data loaded.') + '\n\nType /help for commands' + (hasCreds ? ' or ask me anything.' : '.'));

  document.getElementById('chatInput').addEventListener('keydown', function(e){
    if(e.key==='Enter' && !e.shiftKey){e.preventDefault();sendChat()}
  });
}

function addChatMsg(role, text) {
  chatHistory.push({role:role, text:text});
  var container = document.getElementById('chatMessages');
  var div = document.createElement('div');
  div.className = 'chat-msg ' + role;

  // Format text: bold and code
  var formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--gold)">$1</strong>')
                      .replace(/`([^`]+)`/g, '<code style="background:var(--s2);padding:1px 5px;border-radius:3px;font-size:0.68rem;font-family:JetBrains Mono,monospace;color:var(--grn)">$1</code>');

  div.innerHTML = '<div class="chat-avatar">'+(role==='user'?'\uD83D\uDC64':'\uD83E\uDDE0')+'</div><div class="chat-bubble">'+formatted+'</div>';
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function sendChat() {
  var input = document.getElementById('chatInput');
  var msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  addChatMsg('user', msg);

  var btn = document.getElementById('chatSend');
  btn.disabled = true;
  btn.textContent = '...';

  fetch('/api/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message: msg})
  })
  .then(function(r){return r.json()})
  .then(function(d){
    addChatMsg('system', d.response || 'No response.');
    btn.disabled = false;
    btn.textContent = 'Send';
  })
  .catch(function(e){
    addChatMsg('system', 'Error: ' + e.message);
    btn.disabled = false;
    btn.textContent = 'Send';
  });
}

load();
</script>
</body>
</html>'''


# ─── MAIN ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Nexus Command Center")
    parser.add_argument("--port", type=int, default=3141)
    args = parser.parse_args()

    print(f"""
  ╔══════════════════════════════════════════╗
  ║     NEXUS COMMAND CENTER                 ║
  ║     http://localhost:{args.port}               ║
  ╠══════════════════════════════════════════╣
  ║  Agents:    {len(load_agent_registry()):>3}                        ║""")

    leads, source = load_pipeline_data()
    stats = compute_pipeline_stats(leads)
    print(f"  ║  Contacts:  {stats.get('total', 0):>3}  ({stats.get('hot',0)} hot)             ║")
    print(f"  ║  Outputs:   {len(load_recent_outputs()):>3}                        ║")

    status = build_system_status()
    api_status = "✅ Online" if status.get("anthropic", {}).get("has_credits") else "⚠️  No credits"
    print(f"  ║  Claude:    {api_status:>16}       ║")
    print(f"  ╚══════════════════════════════════════════╝\n")
    print(f"  Press Ctrl+C to stop.\n")

    server = HTTPServer(("0.0.0.0", args.port), CommandCenterHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
