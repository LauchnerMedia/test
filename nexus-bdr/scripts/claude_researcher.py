#!/usr/bin/env python3
"""
Claude-Powered Prospect Research Agent — Nexus BDR Agent
Uses Claude API with web search to discover, research, and qualify prospects.
Replaces Apollo for lead discovery — no paid API needed.

Usage:
    python3 claude_researcher.py --brand tbf --vertical "cannabis manufacturers" --state "California" --max-leads 10
    python3 claude_researcher.py --brand dft --vertical "extract artists" --state "Colorado" --max-leads 5
    python3 claude_researcher.py --company "Cookies" --domain "cookiescalifornia.com"

Environment:
    ANTHROPIC_API_KEY — Your Anthropic API key (required)
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install: pip install requests")
    sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"  # Sonnet for cost efficiency, swap to opus for complex tasks

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_brand_context() -> str:
    """Load brand context from references."""
    brand_path = SKILL_DIR / "references" / "brand-context.md"
    if brand_path.exists():
        return brand_path.read_text()
    return ""


def call_claude(system_prompt: str, user_prompt: str, use_web_search: bool = True) -> str:
    """Call Claude API with optional web search tool."""
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
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
        "messages": [{"role": "user", "content": user_prompt}],
    }

    if use_web_search:
        payload["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"  [Claude] Status: {resp.status_code}")
            print(f"  [Claude] Response: {resp.text[:500]}")
            return ""
        
        data = resp.json()
        
        # Extract text from response content blocks
        text_parts = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block["text"])
        
        return "\n".join(text_parts)

    except requests.exceptions.RequestException as e:
        print(f"  [Claude] Error: {e}")
        return ""


def discover_prospects(brand: str, vertical: str, state: str, max_leads: int) -> list:
    """Use Claude + web search to discover prospects in a vertical."""
    
    brand_context = load_brand_context()
    brand_label = "Terpene Belt Farms" if brand.lower() == "tbf" else "Duty Free Terpenes"
    
    system_prompt = f"""You are a B2B sales research analyst for Nexus Agriscience, which operates two terpene brands.

{brand_context[:3000]}

Your job is to find real companies that would be good prospects for {brand_label}'s botanical terpene products.

CRITICAL RULES:
- Only return REAL companies that actually exist. Never fabricate company names or details.
- Use web search to find actual companies in the specified vertical and location.
- For each company, find a real decision-maker name and title if possible.
- Return results as valid JSON only — no markdown, no explanation, no preamble.
"""

    user_prompt = f"""Search the web and find up to {max_leads} real companies that match this criteria:

Brand: {brand_label}
Vertical: {vertical}
State/Location: {state}

Search for "{vertical} companies in {state}" and related queries to find real businesses.

For each company found, gather:
- Company name
- Website domain
- What they do (1 sentence)
- Estimated employee count (if findable)
- A key decision-maker name and title (if findable)
- City and state
- Why they'd be a good prospect for {brand_label} terpenes (1 sentence)
- A personalization hook for outreach (something specific about them)

Return ONLY a JSON array. No other text. Format:
[
  {{
    "company_name": "Example Co",
    "domain": "example.com",
    "description": "They make cannabis concentrates",
    "estimated_employees": 25,
    "contact_name": "Jane Smith",
    "contact_title": "CEO",
    "city": "Denver",
    "state": "Colorado",
    "prospect_fit": "Active concentrate manufacturer needing consistent terpene supply",
    "personalization_hook": "Recently launched a new live resin product line"
  }}
]
"""

    print(f"  [Claude] Searching for {vertical} prospects in {state}...")
    print(f"  [Claude] This may take 30-60 seconds (web search + analysis)...\n")
    
    response = call_claude(system_prompt, user_prompt, use_web_search=True)
    
    if not response:
        print("  [Claude] No response received.")
        return []
    
    # Try to parse JSON from response
    try:
        # Clean up response — Claude often wraps JSON in text and code blocks
        cleaned = response.strip()
        
        # Try to find JSON array in the response
        # Method 1: Look for ```json ... ``` block
        import re
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1).strip()
        else:
            # Method 2: Look for first [ ... last ]
            start = cleaned.find('[')
            end = cleaned.rfind(']')
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end+1]
            else:
                # Method 3: Try the whole thing
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
        
        prospects = json.loads(cleaned)
        
        if not isinstance(prospects, list):
            print(f"  [Claude] Unexpected response format. Raw response saved.")
            prospects = []
            
    except json.JSONDecodeError:
        print(f"  [Claude] Could not parse JSON response. Saving raw response for review.")
        raw_path = OUTPUT_DIR / f"raw_response_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
        raw_path.write_text(response)
        print(f"  [Claude] Raw response saved to: {raw_path}")
        prospects = []
    
    # Enrich with metadata
    for p in prospects:
        p["source"] = "claude_research"
        p["brand"] = brand_label
        p["vertical"] = vertical
        p["discovered_at"] = datetime.utcnow().isoformat()
        p["status"] = "new"
        p["lead_score"] = 0  # Will be scored next
    
    return prospects


def research_company(company_name: str, domain: str) -> dict:
    """Deep research a specific company using Claude + web search."""
    
    brand_context = load_brand_context()
    
    system_prompt = f"""You are a B2B sales research analyst for Nexus Agriscience.

