#!/usr/bin/env python3
"""
Social Intelligence Engine v2 — Nexus BDR Agent
=================================================
Multi-phase social intelligence pipeline. Not keyword matching —
intent understanding, thread-level analysis, cross-source correlation,
and community engagement strategy.

ARCHITECTURE:
  Phase 1: REDDIT DEEP SCAN (3 sub-phases)
    1a. Direct API harvest — pull raw posts from 10+ subreddits
    1b. Intent classification — Claude classifies each post by buyer intent
    1c. Thread deep-dive — fetch and analyze top threads' full comments

  Phase 2: FORUM & COMMUNITY SCAN
    Future4200, Grasscity, ICMag, industry Discords/Slacks
    Focus on professional operators discussing sourcing

  Phase 3: REVIEW PLATFORM INTELLIGENCE
    Leafly, Weedmaps — flavor/quality complaints mapped to
    specific companies. Cross-reference with prospect list.

  Phase 4: TWITTER/X & LINKEDIN MONITORING
    Industry accounts, company announcements, thought leaders,
    hiring signals, trade show chatter

  Phase 5: CROSS-SOURCE CORRELATION
    Connect signals across platforms. Company X has bad Leafly
    reviews + Reddit complaints + posted a formulator job =
    compounding signal that they need better terpenes.

  Phase 6: DIGEST SYNTHESIS
    Prioritized daily briefing with specific actions, draft
    messages, community engagement plays, and strategic insights.

Usage:
    python3 social_intel_engine.py --full-scan
    python3 social_intel_engine.py --reddit-deep
    python3 social_intel_engine.py --scan-company "Mellow Fellow"
    python3 social_intel_engine.py --scan-competitor "True Terpenes"
    python3 social_intel_engine.py --quick-scan (lighter, 3 phases only)

Environment:
    ANTHROPIC_API_KEY
"""

import os, sys, json, re, time, argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: pip install requests"); sys.exit(1)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-5-20250929"

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
INTEL_DIR = OUTPUT_DIR / "social_intel"
DIGEST_DIR = OUTPUT_DIR / "digests"
HISTORY_DIR = OUTPUT_DIR / "social_history"

for d in [OUTPUT_DIR, INTEL_DIR, DIGEST_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

SUBREDDITS = [
    "CannabisExtracts", "Dabs", "delta8", "hemp", "concentrates",
    "oilpen", "hempflowers", "waxpen", "cleancarts", "vaporents",
    "cannabisprocessing", "delta9", "THCa",
]

COMPETITORS = ["True Terpenes", "Abstrax", "Floraplex", "Denver Terpenes", "Peak Supply Co", "Mr Extractor", "Xtra Laboratories"]


# ─── CORE ──────────────────────────────────────────────────

def call_claude(system, prompt, max_tokens=4096):
    headers = {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}
    payload = {"model": MODEL, "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": prompt}], "tools": [{"type": "web_search_20250305", "name": "web_search"}]}
    for attempt in range(3):
        try:
            resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=300)
            if resp.status_code == 429:
                wait = 30 * (attempt + 1); print(f"      ⏳ Rate limited, waiting {wait}s..."); time.sleep(wait); continue
            if resp.status_code != 200: print(f"      ❌ Error {resp.status_code}"); return ""
            return "\n".join(b["text"] for b in resp.json().get("content", []) if b.get("type") == "text")
        except Exception as e: print(f"      ❌ {e}"); return ""
    return ""

def parse_json(response):
    if not response: return None
    m = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
    if m:
        try: return json.loads(m.group(1).strip())
        except: pass
    depth = 0; start = None
    for i, c in enumerate(response):
        if c == '{':
            if depth == 0: start = i
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try: return json.loads(response[start:i+1])
                except: start = None
    depth = 0; start = None
    for i, c in enumerate(response):
        if c == '[':
            if depth == 0: start = i
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0 and start is not None:
                try: return json.loads(response[start:i+1])
                except: start = None
    return None

def reddit_api(endpoint, params=None):
    """Reddit public JSON API request."""
    url = f"https://www.reddit.com{endpoint}.json"
    headers = {"User-Agent": "NexusBDR/2.0"}
    try:
        resp = requests.get(url, params=params or {}, headers=headers, timeout=15)
        if resp.status_code == 200: return resp.json()
        if resp.status_code == 429: time.sleep(5)
        return None
    except: return None

def load_history():
    """Load previously seen post URLs to detect what's new."""
    path = HISTORY_DIR / "seen_urls.json"
    if path.exists():
        with open(path) as f: return json.load(f)
    return {"urls": [], "last_scan": None}

def save_history(seen_urls):
    """Save seen URLs."""
    # Keep only last 5000 URLs
    path = HISTORY_DIR / "seen_urls.json"
    with open(path, "w") as f:
        json.dump({"urls": seen_urls[-5000:], "last_scan": datetime.utcnow().isoformat()}, f)


# ─── PHASE 1: REDDIT DEEP SCAN ────────────────────────────

