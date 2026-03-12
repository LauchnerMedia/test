#!/usr/bin/env python3
"""
Nexus BDR Orchestrator — PM Agent
==================================
The single entry point for the entire BDR system. Talk to this agent
in natural language and it delegates tasks to specialist agents.

Usage:
    python3 orchestrator.py                          # Interactive mode
    python3 orchestrator.py "find 5 extractors in CO for DFT"  # Single command
    python3 orchestrator.py --briefing               # Daily pipeline briefing

Architecture:
    YOU → PM Agent (this) → delegates to:
        ├── Research Agent    (claude_researcher.py discover/research)
        ├── Outreach Agent    (claude_researcher.py outreach)
        ├── CRM Agent         (hubspot_sync.py)
        ├── Enrichment Agent  (hunter_enrich.py)
        └── [Future] Social Agent (instagram, linkedin)

Environment:
    ANTHROPIC_API_KEY, HUNTER_API_KEY, HUBSPOT_API_KEY
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests")
    sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"

SKILL_DIR = Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = SKILL_DIR / "scripts"
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Conversation history for multi-turn
conversation_history = []


def call_claude(system_prompt: str, messages: list, use_tools: bool = False) -> str:
    """Call Claude API with conversation history."""
    if not ANTHROPIC_API_KEY:
        print("\n  ❌ ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": messages,
    }

    if use_tools:
        payload["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 429:
            print("\n  ⏳ Rate limited. Waiting 60 seconds...")
            import time
            time.sleep(60)
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
        
        if resp.status_code != 200:
            print(f"\n  ❌ Claude API error {resp.status_code}: {resp.text[:200]}")
            return ""

        data = resp.json()
        text_parts = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block["text"])
        return "\n".join(text_parts)

    except requests.exceptions.RequestException as e:
        print(f"\n  ❌ Request error: {e}")
        return ""


def run_script(script_name: str, args: list) -> str:
    """Run a sub-agent script and capture output."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return f"ERROR: Script not found: {script_path}"

    cmd = ["python3", str(script_path)] + args
    print(f"\n  🔧 Running: {script_name} {' '.join(args)}")
    print(f"  {'─'*50}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ},
            cwd=str(SKILL_DIR),
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\n⚠️  Exit code: {result.returncode}"
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr[-500:]}"
        elif result.stderr and "Warning" not in result.stderr and "Traceback" in result.stderr:
            output += f"\nSTDERR: {result.stderr[-500:]}"

        # Print the sub-agent output
        for line in output.strip().split("\n"):
            print(f"  {line}")
        print(f"  {'─'*50}")

        return output

    except subprocess.TimeoutExpired:
        return "ERROR: Script timed out after 300 seconds. Try running directly."
    except Exception as e:
        return f"ERROR running {script_name}: {e}"


