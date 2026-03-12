#!/usr/bin/env python3
"""
Instagram Intelligence Agent — Nexus BDR Agent
================================================
Uses Claude + web search to scrape competitor Instagram profiles,
identify their customers/audience, and feed prospects into the pipeline.

Usage:
    python3 instagram_agent.py profile --username "greendotlabs"
    python3 instagram_agent.py competitors --vertical "cannabis extracts" --state "Colorado" --max 10
    python3 instagram_agent.py audience --username "greendotlabs" --brand dft
    python3 instagram_agent.py hashtag --tag "liveresin" --brand dft --max 10

Environment:
    ANTHROPIC_API_KEY — required
"""

import os
import sys
import json
import re
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

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def call_claude(system_prompt, user_prompt, use_web_search=True):
    """Call Claude API with optional web search."""
    if not ANTHROPIC_API_KEY:
        print("  ❌ ANTHROPIC_API_KEY not set.")
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
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=180)
        if resp.status_code == 429:
            print("  ⏳ Rate limited. Waiting 60 seconds...")
            import time
            time.sleep(60)
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=180)

        if resp.status_code != 200:
            print(f"  ❌ Claude API error {resp.status_code}: {resp.text[:300]}")
            return ""

        data = resp.json()
        text_parts = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block["text"])
        return "\n".join(text_parts)

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Request error: {e}")
        return ""