def phase_1a_reddit_harvest():
    """1a: Pull raw posts from all subreddits via API."""
    print("    📡 Harvesting posts from Reddit API...")
    all_posts = []

    for sub in SUBREDDITS:
        print(f"      r/{sub}...", end=" ", flush=True)
        data = reddit_api(f"/r/{sub}/new", {"limit": 25, "t": "week"})
        if data:
            posts = []
            for child in data.get("data", {}).get("children", []):
                p = child.get("data", {})
                posts.append({
                    "id": p.get("id", ""),
                    "title": p.get("title", ""),
                    "selftext": (p.get("selftext", "") or "")[:800],
                    "author": p.get("author", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "created_utc": p.get("created_utc", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "subreddit": sub,
                    "flair": p.get("link_flair_text", ""),
                })
            print(f"{len(posts)} posts")
            all_posts.extend(posts)
        else:
            print("skip")
        time.sleep(1.2)

    # Also search across all of Reddit
    searches = [
        "terpene supplier",
        "botanical terpenes",
        "distillate flavor",
        "cart filling terpenes",
        "True Terpenes review",
        "extraction scaling production",
        "cannabis license 2026",
        "switching terpene supplier",
    ]
    print(f"\n    🔍 Cross-Reddit searches...")
    for q in searches:
        print(f"      \"{q}\"...", end=" ", flush=True)
        data = reddit_api("/search", {"q": q, "sort": "new", "limit": 15, "t": "month"})
        if data:
            for child in data.get("data", {}).get("children", []):
                p = child.get("data", {})
                all_posts.append({
                    "id": p.get("id", ""),
                    "title": p.get("title", ""),
                    "selftext": (p.get("selftext", "") or "")[:800],
                    "author": p.get("author", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "subreddit": p.get("subreddit", ""),
                    "search_query": q,
                })
            print(f"{len(data.get('data',{}).get('children',[]))} results")
        else:
            print("skip")
        time.sleep(1.5)

    # Dedup
    seen = set()
    unique = []
    for p in all_posts:
        pid = p.get("id", p.get("url"))
        if pid not in seen:
            seen.add(pid)
            unique.append(p)

    print(f"\n    📊 Harvested: {len(unique)} unique posts")
    return unique


def phase_1b_intent_classification(posts):
    """1b: Claude classifies posts by buyer intent — not keyword matching."""
    print("    🧠 Classifying posts by buyer intent...")

    # Batch posts into chunks for efficient classification
    batch_size = 30
    all_classified = []

    for i in range(0, len(posts), batch_size):
        batch = posts[i:i+batch_size]
        batch_summary = []
        for j, p in enumerate(batch):
            batch_summary.append({
                "idx": i+j,
                "title": p["title"][:150],
                "text": p["selftext"][:300],
                "sub": p.get("subreddit", ""),
                "score": p.get("score", 0),
                "comments": p.get("num_comments", 0),
            })

        system = """You are a sales intelligence analyst for a botanical terpene company. Classify Reddit posts by BUYER INTENT — not just keyword matching. Understand what the person NEEDS even if they don't mention terpenes.

Someone saying "my distillate carts taste like nothing" is a HIGH INTENT terpene buyer even though they didn't say "terpene."
Someone asking "best extraction method?" is LOW INTENT for terpenes specifically.
Someone saying "anyone know a good terp supplier?" is CRITICAL INTENT.

Return ONLY valid JSON — an array of classifications."""

        prompt = f"""Classify these {len(batch_summary)} Reddit posts by buyer intent for a botanical terpene company:

{json.dumps(batch_summary, indent=1)}

For each relevant post, return:
[
  {{
    "idx": 0,
    "intent_tier": "CRITICAL|HIGH|MEDIUM|LOW|NONE",
    "intent_type": "SUPPLIER_SEARCH|QUALITY_PROBLEM|SCALING_OPERATOR|NEW_ENTRANT|COMPETITOR_DISSATISFACTION|FORMULATION_QUESTION|INDUSTRY_NEWS|COMMUNITY_DISCUSSION|NOT_RELEVANT",
    "reasoning": "Why this classification — what does this person actually need?",
    "is_prospect": true,
    "prospect_type": "DIRECT_BUYER|INFLUENCER|COMPETITOR_CUSTOMER|NEW_OPERATOR|NOT_PROSPECT",
    "recommended_action": "OUTREACH_DM|COMMENT_ENGAGE|MONITOR|SAVE_FOR_INTEL|IGNORE",
    "urgency": "Do this today|This week|Passive monitor|Skip"
  }}
]

Only include posts that are MEDIUM or above. Skip NONE/LOW entirely."""

        raw = call_claude(system, prompt)
        classified = parse_json(raw)
        if classified and isinstance(classified, list):
            # Merge classifications back into posts
            idx_map = {c["idx"]: c for c in classified if isinstance(c, dict)}
            for j, p in enumerate(batch):
                c = idx_map.get(i+j)
                if c:
                    p.update(c)
                    all_classified.append(p)
        time.sleep(2)

    # Sort by intent
    tier_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    all_classified.sort(key=lambda x: tier_order.get(x.get("intent_tier", "MEDIUM"), 2))

    critical = sum(1 for p in all_classified if p.get("intent_tier") == "CRITICAL")
    high = sum(1 for p in all_classified if p.get("intent_tier") == "HIGH")
    medium = sum(1 for p in all_classified if p.get("intent_tier") == "MEDIUM")
    print(f"    📊 Classified: {critical} CRITICAL, {high} HIGH, {medium} MEDIUM")

    return all_classified


def phase_1c_thread_deep_dive(classified_posts, max_threads=5):
    """1c: Fetch and analyze full comment threads for top posts."""
    print("    🔬 Deep-diving top threads...")

    # Pick top threads to analyze
    top = [p for p in classified_posts if p.get("intent_tier") in ("CRITICAL", "HIGH")][:max_threads]
    if not top:
        top = classified_posts[:max_threads]

    thread_analyses = []
    for p in top:
        url = p.get("url", "")
        title = p.get("title", "?")
        print(f"      📖 \"{title[:60]}\"...", end=" ", flush=True)

        # Fetch thread comments via Reddit API
        # URL format: /r/sub/comments/id/title/
        permalink = url.replace("https://reddit.com", "")
        data = reddit_api(permalink, {"limit": 50, "sort": "best"})

        comments_text = ""
        if data and isinstance(data, list) and len(data) > 1:
            comment_tree = data[1].get("data", {}).get("children", [])
            comments = []
            for c in comment_tree[:20]:
                cd = c.get("data", {})
                body = cd.get("body", "")
                author = cd.get("author", "")
                score = cd.get("score", 0)
                if body and author != "AutoModerator":
                    comments.append(f"[u/{author} | {score}pts]: {body[:300]}")
            comments_text = "\n".join(comments)

        if not comments_text:
            print("no comments")
            continue

        # Analyze thread with Claude
        system = """You are a sales intelligence analyst reading a full Reddit thread. Extract SPECIFIC, ACTIONABLE intelligence. Identify potential prospects, competitive intel, and engagement opportunities. Return ONLY valid JSON."""

        prompt = f"""Analyze this Reddit thread:

TITLE: {title}
POST: {p.get('selftext', '')[:500]}
SUBREDDIT: r/{p.get('subreddit', '')}
URL: {url}

COMMENTS:
{comments_text[:3000]}

Extract:
{{
  "thread_url": "{url}",
  "thread_title": "{title[:100]}",
  "intelligence_value": "HIGH|MEDIUM|LOW",
  "key_insights": ["Specific things we learned from this thread"],
  "prospects_identified": [
    {{
      "username": "u/someone",
      "evidence": "Why they might buy terpenes",
      "intent_level": "CRITICAL|HIGH|MEDIUM",
      "dm_draft": "Draft Reddit DM — helpful, not salesy. Position as expert sharing knowledge, NOT pitching. Under 100 words."
    }}
  ],
  "competitor_mentions": [
    {{
      "competitor": "",
      "sentiment": "POSITIVE|NEGATIVE|MIXED",
      "what_was_said": "Paraphrased",
      "displacement_angle": "How to use this"
    }}
  ],
  "engagement_opportunity": {{
    "should_comment": true,
    "comment_strategy": "Expert advice|Share experience|Answer question|Provide resource",
    "comment_draft": "Draft comment that positions Nexus as knowledgeable without being salesy. Provide genuine value. Under 150 words. Never mention TBF/DFT directly — just be helpful.",
    "why_this_works": "Why this comment will build authority"
  }},
  "market_signals": ["Any market trends, pricing info, or industry shifts mentioned"],
  "product_insights": ["Any mentions of specific terpene strains, preferences, complaints about flavors"]
}}"""

        raw = call_claude(system, prompt)
        analysis = parse_json(raw)
        if analysis:
            thread_analyses.append(analysis)
            prospects = analysis.get("prospects_identified", [])
            print(f"✅ {len(prospects)} prospects, {len(analysis.get('competitor_mentions',[]))} competitor mentions")
        else:
            print("⚠️")
            if raw: (INTEL_DIR / f"raw_thread_{p.get('id','?')}.txt").write_text(raw)

        time.sleep(3)

    return thread_analyses


# ─── PHASE 2: FORUMS & COMMUNITIES ────────────────────────

def phase_2_forums():
    """Deep scan of Future4200 and other professional forums."""
    print("    🧪 Scanning professional forums...")

    system = """You are a technical intelligence analyst scanning professional cannabis extraction forums. These forums contain operators who actually purchase terpenes. Every insight here is high-value. Do extensive searching. Return ONLY valid JSON."""

    prompt = f"""Search professional extraction forums for terpene intelligence. Do at LEAST 6 searches:

1. "site:future4200.com terpene" — general terpene discussions
2. "site:future4200.com botanical terpene" OR "site:future4200.com terp supplier" — sourcing discussions  
3. "site:future4200.com True Terpenes" OR "site:future4200.com Abstrax" OR "site:future4200.com Floraplex" — competitor mentions
4. "site:future4200.com distillate flavor" OR "site:future4200.com terp reintroduction" — formulation discussions
5. "site:future4200.com terpene 2025" OR "site:future4200.com terpene 2026" — recent discussions
6. "future4200 terpene supplier recommendation" — broader search
7. "cannabis extraction forum terpene sourcing" — catch other forums
8. "site:icmag.com terpene" OR "site:rollitup.org terpene" — other grow/extract forums

For each relevant discussion, assess whether the participants are PURCHASERS of terpenes.

Return:
{{
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "high_value_threads": [
    {{
      "forum": "Future4200|ICMag|Other",
      "title": "",
      "url": "",
      "date": "approximate",
      "participant_count": 0,
      "participant_quality": "Professional operators|Hobbyists|Mixed",
      "discussion_summary": "Detailed summary of what's being discussed",
      "terpene_opinions_expressed": ["Specific opinions about terpene brands, quality, pricing"],
      "suppliers_mentioned": [{{"name":"","sentiment":"","context":""}}],
      "buyer_signals": ["Signs that participants are actively purchasing or evaluating terpenes"],
      "technical_insights": ["Technical info about how they use terpenes — ratios, methods, preferences"],
      "prospect_indicators": ["Users who seem like potential customers"],
      "engagement_strategy": "How to participate in this thread authentically"
    }}
  ],
  "supplier_sentiment_summary": {{
    "True Terpenes": {{"overall":"POSITIVE|NEGATIVE|MIXED","key_feedback":[],"vulnerability":""}},
    "Abstrax": {{"overall":"","key_feedback":[],"vulnerability":""}},
    "Floraplex": {{"overall":"","key_feedback":[],"vulnerability":""}},
    "Others": [{{"name":"","sentiment":"","notes":""}}]
  }},
  "formulation_trends": [
    {{
      "trend": "",
      "detail": "What operators are doing differently",
      "volume_implication": "Does this increase or decrease terpene usage?",
      "product_opportunity": "Which of our products align with this trend"
    }}
  ],
  "pricing_intelligence": {{
    "price_points_mentioned": ["Any specific $/L or $/ml figures discussed"],
    "value_perceptions": "What operators consider good value vs overpriced",
    "our_positioning": "How our pricing compares to what the market expects"
  }}
}}"""

    raw = call_claude(system, prompt, max_tokens=4096)
    result = parse_json(raw)
    if result:
        threads = result.get("high_value_threads", [])
        print(f"      ✅ {len(threads)} high-value threads found")
    else:
        print(f"      ⚠️ Parse failed")
        if raw: (INTEL_DIR / f"raw_forums_{datetime.utcnow().strftime('%H%M')}.txt").write_text(raw)
        result = {}
    return result


# ─── PHASE 3: REVIEW INTELLIGENCE ─────────────────────────

def phase_3_reviews(target_companies=None):
    """Product review intelligence from Leafly and Weedmaps."""
    print("    ⭐ Scanning product reviews...")

    company_context = ""
    if target_companies:
        company_context = f"\nFocus on these companies specifically: {', '.join(target_companies[:10])}\n"

    system = """You are a product quality analyst for a terpene company. Scan review platforms to find companies whose products have flavor or quality issues — those are your hottest prospects because better terpenes directly solve their problem. Be specific — name brands, products, and cite review patterns. Return ONLY valid JSON."""

    prompt = f"""Search Leafly and Weedmaps for flavor and quality intelligence. Do at LEAST 6 searches:

1. site:leafly.com "no flavor" OR "tasteless" OR "chemical taste" vape cart review
2. site:weedmaps.com "flavor" OR "taste" vape cartridge review negative
3. site:leafly.com "great flavor" OR "amazing taste" vape — find who's doing it RIGHT
4. site:leafly.com "terpene" review 2025 2026
5. "weedmaps review" "distillate" "flavor" 2025 2026
6. "leafly review" "botanical" OR "CDT" OR "cannabis derived terpene"
{f'7. site:leafly.com "{target_companies[0]}" review' if target_companies else '7. site:leafly.com vape cart flavor review recent'}
{f'8. site:weedmaps.com "{target_companies[0]}" review' if target_companies else '8. site:weedmaps.com concentrate flavor quality review'}
{company_context}

Return:
{{
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "brands_with_flavor_problems": [
    {{
      "brand_name": "",
      "products_affected": ["specific product names"],
      "platform": "Leafly|Weedmaps|Both",
      "complaint_pattern": "What reviewers consistently say about flavor",
      "complaint_volume": "How many negative flavor reviews found",
      "sample_complaints_paraphrased": ["Paraphrased review excerpts"],
      "root_cause_assessment": "Likely cause — bad terps, no terps, synthetic terps, inconsistent batches",
      "our_solution": "Specific TBF/DFT products that would fix this",
      "outreach_priority": "CRITICAL|HIGH|MEDIUM",
      "pitch_angle": "Exactly what to say to this brand about their review problem"
    }}
  ],
  "brands_with_great_flavor": [
    {{
      "brand_name": "",
      "products": [""],
      "what_reviewers_love": "Specific flavor comments",
      "likely_terpene_source": "Botanical|CDT|Unknown — with reasoning",
      "competitive_intel": "Are they buying from our competitors? Evidence?",
      "is_current_customer_potential": "Could they already be buying from us or a competitor?"
    }}
  ],
  "flavor_trend_data": {{
    "most_requested_strains": ["Strains consumers mention wanting most"],
    "flavor_preferences_shifting": "Any shifts in what consumers want — fruity vs gas vs exotic",
    "format_preferences": "Cart vs disposable vs concentrate — which cares most about flavor",
    "our_catalog_gaps": "Strain profiles consumers want that we might not offer"
  }},
  "review_based_prospect_list": [
    {{
      "brand": "",
      "reason": "Why reviews indicate they need better terpenes",
      "urgency": "HIGH|MEDIUM|LOW",
      "estimated_impact": "How much better reviews could get with our terpenes",
      "recommended_outreach": "Specific approach based on review data"
    }}
  ]
}}"""

    raw = call_claude(system, prompt, max_tokens=4096)
    result = parse_json(raw)
    if result:
        problems = result.get("brands_with_flavor_problems", [])
        print(f"      ✅ {len(problems)} brands with flavor issues identified")
    else:
        print(f"      ⚠️ Parse failed")
        if raw: (INTEL_DIR / f"raw_reviews_{datetime.utcnow().strftime('%H%M')}.txt").write_text(raw)
        result = {}
    return result


# ─── PHASE 4: TWITTER & LINKEDIN ──────────────────────────

def phase_4_social_platforms():
    """Twitter/X and LinkedIn monitoring."""
    print("    🐦 Scanning Twitter/X and LinkedIn...")

    system = """You are a social media intelligence analyst monitoring the cannabis and terpene industry on Twitter/X and LinkedIn. Focus on ACTIONABLE signals — company announcements, hiring, product launches, trade shows, thought leadership. Return ONLY valid JSON."""

    prompt = f"""Search Twitter/X and LinkedIn for cannabis/terpene industry intelligence. Do 8+ searches:

1. "terpenes" OR "botanical terpene" twitter.com OR x.com 2025 2026
2. "True Terpenes" OR "Abstrax" OR "Floraplex" twitter
3. "#terpenes" OR "#cannabisextraction" OR "#liveresin" twitter recent
4. cannabis extraction company hiring twitter OR linkedin 2026
5. "MJBizCon" OR "Hall of Flowers" OR "Benzinga Cannabis" 2026 twitter
6. cannabis company expansion announcement twitter 2026
7. "terpene" linkedin article OR post recent
8. cannabis processing facility new license announcement 2026

Return:
{{
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "company_signals": [
    {{
      "company": "",
      "platform": "Twitter|LinkedIn",
      "signal_type": "PRODUCT_LAUNCH|EXPANSION|HIRING|PARTNERSHIP|FUNDING|EVENT|AWARD",
      "detail": "What they announced or posted",
      "url": "",
      "terpene_opportunity": "Why this matters for terpene sales",
      "action": "What to do about it"
    }}
  ],
  "competitor_social_activity": [
    {{
      "competitor": "",
      "platform": "",
      "activity": "What they're posting/promoting",
      "engagement_level": "How much traction they're getting",
      "our_counter": "How to respond or capitalize"
    }}
  ],
  "thought_leaders_and_influencers": [
    {{
      "name": "",
      "handle": "",
      "platform": "",
      "relevance": "Why they matter for terpene sales",
      "recent_content": "What they've been talking about",
      "engagement_opportunity": "How to connect — comment, share, DM",
      "follower_count": ""
    }}
  ],
  "trade_show_intel": [
    {{
      "event": "",
      "date": "",
      "location": "",
      "relevant_exhibitors": ["Companies that might need terpenes"],
      "pre_event_actions": ["What to do before the event"]
    }}
  ],
  "hiring_signals": [
    {{
      "company": "",
      "role_posted": "",
      "platform": "",
      "what_it_signals": "Why this hiring signals terpene purchasing potential",
      "action": "What to do"
    }}
  ],
  "trending_conversations": [
    {{
      "topic": "",
      "platforms": [],
      "our_angle": "How to insert ourselves into this conversation"
    }}
  ]
}}"""

    raw = call_claude(system, prompt, max_tokens=4096)
    result = parse_json(raw)
    if result:
        signals = result.get("company_signals", [])
        leaders = result.get("thought_leaders_and_influencers", [])
        print(f"      ✅ {len(signals)} company signals, {len(leaders)} influencers identified")
    else:
        print(f"      ⚠️ Parse failed")
        if raw: (INTEL_DIR / f"raw_social_{datetime.utcnow().strftime('%H%M')}.txt").write_text(raw)
        result = {}
    return result


# ─── PHASE 5: CROSS-SOURCE CORRELATION ────────────────────

def phase_5_correlation(reddit_classified, threads, forums, reviews, social):
    """Connect signals across platforms into compounding intelligence."""
    print("    🔗 Cross-correlating signals across all sources...")

    system = """You are a senior intelligence analyst. Multiple sources have been scanned. Your job is to find PATTERNS — signals that appear across multiple platforms that compound into stronger intelligence than any single source provides.

A company with bad Leafly reviews + Reddit complaints + a job posting for a formulator = CRITICAL SIGNAL that they're about to change terpene suppliers.

A competitor getting negative Reddit sentiment + losing customers on Future4200 + quiet on social media = VULNERABILITY to exploit.

Return ONLY valid JSON."""

    # Prepare condensed summaries of each source
    reddit_summary = []
    for p in reddit_classified[:20]:
        reddit_summary.append({
            "title": p.get("title", "")[:100],
            "intent": p.get("intent_tier", ""),
            "type": p.get("intent_type", ""),
            "sub": p.get("subreddit", ""),
        })

    prompt = f"""Cross-correlate these intelligence sources:

REDDIT CLASSIFIED POSTS ({len(reddit_classified)} relevant):
{json.dumps(reddit_summary, indent=1)[:2000]}

THREAD DEEP-DIVES:
{json.dumps(threads[:5], indent=1, default=str)[:2000]}

FORUM INTELLIGENCE:
{json.dumps(forums, indent=1, default=str)[:2000]}

REVIEW INTELLIGENCE:
{json.dumps(reviews, indent=1, default=str)[:2000]}

SOCIAL PLATFORM SIGNALS:
{json.dumps(social, indent=1, default=str)[:2000]}

Find cross-source patterns:
{{
  "compounding_signals": [
    {{
      "entity": "Company or person name",
      "signal_strength": "CRITICAL|STRONG|MODERATE",
      "sources": ["Reddit", "Leafly", "Twitter"],
      "evidence_chain": [
        {{"source": "Reddit", "signal": "what we found"}},
        {{"source": "Leafly", "signal": "what we found"}},
        {{"source": "Twitter", "signal": "what we found"}}
      ],
      "synthesis": "What these signals TOGETHER tell us that no single source reveals",
      "recommended_action": "Specific, prioritized action",
      "urgency": "Immediate|This week|This month",
      "estimated_opportunity": "$ potential if we act on this"
    }}
  ],
  "competitor_vulnerability_map": [
    {{
      "competitor": "",
      "vulnerability": "Specific weakness revealed across sources",
      "evidence": ["Source 1 says...", "Source 2 says..."],
      "exploitation_strategy": "How to use this to win their customers",
      "target_accounts": ["Specific companies we should approach who use this competitor"]
    }}
  ],
  "market_narrative": {{
    "current_state": "What the market conversation is telling us overall",
    "direction": "Where things are heading",
    "our_position": "How Nexus/TBF/DFT is positioned relative to the conversation",
    "strategic_recommendations": ["What to do about the broader market narrative"]
  }},
  "emerging_opportunities": [
    {{
      "opportunity": "",
      "evidence_sources": [],
      "time_sensitivity": "Act now|This quarter|Long-term",
      "potential_value": "",
      "next_step": ""
    }}
  ],
  "blind_spots": ["Things we should be tracking that we're not seeing enough signal on"]
}}"""

    raw = call_claude(system, prompt, max_tokens=4096)
    result = parse_json(raw)
    if result:
        compounds = result.get("compounding_signals", [])
        vulns = result.get("competitor_vulnerability_map", [])
        print(f"      ✅ {len(compounds)} compounding signals, {len(vulns)} competitor vulnerabilities")
    else:
        print(f"      ⚠️ Parse failed")
        if raw: (INTEL_DIR / f"raw_correlation_{datetime.utcnow().strftime('%H%M')}.txt").write_text(raw)
        result = {}
    return result


# ─── PHASE 6: DIGEST SYNTHESIS ─────────────────────────────

def phase_6_digest(all_phases):
    """Synthesize everything into prioritized daily digest."""
    print("    📰 Synthesizing daily digest...")

    system = """You are the Chief Intelligence Officer for Nexus Agriscience. Create a daily intelligence digest that a sales team can read in 10 minutes and take action on immediately.

RULES:
- Lead with ACTIONS, not data
- Every action must have a draft message or specific next step
- Rank everything by revenue potential
- Be specific — names, companies, URLs, dollar amounts
- Include community engagement plays — where to comment, what to say
- The team should finish reading and know exactly what to do today

Return ONLY valid JSON."""

    prompt = f"""Create the daily intelligence digest from these 5 phases:

REDDIT (classified posts + thread analyses):
{json.dumps(all_phases.get('reddit_classified', [])[:15], indent=1, default=str)[:1500]}
{json.dumps(all_phases.get('thread_analyses', [])[:3], indent=1, default=str)[:1500]}

FORUMS:
{json.dumps(all_phases.get('forums', {}), indent=1, default=str)[:1500]}

REVIEWS:
{json.dumps(all_phases.get('reviews', {}), indent=1, default=str)[:1500]}

SOCIAL:
{json.dumps(all_phases.get('social', {}), indent=1, default=str)[:1500]}

CROSS-CORRELATIONS:
{json.dumps(all_phases.get('correlation', {}), indent=1, default=str)[:2000]}

Generate:
{{
  "digest_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "executive_summary": "4-5 sentence overview. What's the single most important thing today?",
  "priority_score": 0,

  "do_right_now": [
    {{
      "rank": 1,
      "action": "Specific action",
      "target": "Company or person",
      "channel": "Reddit DM|Email|LinkedIn|Comment|Phone",
      "context": "Why now — what triggered this",
      "source_url": "",
      "revenue_potential": "$ estimate",
      "draft_message": "Complete draft — ready to send. Under 150 words. Genuinely helpful, not salesy.",
      "follow_up": "What to do after sending"
    }}
  ],

  "community_engagement_plays": [
    {{
      "platform": "Reddit|Future4200|Twitter|LinkedIn",
      "thread_url": "",
      "what_to_do": "Comment|Post|Share|DM",
      "strategy": "Expert advice|Answer question|Share insight|Build rapport",
      "draft_content": "Exact text to post. Provides genuine value. NEVER mentions TBF or DFT by name. Positions you as a terpene expert who happens to help people.",
      "expected_outcome": "Build authority|Generate DM|Create opportunity"
    }}
  ],

  "competitor_intelligence_brief": {{
    "headline": "Most important competitive development",
    "details": [{{"competitor":"","situation":"","our_play":"","talking_points":[]}}],
    "vulnerability_to_exploit": "The single biggest competitor weakness right now"
  }},

  "market_intelligence": {{
    "sentiment": "BULLISH|NEUTRAL|BEARISH on terpene market",
    "top_3_trends": [
      {{"trend":"","evidence":"","our_play":"What to do about it"}}
    ],
    "hot_strains_this_week": ["Strains getting consumer buzz"],
    "emerging_formats": ["Product types gaining traction"]
  }},

  "prospect_radar": [
    {{
      "prospect": "Company or username",
      "source": "Where detected",
      "signal": "What they did/said",
      "fit": "Why they'd buy terpenes",
      "priority": "CRITICAL|HIGH|MEDIUM",
      "next_step": "Specific action to take"
    }}
  ],

  "content_calendar": [
    {{
      "this_week": "Topic to post about based on what the market is discussing",
      "platform": "Where to post",
      "angle": "Our unique take",
      "draft": "Draft post text"
    }}
  ],

  "watchlist_changes": [
    {{"entity":"","direction":"UP|DOWN","reason":""}}
  ],

  "tomorrow_preview": "Based on today's signals, what to watch for tomorrow"
}}"""

    raw = call_claude(system, prompt, max_tokens=5000)
    result = parse_json(raw)
    if result:
        actions = result.get("do_right_now", [])
        plays = result.get("community_engagement_plays", [])
        print(f"      ✅ Digest: {len(actions)} actions, {len(plays)} engagement plays")
    else:
        print(f"      ⚠️ Parse failed")
        if raw: (INTEL_DIR / f"raw_digest_{datetime.utcnow().strftime('%H%M')}.txt").write_text(raw)
        result = {}
    return result


# ─── RENDER ────────────────────────────────────────────────

def render_digest_md(digest):
    d = digest
    md = f"""# 🌅 Nexus Intelligence Digest — {d.get('digest_date', 'today')}
*Priority Score: {d.get('priority_score', '?')}/10*

---

## Executive Summary

{d.get('executive_summary', 'N/A')}

---

## ⚡ Do Right Now

"""
    for a in d.get("do_right_now", []):
        md += f"""### #{a.get('rank','?')} — {a.get('action','')}
**Target:** {a.get('target','')} | **Channel:** {a.get('channel','')} | **Revenue:** {a.get('revenue_potential','')}

*Why now:* {a.get('context','')}
*Source:* {a.get('source_url','')}

**Message:**
```
{a.get('draft_message','')}
```

*Follow-up:* {a.get('follow_up','')}

"""

    plays = d.get("community_engagement_plays", [])
    if plays:
        md += "---\n\n## 🎯 Community Engagement Plays\n\n"
        for p in plays:
            md += f"""### {p.get('platform','')} — {p.get('what_to_do','')}
*Strategy:* {p.get('strategy','')} | *Expected:* {p.get('expected_outcome','')}
*Thread:* {p.get('thread_url','')}

```
{p.get('draft_content','')}
```

"""

    comp = d.get("competitor_intelligence_brief", {})
    if comp.get("headline"):
        md += f"---\n\n## ⚔️ Competitor Brief\n\n**{comp['headline']}**\n\n"
        for detail in comp.get("details", []):
            md += f"**{detail.get('competitor','')}:** {detail.get('situation','')}\n"
            md += f"- Our play: {detail.get('our_play','')}\n\n"
        if comp.get("vulnerability_to_exploit"):
            md += f"**Exploit this:** {comp['vulnerability_to_exploit']}\n\n"

    market = d.get("market_intelligence", {})
    if market:
        md += f"---\n\n## 📈 Market Intelligence — {market.get('sentiment','?')}\n\n"
        for t in market.get("top_3_trends", []):
            md += f"**{t.get('trend','')}** — {t.get('evidence','')}\n- Our play: {t.get('our_play','')}\n\n"
        hot = market.get("hot_strains_this_week", [])
        if hot: md += f"**Hot strains:** {', '.join(hot)}\n\n"

    prospects = d.get("prospect_radar", [])
    if prospects:
        md += "---\n\n## 🎯 Prospect Radar\n\n"
        for p in prospects:
            emoji = "🔴" if p.get("priority") == "CRITICAL" else "🟡" if p.get("priority") == "HIGH" else "🔵"
            md += f"{emoji} **{p.get('prospect','')}** ({p.get('source','')}) — {p.get('signal','')}\n"
            md += f"- Next: {p.get('next_step','')}\n\n"

    cal = d.get("content_calendar", [])
    if cal:
        md += "---\n\n## 📝 Content Calendar\n\n"
        for c in cal:
            md += f"**{c.get('this_week','')}** on {c.get('platform','')}\n"
            if c.get("draft"): md += f"```\n{c['draft'][:300]}\n```\n\n"

    md += f"\n---\n\n## 🔮 Tomorrow\n\n{d.get('tomorrow_preview', 'N/A')}\n"
    md += "\n---\n*Nexus Social Intelligence Engine v2*\n"
    return md


def display_digest_summary(digest):
    d = digest
    print(f"\n  {'━'*60}")
    print(f"  🌅 DAILY INTELLIGENCE DIGEST")
    print(f"  Priority: {d.get('priority_score', '?')}/10")
    print(f"  {'━'*60}")
    print(f"\n  {d.get('executive_summary', 'N/A')[:300]}")

    actions = d.get("do_right_now", [])
    if actions:
        print(f"\n  ⚡ DO NOW ({len(actions)} actions):")
        for a in actions[:3]:
            print(f"  → [{a.get('rank','?')}] {a.get('action','?')[:80]}")
            print(f"     💰 {a.get('revenue_potential','?')} | 📧 {a.get('channel','?')}")

    plays = d.get("community_engagement_plays", [])
    if plays:
        print(f"\n  🎯 ENGAGE ({len(plays)} plays):")
        for p in plays[:2]:
            print(f"  → {p.get('platform','')} — {p.get('strategy','')[:60]}")

    radar = d.get("prospect_radar", [])
    hot = [p for p in radar if p.get("priority") in ("CRITICAL", "HIGH")]
    if hot:
        print(f"\n  🔴 HOT PROSPECTS ({len(hot)}):")
        for p in hot[:3]:
            print(f"  → {p.get('prospect','?')} — {p.get('signal','')[:60]}")


# ─── COMPANY-SPECIFIC SCAN ────────────────────────────────

def scan_company_deep(company):
    """Multi-source deep scan on a single company."""
    print(f"\n  🎯 Deep social scan: {company}\n")

    system = """You are a social media intelligence analyst doing a comprehensive scan of a single company across all platforms. Search exhaustively. Return ONLY valid JSON."""

    prompt = f"""Deep scan ALL social platforms for "{company}". Do at LEAST 10 searches:

1. "{company}" site:reddit.com
2. "{company}" site:reddit.com review OR complaint OR "anyone tried"
3. "{company}" site:future4200.com
4. "{company}" leafly review
5. "{company}" weedmaps review
6. "{company}" twitter OR x.com
7. "{company}" instagram followers
8. "{company}" linkedin company
9. "{company}" "flavor" OR "taste" OR "terpene" review
10. "{company}" news 2025 2026

Return:
{{
  "company": "{company}",
  "scan_date": "{datetime.utcnow().strftime('%Y-%m-%d')}",
  "social_footprint": {{
    "platforms_active": [],
    "total_mentions_found": 0,
    "overall_sentiment": "POSITIVE|NEGATIVE|MIXED",
    "brand_strength_assessment": "Strong|Growing|Stable|Declining|Weak"
  }},
  "reddit_intelligence": {{
    "threads_found": 0,
    "sentiment": "",
    "key_discussions": [{{"title":"","url":"","summary":"","sentiment":""}}],
    "flavor_feedback": "What Reddit says about their product taste/flavor",
    "terpene_mentions": "Any mentions of their terpene usage"
  }},
  "review_intelligence": {{
    "leafly_rating": "",
    "weedmaps_rating": "",
    "flavor_sentiment": "What reviewers say about flavor",
    "quality_sentiment": "What reviewers say about quality",
    "top_complaints": [],
    "top_praise": [],
    "terpene_opportunity": "How better terpenes would improve their reviews"
  }},
  "social_media_presence": {{
    "instagram": {{"handle":"","followers":0,"engagement":"","content_themes":[]}},
    "twitter": {{"handle":"","activity":"","key_posts":[]}},
    "linkedin": {{"url":"","employee_count":0}}
  }},
  "competitive_position": {{
    "how_consumers_compare_them": "vs which competitors",
    "perceived_tier": "Budget|Mid|Premium|Luxury",
    "market_narrative": "What the social conversation says about this brand"
  }},
  "sales_intelligence": {{
    "terpene_fit_assessment": "HIGH|MEDIUM|LOW — based on social evidence",
    "evidence": ["Specific social signals that indicate terpene purchasing potential"],
    "vulnerability_points": ["Where their social presence reveals pain points we can solve"],
    "best_approach_angle": "Based on their social persona, how should we approach them?",
    "outreach_hooks": ["Specific things from social to reference in outreach"]
  }}
}}"""

    raw = call_claude(system, prompt, max_tokens=4096)
    result = parse_json(raw)
    if result:
        print(f"  ✅ {company} scan complete")
        presence = result.get("social_footprint", {})
        print(f"  📊 Sentiment: {presence.get('overall_sentiment','?')} | Strength: {presence.get('brand_strength_assessment','?')}")
        sales = result.get("sales_intelligence", {})
        print(f"  🎯 Terpene fit: {sales.get('terpene_fit_assessment','?')}")
        for hook in sales.get("outreach_hooks", [])[:3]:
            print(f"  💬 {hook}")
    else:
        if raw: (INTEL_DIR / f"raw_company_{company.replace(' ','_')[:20]}.txt").write_text(raw)
    return result


# ─── MAIN PIPELINE ─────────────────────────────────────────

def run_full_scan():
    """Execute all 6 phases."""
    all_phases = {}
    timings = {}
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")

    phases = [
        ("Phase 1a", "REDDIT HARVEST", lambda: phase_1a_reddit_harvest()),
        ("Phase 1b", "INTENT CLASSIFICATION", lambda: phase_1b_intent_classification(all_phases.get("reddit_raw", []))),
        ("Phase 1c", "THREAD DEEP-DIVES", lambda: phase_1c_thread_deep_dive(all_phases.get("reddit_classified", []))),
        ("Phase 2", "FORUMS & COMMUNITIES", lambda: phase_2_forums()),
        ("Phase 3", "REVIEW INTELLIGENCE", lambda: phase_3_reviews()),
        ("Phase 4", "TWITTER & LINKEDIN", lambda: phase_4_social_platforms()),
        ("Phase 5", "CROSS-CORRELATION", lambda: phase_5_correlation(
            all_phases.get("reddit_classified", []),
            all_phases.get("thread_analyses", []),
            all_phases.get("forums", {}),
            all_phases.get("reviews", {}),
            all_phases.get("social", {}),
        )),
        ("Phase 6", "DIGEST SYNTHESIS", lambda: phase_6_digest(all_phases)),
    ]

    for label, title, fn in phases:
        t0 = time.time()
        print(f"\n  ┌─ {label}: {title}")

        result = fn()
        timings[label] = time.time() - t0

        # Store results
        if label == "Phase 1a":
            all_phases["reddit_raw"] = result if isinstance(result, list) else []
        elif label == "Phase 1b":
            all_phases["reddit_classified"] = result if isinstance(result, list) else []
        elif label == "Phase 1c":
            all_phases["thread_analyses"] = result if isinstance(result, list) else []
        elif label == "Phase 2":
            all_phases["forums"] = result or {}
        elif label == "Phase 3":
            all_phases["reviews"] = result or {}
        elif label == "Phase 4":
            all_phases["social"] = result or {}
        elif label == "Phase 5":
            all_phases["correlation"] = result or {}
        elif label == "Phase 6":
            all_phases["digest"] = result or {}

        print(f"  └─ ✅ {label} complete ({timings[label]:.0f}s)")
        if label not in ("Phase 1a",) and label != phases[-1][0]:
            time.sleep(3)

    total = sum(timings.values())
    print(f"\n  ⏱️  Total scan time: {total:.0f}s ({total/60:.1f} min)")

    # Save everything
    json_path = INTEL_DIR / f"full_scan_{ts}.json"
    with open(json_path, "w") as f:
        json.dump({"metadata": {"scan_date": datetime.utcnow().isoformat(), "total_seconds": total, "timings": timings}, "phases": {k: v for k, v in all_phases.items() if k != "reddit_raw"}}, f, indent=2, default=str)
    print(f"\n  💾 Full scan: {json_path}")

    # Save and display digest
    digest = all_phases.get("digest", {})
    if digest:
        digest_json = DIGEST_DIR / f"digest_{ts}.json"
        with open(digest_json, "w") as f:
            json.dump(digest, f, indent=2)

        digest_md = DIGEST_DIR / f"digest_{ts}.md"
        digest_md.write_text(render_digest_md(digest))

        display_digest_summary(digest)
        print(f"\n  💾 Digest JSON: {digest_json}")
        print(f"  📄 Digest Brief: {digest_md}")

    # Update history
    history = load_history()
    new_urls = [p.get("url", "") for p in all_phases.get("reddit_raw", []) if p.get("url")]
    history["urls"].extend(new_urls)
    save_history(history["urls"])

    return all_phases


def run_quick_scan():
    """Lighter scan — Reddit + Reviews + Digest only."""
    all_phases = {}
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")

    print("\n  ⚡ QUICK SCAN — Reddit + Reviews + Digest\n")

    # Reddit
    print("  ┌─ Reddit harvest...")
    raw = phase_1a_reddit_harvest()
    all_phases["reddit_raw"] = raw
    time.sleep(2)

    print("  ├─ Intent classification...")
    classified = phase_1b_intent_classification(raw)
    all_phases["reddit_classified"] = classified
    time.sleep(2)

    # Reviews
    print("  ├─ Review intelligence...")
    reviews = phase_3_reviews()
    all_phases["reviews"] = reviews or {}
    time.sleep(2)

    # Quick digest
    print("  └─ Generating digest...")
    all_phases["forums"] = {}
    all_phases["social"] = {}
    all_phases["thread_analyses"] = []
    all_phases["correlation"] = {}
    digest = phase_6_digest(all_phases)
    all_phases["digest"] = digest or {}

    if digest:
        digest_md = DIGEST_DIR / f"quick_digest_{ts}.md"
        digest_md.write_text(render_digest_md(digest))
        display_digest_summary(digest)
        print(f"\n  📄 Digest: {digest_md}")


def main():
    parser = argparse.ArgumentParser(description="Social Intelligence Engine v2 — Nexus BDR")
    parser.add_argument("--full-scan", action="store_true", help="Full 6-phase scan")
    parser.add_argument("--quick-scan", action="store_true", help="Quick 3-phase scan")
    parser.add_argument("--reddit-deep", action="store_true", help="Reddit only — all 3 sub-phases")
    parser.add_argument("--scan-company", help="Deep scan a specific company")
    parser.add_argument("--scan-competitor", help="Deep scan a competitor")
    parser.add_argument("--forums-only", action="store_true")
    parser.add_argument("--reviews-only", action="store_true")
    parser.add_argument("--social-only", action="store_true")

    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("  ❌ Set ANTHROPIC_API_KEY"); sys.exit(1)

    print(f"\n  {'━'*60}")
    print(f"  📡 NEXUS SOCIAL INTELLIGENCE ENGINE v2")
    print(f"  {datetime.utcnow().strftime('%A, %B %d, %Y')}")
    print(f"  {'━'*60}")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")

    if args.full_scan:
        run_full_scan()
    elif args.quick_scan:
        run_quick_scan()
    elif args.reddit_deep:
        raw = phase_1a_reddit_harvest()
        classified = phase_1b_intent_classification(raw)
        threads = phase_1c_thread_deep_dive(classified)
        path = INTEL_DIR / f"reddit_deep_{ts}.json"
        with open(path, "w") as f:
            json.dump({"classified": classified, "threads": threads}, f, indent=2, default=str)
        print(f"\n  💾 {path}")
    elif args.scan_company:
        result = scan_company_deep(args.scan_company)
        if result:
            path = INTEL_DIR / f"company_{args.scan_company.replace(' ','_').lower()[:20]}_{ts}.json"
            with open(path, "w") as f: json.dump(result, f, indent=2)
            print(f"\n  💾 {path}")
    elif args.scan_competitor:
        result = scan_company_deep(args.scan_competitor)
        if result:
            path = INTEL_DIR / f"competitor_{args.scan_competitor.replace(' ','_').lower()[:20]}_{ts}.json"
            with open(path, "w") as f: json.dump(result, f, indent=2)
            print(f"\n  💾 {path}")
    elif args.forums_only:
        result = phase_2_forums()
        if result:
            path = INTEL_DIR / f"forums_{ts}.json"
            with open(path, "w") as f: json.dump(result, f, indent=2)
            print(f"\n  💾 {path}")
    elif args.reviews_only:
        result = phase_3_reviews()
        if result:
            path = INTEL_DIR / f"reviews_{ts}.json"
            with open(path, "w") as f: json.dump(result, f, indent=2)
            print(f"\n  💾 {path}")
    elif args.social_only:
        result = phase_4_social_platforms()
        if result:
            path = INTEL_DIR / f"social_{ts}.json"
            with open(path, "w") as f: json.dump(result, f, indent=2)
            print(f"\n  💾 {path}")
    else:
        parser.print_help()

    print(f"\n  {'━'*60}\n")

if __name__ == "__main__":
    main()