def get_latest_file(prefix: str, ext: str = ".json"):
    """Get the most recently created file matching a prefix."""
    files = sorted(OUTPUT_DIR.glob(f"{prefix}*{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def parse_and_execute(user_input: str) -> str:
    """Use Claude to interpret the user's request and decide which agents to invoke."""

    # Check for available outputs to give context
    existing_files = list(OUTPUT_DIR.glob("*.json"))
    file_summaries = []
    for f in sorted(existing_files, key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        file_summaries.append(f"  - {f.name} ({f.stat().st_size} bytes, {datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')})")
    files_context = "\n".join(file_summaries) if file_summaries else "  (none yet)"

    system_prompt = f"""You are the PM Orchestrator for the Nexus BDR Agent system. You manage a team of AI agents that handle B2B sales prospecting for Nexus Agriscience (two brands: Terpene Belt Farms and Duty Free Terpenes).

YOUR AVAILABLE AGENTS AND THEIR EXACT COMMANDS:

1. RESEARCH AGENT (claude_researcher.py)
   - Discover prospects: discover --brand [tbf|dft] --vertical "[description]" --state "[state]" --max-leads [N]
   - Deep research: research --company "[name]" --domain "[domain.com]"
   - Generate outreach: outreach --input [filepath] --brand [tbf|dft]

2. CRM AGENT — GoHighLevel (ghl_sync.py)
   - Create contact: create-contact --first-name "[name]" --last-name "[name]" --email "[email]" --company "[company]" --phone "[phone]" --tags "[tags]"
   - Search contacts: search-contacts --query "[search term]"
   - Tag contact: tag-contact --contact-id "[id]" --tags "Tag1,Tag2"
   - Get pipelines: get-pipelines
   - Create opportunity: create-opportunity --contact-id "[id]" --pipeline-id "[pid]" --stage-id "[sid]" --name "[deal name]" --value [amount]
   - Update opportunity: update-opportunity --opportunity-id "[id]" --stage-id "[sid]" --status "[open|won|lost]"
   - Pipeline report: pipeline-report --pipeline-id "[pid]"
   - Send email: send-email --contact-id "[id]" --subject "[subject]" --body "[html body]"
   - Send SMS: send-sms --contact-id "[id]" --message "[message]"
   - Get calendars: get-calendars
   - Get workflows: get-workflows
   - Bulk import: bulk-import --input [filepath] --pipeline-id "[pid]" --stage-id "[sid]" --tags "tag1,tag2"

3. HUBSPOT CRM AGENT (hubspot_sync.py) — Legacy, available but prefer GHL
   - Same commands as before (create-contact, pipeline-report, etc)

4. ENRICHMENT AGENT (hunter_enrich.py)
   - Enrich leads: --input [filepath] --min-confidence [70]

4. ENRICHMENT AGENT (hunter_enrich.py)
   - Enrich leads: --input [filepath] --min-confidence [70]

5. INSTAGRAM INTELLIGENCE AGENT (instagram_agent.py)
   - Profile scrape: profile --username "[handle]"
   - Find competitors: competitors --vertical "[description]" --state "[state]" --max [N]
   - Audience analysis: audience --username "[handle]" --brand [tbf|dft]
   - Hashtag search: hashtag --tag "[hashtag_no_hash]" --brand [tbf|dft] --max [N]

6. TRIGGER EVENT MONITOR (trigger_monitor.py)
   - Scan single company: --scan-company "[company name]"
   - Scan entire watchlist: --scan-all --max [N]
   - Scan from file: --scan-list "[path_to_json]"
   - Scan industry: --scan-industry --vertical "[vertical]" --state "[ST]"
   - Scan competitors: --scan-competitors
   - Build watchlist: --build-watchlist
   - Add to watchlist: --add-company "[name]" --domain "[domain]"

7. CSV/LIST IMPORTER (csv_importer.py)
   - Preview: --input "[file.csv]" --preview
   - Import: --input "[file.csv]" --source-label "[source name]"
   - Import + enrich: --input "[file.csv]" --enrich --import-ghl

8. ENRICHMENT PIPELINE (enrich_pipeline.py)
   - Enrich + score: --input "[file.json]" --brand auto
   - Enrich + import: --input "[file.json]" --brand auto --import-ghl --pipeline-id "[id]" --stage-id "[id]"
   - Skip enrichment: --input "[file.json]" --skip-enrich --import-ghl

IMPORTANT NOTES:
- When user says "CRM", "pipeline", "contacts", "deals" — default to GHL agent (ghl_sync.py), NOT HubSpot
- For GHL commands, the user needs GHL_API_TOKEN and GHL_LOCATION_ID env vars set
- When importing prospects to GHL, first run get-pipelines to find the right pipeline/stage IDs
- Use upsert logic to avoid duplicates
- When user says "scan", "monitor", "signals", "alerts", "briefing" — use trigger_monitor.py
- When user says "import", "csv", "list", "spreadsheet" — use csv_importer.py
- When user says "enrich" — use enrich_pipeline.py

EXISTING OUTPUT FILES:
{files_context}

YOUR JOB:
- Interpret what the user wants in natural language
- Decide which agent(s) to invoke and in what order
- Return a JSON action plan

RESPOND WITH ONLY THIS JSON (no other text):
{{
  "understanding": "What the user wants in one sentence",
  "plan": [
    {{
      "step": 1,
      "agent": "research|crm|enrichment|outreach|none",
      "script": "script_name.py",
      "args": ["list", "of", "arguments"],
      "description": "What this step does"
    }}
  ],
  "message": "Brief friendly message to the user about what you're about to do",
  "needs_clarification": false,
  "clarification_question": ""
}}

If you need more info from the user, set needs_clarification to true and ask in clarification_question.
If the request is just a question or chat (not a task), set agent to "none" and answer in "message".
"""

    messages = [{"role": "user", "content": user_input}]
    response = call_claude(system_prompt, messages, use_tools=False)

    if not response:
        return "Couldn't reach the planning agent. Try again."

    # Parse the plan
    try:
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            plan = json.loads(json_match.group(0))
        else:
            return f"Planning error. Raw response: {response[:300]}"
    except json.JSONDecodeError:
        return f"Couldn't parse plan. Raw: {response[:300]}"

    # If clarification needed, just ask
    if plan.get("needs_clarification"):
        return f"\n  💬 {plan.get('clarification_question', 'Could you be more specific?')}"

    # If no action needed (just a question)
    steps = plan.get("plan", [])
    if not steps or (len(steps) == 1 and steps[0].get("agent") == "none"):
        return f"\n  💬 {plan.get('message', response[:300])}"

    # Execute the plan
    print(f"\n  🎯 {plan.get('understanding', '')}")
    print(f"  💬 {plan.get('message', '')}")
    print(f"\n  📋 Execution Plan ({len(steps)} steps):")
    for step in steps:
        print(f"     {step['step']}. [{step['agent'].upper()}] {step['description']}")

    results = []
    for step in steps:
        script = step.get("script", "")
        args = step.get("args", [])

        if step.get("agent") == "none":
            continue

        if not script:
            results.append(f"Step {step['step']}: No script specified, skipping.")
            continue

        output = run_script(script, args)
        results.append(output)

        # If a step fails, don't continue blindly
        if "ERROR" in output and "Warning" not in output:
            print(f"\n  ⚠️  Step {step['step']} had an error. Stopping execution.")
            break

    return "\n".join(results)


def daily_briefing() -> str:
    """Generate a daily pipeline briefing."""
    print("\n  📊 Generating daily briefing...\n")

    # Pull pipeline report
    crm_output = run_script("hubspot_sync.py", ["pipeline-report"])

    # Check for pending follow-ups
    followups_path = OUTPUT_DIR / "follow-ups.json"
    followup_count = 0
    overdue = 0
    if followups_path.exists():
        try:
            followups = json.load(open(followups_path))
            followup_count = len(followups)
            today = datetime.utcnow().date()
            for fu in followups:
                due = datetime.fromisoformat(fu.get("due_date", "2099-01-01")).date()
                if due <= today:
                    overdue += 1
        except (json.JSONDecodeError, KeyError):
            pass

    # Check recent activity
    activity_path = OUTPUT_DIR / "activity-log.json"
    recent_activities = 0
    if activity_path.exists():
        try:
            activities = json.load(open(activity_path))
            week_ago = datetime.utcnow().timestamp() - (7 * 86400)
            recent_activities = sum(
                1 for a in activities
                if datetime.fromisoformat(a.get("timestamp", "2000-01-01")).timestamp() > week_ago
            )
        except (json.JSONDecodeError, KeyError):
            pass

    # Count prospect files
    prospect_files = list(OUTPUT_DIR.glob("prospects_*.json"))
    total_prospects = 0
    for pf in prospect_files:
        try:
            data = json.load(open(pf))
            total_prospects += len(data.get("prospects", []))
        except:
            pass

    briefing = f"""
  {'='*50}
  📊  DAILY BDR BRIEFING — {datetime.utcnow().strftime('%B %d, %Y')}
  {'='*50}

  📂 Pipeline:
{crm_output if crm_output else '     (No CRM data — check HUBSPOT_API_KEY)'}

  📬 Follow-ups:
     Total scheduled: {followup_count}
     Overdue: {overdue}

  🔍 Prospecting:
     Total prospects discovered: {total_prospects}
     Prospect files: {len(prospect_files)}

  📝 Activity (last 7 days):
     Actions logged: {recent_activities}

  {'='*50}
  💡 Suggested actions:
     {"• Address " + str(overdue) + " overdue follow-ups" if overdue > 0 else "• No overdue follow-ups ✅"}
     • Run prospect discovery for new verticals/states
     • Deep research your top prospects before outreach
  {'='*50}
"""
    return briefing


def interactive_mode():
    """Run the orchestrator in interactive CLI mode."""
    print(f"""
  {'='*60}
  🤖  NEXUS BDR ORCHESTRATOR — PM Agent
  {'='*60}

  Talk to me in natural language. I'll delegate to the right agents.

  Examples:
    "find 10 extract artists in Oklahoma for DFT"
    "deep research Green Dot Labs"
    "generate outreach for the Colorado prospects"
    "show me the pipeline"
    "daily briefing"
    "import last prospects to HubSpot"

  Type 'quit' or 'exit' to leave.
  Type 'briefing' for daily pipeline summary.
  {'='*60}
""")

    while True:
        try:
            user_input = input("\n  You → ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  👋 Later.\n")
            break

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("\n  👋 Later.\n")
            break

        if user_input.lower() in ["briefing", "daily briefing", "daily", "status"]:
            print(daily_briefing())
            continue

        # Send to the planning agent
        result = parse_and_execute(user_input)
        print(result)


def main():
    parser = argparse.ArgumentParser(description="Nexus BDR Orchestrator — PM Agent")
    parser.add_argument("command", nargs="?", default=None, help="Natural language command (or omit for interactive mode)")
    parser.add_argument("--briefing", action="store_true", help="Show daily pipeline briefing")

    args = parser.parse_args()

    if args.briefing:
        print(daily_briefing())
    elif args.command:
        # Single command mode
        print(f"\n{'='*60}")
        print(f"  🤖  NEXUS BDR ORCHESTRATOR")
        print(f"{'='*60}")
        result = parse_and_execute(args.command)
        print(result)
        print(f"\n{'='*60}\n")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