def parse_json_response(response):
    """Extract JSON from Claude's response."""
    if not response:
        return None
    cleaned = response.strip()
    # Try ```json block
    json_match = re.search(r'```json\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(1).strip()
    else:
        # Find first [ or { to last ] or }
        arr_start = cleaned.find('[')
        obj_start = cleaned.find('{')
        if arr_start != -1 and (obj_start == -1 or arr_start < obj_start):
            end = cleaned.rfind(']')
            if end > arr_start:
                cleaned = cleaned[arr_start:end+1]
        elif obj_start != -1:
            end = cleaned.rfind('}')
            if end > obj_start:
                cleaned = cleaned[obj_start:end+1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def save_output(data, prefix):
    """Save output to JSON file."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = OUTPUT_DIR / f"{prefix}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n  💾 Saved to: {path}")
    return path


# ─── PROFILE COMMAND ────────────────────────────────────────

def scrape_profile(username):
    """Scrape an Instagram profile using Claude + web search."""
    system_prompt = """You are an Instagram intelligence analyst. Your job is to find publicly available information about Instagram accounts using web search.

Search for the Instagram profile and any web pages that reference it. Extract as much business intelligence as possible.

Return ONLY valid JSON — no other text."""

    user_prompt = f"""Research the Instagram account @{username} thoroughly.

Search for:
1. "instagram.com/{username}" to find their profile info
2. "{username} instagram" to find mentions and reviews
3. The company behind the account and their website

Extract and return this JSON:
{{
  "username": "{username}",
  "full_name": "",
  "bio": "",
  "follower_count": 0,
  "following_count": 0,
  "post_count": 0,
  "is_business": true,
  "business_category": "",
  "website": "",
  "business_email": "",
  "phone": "",
  "city": "",
  "state": "",
  "company_name": "",
  "company_description": "",
  "key_products": ["list of products/services"],
  "content_themes": ["what they post about"],
  "hashtags_used": ["common hashtags they use"],
  "engagement_level": "HIGH/MEDIUM/LOW based on follower count and apparent activity",
  "notable_info": "anything interesting for sales outreach",
  "last_active": "approximate based on what you find",
  "linked_accounts": ["other social profiles found"],
  "potential_decision_makers": [
    {{"name": "", "title": "", "source": "where you found this"}}
  ]
}}

If you can't find certain fields, use null. Never fabricate data."""

    print(f"  🔍 Researching @{username}...")
    print(f"  ⏳ This may take 30-90 seconds...\n")

    response = call_claude(system_prompt, user_prompt)
    result = parse_json_response(response)

    if not result:
        raw_path = OUTPUT_DIR / f"raw_ig_{username}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
        raw_path.write_text(response)
        print(f"  ⚠️  Could not parse response. Raw saved to: {raw_path}")
        return None

    result["scraped_at"] = datetime.utcnow().isoformat()
    result["source"] = "claude_web_search"

    # Display
    print(f"  📸 @{result.get('username', username)}")
    print(f"  👤 {result.get('full_name', 'N/A')}")
    print(f"  📝 {result.get('bio', 'N/A')[:100]}")
    print(f"  👥 {result.get('follower_count', '?')} followers | {result.get('following_count', '?')} following | {result.get('post_count', '?')} posts")
    print(f"  🌐 {result.get('website', 'N/A')}")
    print(f"  📧 {result.get('business_email', 'N/A')}")
    print(f"  🏢 {result.get('company_name', 'N/A')} — {result.get('business_category', 'N/A')}")
    
    products = result.get("key_products", [])
    if products:
        print(f"  📦 Products: {', '.join(products[:5])}")
    
    themes = result.get("content_themes", [])
    if themes:
        print(f"  🎯 Content: {', '.join(themes[:5])}")

    dms = result.get("potential_decision_makers", [])
    if dms:
        print(f"\n  👤 Decision Makers Found:")
        for dm in dms:
            print(f"     • {dm.get('name', '?')} — {dm.get('title', '?')}")

    return result


# ─── COMPETITORS COMMAND ────────────────────────────────────

def find_competitors(vertical, state, max_results=10):
    """Find competitor Instagram accounts in a vertical."""
    system_prompt = """You are an Instagram intelligence analyst specializing in cannabis and terpene industry accounts. 
Your job is to find real Instagram accounts of businesses in a specific vertical using web search.

CRITICAL: Only return accounts that actually exist. Verify each one via web search.
Return ONLY valid JSON — no other text."""

    user_prompt = f"""Find up to {max_results} real Instagram business accounts for: {vertical} in {state}

Search strategies:
1. "{vertical} {state} instagram" 
2. "instagram.com" + "{vertical}" + "{state}"
3. Known companies in this space + "instagram"
4. Relevant hashtags that would surface these businesses

For each account found, return:
[
  {{
    "username": "their_ig_handle",
    "company_name": "Company Name",
    "follower_count": 0,
    "bio_summary": "What their bio says in 1 sentence",
    "website": "their website if found",
    "business_email": "email if public",
    "city": "",
    "state": "{state}",
    "relevance": "Why they're relevant to terpene sales",
    "engagement_level": "HIGH/MEDIUM/LOW",
    "prospect_quality": "HOT/WARM/COOL based on fit for terpene products"
  }}
]

Only include accounts you've verified exist. Never fabricate Instagram handles."""

    print(f"  🔍 Finding {vertical} competitors on Instagram in {state}...")
    print(f"  ⏳ This may take 60-90 seconds...\n")

    response = call_claude(system_prompt, user_prompt)
    result = parse_json_response(response)

    if not result or not isinstance(result, list):
        raw_path = OUTPUT_DIR / f"raw_ig_competitors_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
        raw_path.write_text(response or "No response")
        print(f"  ⚠️  Could not parse. Raw saved to: {raw_path}")
        return []

    print(f"  📊 Found {len(result)} competitor accounts:\n")
    for i, acct in enumerate(result, 1):
        quality = acct.get("prospect_quality", "?")
        emoji = "🔥" if quality == "HOT" else "🟡" if quality == "WARM" else "🔵"
        print(f"  {i}. {emoji} @{acct.get('username', '?')} — {acct.get('company_name', '?')}")
        print(f"     {acct.get('follower_count', '?')} followers | {acct.get('bio_summary', '')[:80]}")
        print(f"     {acct.get('relevance', '')[:80]}")
        print()

    # Add metadata
    for acct in result:
        acct["discovered_at"] = datetime.utcnow().isoformat()
        acct["source"] = "instagram_competitor_search"
        acct["vertical"] = vertical
        acct["search_state"] = state

    return result


# ─── AUDIENCE COMMAND ───────────────────────────────────────

def analyze_audience(username, brand="dft"):
    """Analyze a competitor's audience to find prospect leads."""
    brand_label = "Terpene Belt Farms" if brand.lower() == "tbf" else "Duty Free Terpenes"
    
    # Load brand context
    brand_path = SKILL_DIR / "references" / "brand-context.md"
    brand_context = brand_path.read_text()[:2000] if brand_path.exists() else ""

    system_prompt = f"""You are an Instagram intelligence analyst for {brand_label}, a botanical terpene supplier.

{brand_context}

Your job is to analyze a competitor's Instagram audience and identify potential B2B prospects — businesses that follow or engage with the competitor that could be terpene buyers.

Use web search to find:
1. Businesses that publicly interact with this account (tagged posts, comments, collaborations)
2. Related accounts in their following/follower overlap
3. Businesses mentioned alongside this account
4. Brands that use similar hashtags

Return ONLY valid JSON — no other text."""

    user_prompt = f"""Analyze the audience and business network around @{username} on Instagram.

Search for:
1. "@{username}" + "tagged" or "collab" or "partner" to find business relationships
2. Businesses that comment on or are mentioned alongside @{username}
3. Related Instagram accounts in the same niche
4. Companies in their supply chain or customer base
5. "@{username}" reviews, mentions on forums, Reddit, etc.

Return prospects found — these are businesses connected to @{username} that could buy terpenes:
{{
  "target_account": "{username}",
  "analysis": {{
    "estimated_audience_size": 0,
    "audience_type": "B2B/B2C/Mixed",
    "primary_audience": "description of who follows them",
    "geographic_focus": "where their audience is",
    "content_engagement": "what posts get most engagement"
  }},
  "business_network": [
    {{
      "company_name": "",
      "instagram": "@handle",
      "relationship": "customer/partner/supplier/competitor",
      "description": "what they do",
      "website": "",
      "city": "",
      "state": "",
      "terpene_fit": "why they'd buy terpenes",
      "prospect_quality": "HOT/WARM/COOL"
    }}
  ],
  "recommended_hashtags": ["hashtags to monitor for more prospects"],
  "outreach_strategy": "How to approach prospects found in this network for {brand_label}"
}}"""

    print(f"  🔍 Analyzing @{username}'s audience and business network...")
    print(f"  🎯 Looking for {brand_label} prospects in their orbit...")
    print(f"  ⏳ This may take 60-120 seconds...\n")

    response = call_claude(system_prompt, user_prompt)
    result = parse_json_response(response)

    if not result:
        raw_path = OUTPUT_DIR / f"raw_ig_audience_{username}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
        raw_path.write_text(response or "No response")
        print(f"  ⚠️  Could not parse. Raw saved to: {raw_path}")
        return None

    # Display
    analysis = result.get("analysis", {})
    print(f"  📊 Audience Analysis for @{username}:")
    print(f"     Size: ~{analysis.get('estimated_audience_size', '?')}")
    print(f"     Type: {analysis.get('audience_type', '?')}")
    print(f"     Focus: {analysis.get('primary_audience', '?')}")
    print(f"     Geo: {analysis.get('geographic_focus', '?')}")

    network = result.get("business_network", [])
    if network:
        print(f"\n  🏢 Business Network ({len(network)} prospects found):\n")
        for biz in network:
            quality = biz.get("prospect_quality", "?")
            emoji = "🔥" if quality == "HOT" else "🟡" if quality == "WARM" else "🔵"
            print(f"     {emoji} {biz.get('company_name', '?')} (@{biz.get('instagram', '?')})")
            print(f"        {biz.get('relationship', '?')} — {biz.get('description', '')[:70]}")
            print(f"        Terpene fit: {biz.get('terpene_fit', 'N/A')[:70]}")
            print()

    hashtags = result.get("recommended_hashtags", [])
    if hashtags:
        print(f"  #️⃣  Monitor these hashtags: {', '.join(hashtags[:10])}")

    strategy = result.get("outreach_strategy", "")
    if strategy:
        print(f"\n  💡 Outreach Strategy: {strategy[:200]}")

    result["scraped_at"] = datetime.utcnow().isoformat()
    result["brand"] = brand_label
    return result


# ─── HASHTAG COMMAND ────────────────────────────────────────

def search_hashtag(tag, brand="dft", max_results=10):
    """Find businesses posting with specific hashtags."""
    brand_label = "Terpene Belt Farms" if brand.lower() == "tbf" else "Duty Free Terpenes"

    system_prompt = f"""You are an Instagram hashtag analyst for {brand_label}.
Find real businesses that use specific hashtags on Instagram.
Return ONLY valid JSON — no other text."""

    user_prompt = f"""Search for businesses that use #{tag} on Instagram.

Search strategies:
1. "instagram #{tag}" to find posts and accounts
2. "#{tag}" + "cannabis" or "extraction" or "concentrates"
3. Related hashtags and the businesses using them

Find up to {max_results} real business accounts using #{tag} or related tags.

Return:
[
  {{
    "username": "@handle",
    "company_name": "",
    "bio_summary": "",
    "follower_count": 0,
    "website": "",
    "hashtags_used": ["#{tag}", "other relevant tags"],
    "content_type": "what they post",
    "prospect_quality": "HOT/WARM/COOL for terpene sales",
    "terpene_fit": "why they'd buy terpenes"
  }}
]

Only real, verified accounts. Never fabricate."""

    print(f"  #️⃣  Searching Instagram for #{tag} businesses...")
    print(f"  ⏳ This may take 30-60 seconds...\n")

    response = call_claude(system_prompt, user_prompt)
    result = parse_json_response(response)

    if not result or not isinstance(result, list):
        raw_path = OUTPUT_DIR / f"raw_ig_hashtag_{tag}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.txt"
        raw_path.write_text(response or "No response")
        print(f"  ⚠️  Could not parse. Raw saved to: {raw_path}")
        return []

    print(f"  📊 Found {len(result)} accounts using #{tag}:\n")
    for i, acct in enumerate(result, 1):
        quality = acct.get("prospect_quality", "?")
        emoji = "🔥" if quality == "HOT" else "🟡" if quality == "WARM" else "🔵"
        print(f"  {i}. {emoji} @{acct.get('username', '?')} — {acct.get('company_name', '?')}")
        print(f"     {acct.get('terpene_fit', '')[:80]}")
        print()

    for acct in result:
        acct["discovered_at"] = datetime.utcnow().isoformat()
        acct["source"] = f"instagram_hashtag_{tag}"
        acct["brand"] = brand_label

    return result


# ─── CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Instagram Intelligence Agent — Nexus BDR")
    subparsers = parser.add_subparsers(dest="command")

    # profile
    p = subparsers.add_parser("profile", help="Scrape a single IG profile")
    p.add_argument("--username", required=True)

    # competitors
    c = subparsers.add_parser("competitors", help="Find competitor IG accounts")
    c.add_argument("--vertical", required=True)
    c.add_argument("--state", default="Colorado")
    c.add_argument("--max", type=int, default=10)

    # audience
    a = subparsers.add_parser("audience", help="Analyze competitor's audience for prospects")
    a.add_argument("--username", required=True)
    a.add_argument("--brand", default="dft", choices=["tbf", "dft"])

    # hashtag
    h = subparsers.add_parser("hashtag", help="Find businesses using a hashtag")
    h.add_argument("--tag", required=True)
    h.add_argument("--brand", default="dft", choices=["tbf", "dft"])
    h.add_argument("--max", type=int, default=10)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    print(f"\n  {'='*55}")
    print(f"  📸 NEXUS BDR — Instagram Intelligence Agent")
    print(f"  Command: {args.command}")
    print(f"  {'='*55}\n")

    if args.command == "profile":
        result = scrape_profile(args.username)
        if result:
            save_output(result, f"ig_profile_{args.username}")

    elif args.command == "competitors":
        result = find_competitors(args.vertical, args.state, args.max)
        if result:
            save_output({
                "metadata": {
                    "vertical": args.vertical,
                    "state": args.state,
                    "total": len(result),
                },
                "accounts": result,
            }, f"ig_competitors_{args.state.lower().replace(' ', '_')}")

    elif args.command == "audience":
        result = analyze_audience(args.username, args.brand)
        if result:
            save_output(result, f"ig_audience_{args.username}")

    elif args.command == "hashtag":
        result = search_hashtag(args.tag, args.brand, args.max)
        if result:
            save_output({
                "metadata": {"hashtag": args.tag, "total": len(result)},
                "accounts": result,
            }, f"ig_hashtag_{args.tag}")

    print(f"\n  {'='*55}\n")


if __name__ == "__main__":
    main()