{brand_context[:2000]}

Your job is to deeply research a prospect company and provide intelligence that helps sales reps write highly personalized outreach.

Return results as valid JSON only — no markdown, no explanation, no preamble.
"""

    user_prompt = f"""Research the company "{company_name}" (website: {domain}) thoroughly.

Search for:
1. What they do and their main products/services
2. Company size and locations
3. Recent news (funding, product launches, acquisitions, expansions)
4. Key leadership team members and their roles
5. Job postings (especially R&D, manufacturing, formulation, extraction roles)
6. Social media presence and recent content
7. Any mention of terpenes, botanical ingredients, or flavor/aroma sourcing
8. Competitors they operate alongside
9. Challenges their market segment faces right now

Return ONLY this JSON structure:
{{
  "company_name": "{company_name}",
  "domain": "{domain}",
  "description": "What they do in 2-3 sentences",
  "products": ["list", "of", "main", "products"],
  "estimated_employees": 0,
  "locations": ["City, State"],
  "leadership": [
    {{"name": "Name", "title": "Title", "linkedin": "url if found"}}
  ],
  "recent_news": [
    {{"headline": "Brief description", "date": "approximate date", "relevance": "why this matters for selling terpenes"}}
  ],
  "hiring_signals": ["relevant job titles they're hiring for"],
  "terpene_relevance": "How/why they would use botanical terpenes",
  "personalization_hooks": [
    "Specific thing to reference in outreach",
    "Another specific hook"
  ],
  "recommended_brand": "TBF or DFT based on their profile",
  "recommended_template": "which outreach template to use",
  "fit_score": "HIGH/MEDIUM/LOW with brief explanation",
  "outreach_angle": "The specific angle to lead with in outreach"
}}
"""

    print(f"  [Claude] Deep researching {company_name} ({domain})...")
    print(f"  [Claude] This may take 30-90 seconds...\n")
    
    response = call_claude(system_prompt, user_prompt, use_web_search=True)
    
    if not response:
        return {"error": "No response from Claude", "company_name": company_name}
    
    try:
        cleaned = response.strip()
        import re
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1).strip()
        else:
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end+1]
        
        research = json.loads(cleaned)
        research["researched_at"] = datetime.utcnow().isoformat()
        research["source"] = "claude_deep_research"
        return research
        
    except json.JSONDecodeError:
        raw_path = OUTPUT_DIR / f"raw_research_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
        raw_path.write_text(response)
        print(f"  [Claude] Could not parse JSON. Raw saved to: {raw_path}")
        return {"error": "JSON parse failed", "company_name": company_name, "raw_file": str(raw_path)}


def generate_outreach(prospect: dict, brand: str) -> dict:
    """Generate personalized outreach sequence for a prospect."""
    
    # Load outreach templates for context
    templates_path = SKILL_DIR / "references" / "outreach-templates.md"
    templates = templates_path.read_text() if templates_path.exists() else ""
    
    brand_label = "Terpene Belt Farms" if brand.lower() == "tbf" else "Duty Free Terpenes"
    
    system_prompt = f"""You are writing sales outreach for {brand_label}, a botanical terpene supplier.

Use these outreach templates as style guides:
{templates[:3000]}

Write authentic, personalized outreach. Never be generic. Reference specific things about the prospect.
Return valid JSON only.
"""

    prospect_info = json.dumps(prospect, indent=2)
    
    user_prompt = f"""Generate a 3-email outreach sequence for this prospect:

{prospect_info}

Return ONLY this JSON:
{{
  "prospect": "{prospect.get('company_name', 'Unknown')}",
  "contact": "{prospect.get('contact_name', 'Decision Maker')}",
  "brand": "{brand_label}",
  "sequence": [
    {{
      "day": 0,
      "type": "email",
      "subject": "Subject line under 8 words",
      "body": "Email body under 150 words. Personalized."
    }},
    {{
      "day": 7,
      "type": "email", 
      "subject": "Re: original subject",
      "body": "Follow-up with value-add. Under 100 words."
    }},
    {{
      "day": 14,
      "type": "email",
      "subject": "Closing the loop",
      "body": "Soft break-up email. Under 80 words."
    }}
  ]
}}
"""

    print(f"  [Claude] Generating outreach for {prospect.get('company_name', 'Unknown')}...")
    
    response = call_claude(system_prompt, user_prompt, use_web_search=False)
    
    if not response:
        return {"error": "No response"}
    
    try:
        cleaned = response.strip()
        import re
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1).strip()
        else:
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end+1]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "JSON parse failed", "raw": response[:500]}


def main():
    parser = argparse.ArgumentParser(description="Claude-Powered Prospect Research — Nexus BDR Agent")
    subparsers = parser.add_subparsers(dest="command")

    # discover
    disc = subparsers.add_parser("discover", help="Find new prospects in a vertical")
    disc.add_argument("--brand", required=True, choices=["tbf", "dft"], help="TBF or DFT")
    disc.add_argument("--vertical", required=True, help="Target vertical (e.g. 'cannabis extraction companies')")
    disc.add_argument("--state", default="California", help="State to search in")
    disc.add_argument("--max-leads", type=int, default=10, help="Max leads to find")

    # research
    res = subparsers.add_parser("research", help="Deep research a specific company")
    res.add_argument("--company", required=True, help="Company name")
    res.add_argument("--domain", required=True, help="Company website domain")

    # outreach
    out = subparsers.add_parser("outreach", help="Generate outreach for a prospect")
    out.add_argument("--input", required=True, help="Prospect JSON file or inline JSON")
    out.add_argument("--brand", required=True, choices=["tbf", "dft"])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"  NEXUS BDR AGENT — Claude Research Engine")
    print(f"  Model: {MODEL}")
    print(f"  Command: {args.command}")
    print(f"{'='*60}\n")

    if args.command == "discover":
        prospects = discover_prospects(args.brand, args.vertical, args.state, args.max_leads)
        
        if prospects:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
            output_path = OUTPUT_DIR / f"prospects_{args.brand}_{timestamp}.json"
            
            with open(output_path, "w") as f:
                json.dump({
                    "metadata": {
                        "brand": args.brand,
                        "vertical": args.vertical,
                        "state": args.state,
                        "total": len(prospects),
                        "generated_at": datetime.utcnow().isoformat(),
                    },
                    "prospects": prospects,
                }, f, indent=2)
            
            print(f"\n  📊 Found {len(prospects)} prospects:\n")
            for i, p in enumerate(prospects, 1):
                print(f"  {i}. {p.get('company_name', '?')} — {p.get('description', '')[:60]}")
                if p.get('contact_name'):
                    print(f"     Contact: {p['contact_name']} ({p.get('contact_title', '?')})")
                print(f"     Fit: {p.get('prospect_fit', 'N/A')}")
                print()
            
            print(f"  💾 Saved to: {output_path}")
        else:
            print("  No prospects found.")

    elif args.command == "research":
        research = research_company(args.company, args.domain)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        company_slug = args.company.lower().replace(" ", "_")[:30]
        output_path = OUTPUT_DIR / f"research_{company_slug}_{timestamp}.json"
        
        with open(output_path, "w") as f:
            json.dump(research, f, indent=2)
        
        if "error" not in research:
            print(f"\n  📊 Research Summary for {args.company}:")
            print(f"  Description: {research.get('description', 'N/A')}")
            print(f"  Fit: {research.get('fit_score', 'N/A')}")
            print(f"  Recommended Brand: {research.get('recommended_brand', 'N/A')}")
            print(f"  Outreach Angle: {research.get('outreach_angle', 'N/A')}")
            
            hooks = research.get("personalization_hooks", [])
            if hooks:
                print(f"\n  🎯 Personalization Hooks:")
                for hook in hooks:
                    print(f"     • {hook}")
            
            leaders = research.get("leadership", [])
            if leaders:
                print(f"\n  👤 Key Contacts:")
                for l in leaders[:5]:
                    print(f"     • {l.get('name', '?')} — {l.get('title', '?')}")
        
        print(f"\n  💾 Full research saved to: {output_path}")

    elif args.command == "outreach":
        # Load prospect data
        input_path = Path(args.input)
        if input_path.exists():
            with open(input_path) as f:
                data = json.load(f)
            # Handle both single prospect and list formats
            if "prospects" in data:
                prospects = data["prospects"]
            elif isinstance(data, list):
                prospects = data
            else:
                prospects = [data]
        else:
            print(f"  ERROR: File not found: {args.input}")
            sys.exit(1)
        
        all_sequences = []
        for prospect in prospects:
            sequence = generate_outreach(prospect, args.brand)
            all_sequences.append(sequence)
            
            if "error" not in sequence:
                print(f"\n  ✅ {prospect.get('company_name', '?')}:")
                for email in sequence.get("sequence", []):
                    print(f"     Day {email['day']}: {email['subject']}")
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        output_path = OUTPUT_DIR / f"sequences_{args.brand}_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(all_sequences, f, indent=2)
        
        print(f"\n  💾 Sequences saved to: {output_path}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
