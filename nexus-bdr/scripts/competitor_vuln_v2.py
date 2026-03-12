#!/usr/bin/env python3
"""
Competitor Vulnerability Engine v2 — Nexus BDR Agent
======================================================
v1 searched Reddit for competitor brand names. Got 0 results.
B2B terpene suppliers don't get discussed by name on Reddit.

v2 FIX: Search for CATEGORY COMPLAINTS and SWITCHING BEHAVIOR.
People don't say "True Terpenes sucks" — they say:
  "my terps taste synthetic"
  "batch consistency is trash"
  "looking for a new terpene supplier"
  "CDT vs BDT which is better"
  "anyone else have issues with their terp supplier"

ALSO ADDED:
  - Forum scanning (Future4200 is THE B2B cannabis industry forum)
  - Trustpilot detailed review analysis
  - Industry pricing intelligence from public sources
  - Competitive positioning matrix

Usage:
    python3 competitor_vuln_v2.py --scan
    python3 competitor_vuln_v2.py --scan --days 14
"""

import os, sys, json, re, time, argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from collections import defaultdict

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs" if (SCRIPT_DIR / "outputs").exists() else SCRIPT_DIR.parent / "outputs"
VULN_DIR = OUTPUT_DIR / "competitor_intel"
VULN_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"}

# ═══════════════════════════════════════════════════════════
# COMPETITOR DATABASE (unchanged from v1)
# ═══════════════════════════════════════════════════════════

COMPETITORS = {
    "True Terpenes": {
        "domain": "trueterpenes.com",
        "pricing_botanical": "$80-150/L",
        "pricing_cdt": "$2,000-4,000/L",
        "known_weaknesses": ["slow custom orders (4-6 weeks)", "quality complaints on recent batches", "corporate feel", "price increases 2024-2025"],
        "market_position": "Market leader, premium botanical + CDT",
        "tbf_angle": "TBF offers faster custom turnaround, better batch consistency, competitive pricing at scale",
        "dft_angle": "DFT offers hype strains True Terpenes doesn't carry, faster shipping, no minimum BS",
    },
    "Abstrax Tech": {
        "domain": "abstraxtech.com",
        "pricing_botanical": "$120-200/L",
        "pricing_cdt": "$3,000-6,000/L",
        "known_weaknesses": ["expensive", "complex ordering process", "slow response times", "overengineered for small operators"],
        "market_position": "Science/R&D focused, premium CDT",
        "tbf_angle": "TBF matches scientific rigor with simpler ordering and faster turnaround",
        "dft_angle": "DFT is for operators who want great terps without the PhD-level ordering process",
    },
    "Floraplex": {
        "domain": "floraplex.com",
        "pricing_botanical": "$40-80/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["inconsistent quality", "synthetic undertones", "batch variation", "no custom blending", "poor customer service"],
        "market_position": "Budget botanical, 200+ strains",
        "tbf_angle": "TBF delivers consistency Floraplex can't at competitive volume pricing",
        "dft_angle": "DFT offers authentic strain profiles without the synthetic aftertaste",
    },
    "Denver Terpenes": {
        "domain": "denverterpenes.com",
        "pricing_botanical": "$60-120/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["limited strain selection", "can't scale", "regional only"],
        "market_position": "Regional CO supplier",
        "tbf_angle": "TBF offers national scale and consistency Denver can't match",
        "dft_angle": "DFT has 3x the strain library with exotic/hype profiles",
    },
    "Peak Supply Co": {
        "domain": "peaksupplyco.com",
        "pricing_botanical": "$50-90/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["limited B2B infrastructure", "DTC focused", "inconsistent availability"],
        "market_position": "DTC terpene supplier",
        "tbf_angle": "TBF offers real B2B infrastructure and dedicated account management",
        "dft_angle": "DFT offers better hype strain accuracy and craft attention",
    },
    "Terps USA": {
        "domain": "terpsusa.com",
        "pricing_botanical": "$35-70/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["bottom-tier quality", "synthetic", "no COAs"],
        "market_position": "Budget/discount",
        "tbf_angle": "TBF provides actual cannabis-origin quality at enterprise pricing",
        "dft_angle": "DFT delivers real strain profiles at slight premium over synthetic",
    },
    "Extract Consultants": {
        "domain": "extractconsultants.com",
        "pricing_botanical": "$70-120/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["formulation focused not production", "limited strain library", "slow innovation"],
        "market_position": "Formulation consulting + terpenes",
        "tbf_angle": "TBF offers formulation support with actual production scale",
        "dft_angle": "DFT offers fresher, trendier profiles",
    },
}

# ═══════════════════════════════════════════════════════════
# v2 FIX: CATEGORY-BASED SEARCH QUERIES
# People don't say "True Terpenes sucks" — they say these things:
# ═══════════════════════════════════════════════════════════

CATEGORY_SEARCHES = {
    "supplier_complaints": [
        "terpene supplier issues",
        "terpenes taste synthetic",
        "terpene quality inconsistent",
        "batch consistency terpenes",
        "terpene supplier problems",
    ],
    "switching_behavior": [
        "looking for terpene supplier",
        "new terpene supplier recommendation",
        "best terpene supplier 2025",
        "best terpene supplier 2026",
        "switching terpene supplier",
        "terpene supplier recommendation",
    ],
    "cdt_vs_bdt_debate": [
        "CDT vs BDT",
        "cannabis derived terpenes vs botanical",
        "botanical terpenes worth it",
        "CDT terpenes price",
        "are botanical terpenes good",
    ],
    "quality_discussion": [
        "terpene COA lab results",
        "terpene purity testing",
        "fake terpenes",
        "synthetic terpenes dangerous",
        "natural vs synthetic terpenes",
    ],
    "formulation_needs": [
        "custom terpene blend",
        "terpene formulation help",
        "terpene ratio vape",
        "how much terpene to add",
        "terpene percentage cart",
    ],
    "brand_mentions": [
        "true terpenes",
        "abstrax tech",
        "floraplex terpenes",
        "peak supply terpenes",
        "terps usa",
        "extract consultants terpenes",
        "denver terpenes",
    ],
    "pricing_discussion": [
        "terpene price per liter",
        "bulk terpenes cost",
        "wholesale terpenes",
        "cheapest terpenes",
        "terpene pricing",
    ],
}

REDDIT_SUBS = [
    "delta8", "altcannabinoids", "CBD", "cannabisextracts",
    "CannabisExtracts", "vaporents", "hempflowers", "cleancarts",
    "Dabs", "FLMedicalTrees", "hemp", "oilpen",
    "DIY_eJuice", "concentrates",
]

# ═══════════════════════════════════════════════════════════
# SIGNAL DETECTION
# ═══════════════════════════════════════════════════════════

COMPLAINT_SIGNALS = [
    "disappointed", "terrible", "awful", "worst", "horrible",
    "never again", "switched from", "stopped using", "used to use",
    "quality dropped", "not what it used to be", "went downhill",
    "inconsistent", "batch variation", "different every time",
    "synthetic", "chemical taste", "artificial", "off taste", "off flavor",
    "overpriced", "too expensive", "not worth", "rip off", "ripoff",
    "slow shipping", "took forever", "still waiting", "no response",
    "bad customer service", "won't respond", "ghosted", "no reply",
    "would not recommend", "stay away", "don't buy", "avoid",
    "anyone else have problems", "am i the only one",
    "headache", "harsh", "burning", "throat", "cough",
    "doesn't taste like", "nothing like", "false advertising",
]

SWITCHING_SIGNALS = [
    "looking for", "need a supplier", "need new", "who sells",
    "recommend", "recommendation", "suggestions",
    "better than", "alternative to", "replacement for",
    "switching from", "switched to", "moved to", "trying",
    "anyone know", "where can i", "where do you",
    "tired of", "fed up", "done with", "over it",
    "what do you use", "what supplier", "where to buy",
    "best place to get", "best source for",
]

COMPETITOR_MENTIONS = {}
for name, info in COMPETITORS.items():
    terms = [name.lower()]
    terms.append(info["domain"].replace(".com", "").lower())
    # Add variations
    terms.extend([
        name.lower().replace(" ", ""),
        name.lower().replace("tech", "").strip(),
    ])
    COMPETITOR_MENTIONS[name] = [t for t in terms if len(t) > 3]


def classify_post(title, body):
    """Classify a post by category and extract intelligence."""
    text = f"{title} {body}".lower()

    result = {
        "complaints": [s for s in COMPLAINT_SIGNALS if s in text],
        "switching": [s for s in SWITCHING_SIGNALS if s in text],
        "competitors_mentioned": [],
        "is_supplier_seeking": False,
        "is_complaint": False,
        "is_comparison": False,
        "is_pricing": False,
        "intent_score": 0,
    }

    # Check competitor mentions
    for comp_name, terms in COMPETITOR_MENTIONS.items():
        for t in terms:
            if t in text:
                result["competitors_mentioned"].append(comp_name)
                break

    # Classify intent
    result["is_supplier_seeking"] = len(result["switching"]) >= 1
    result["is_complaint"] = len(result["complaints"]) >= 1
    result["is_comparison"] = "vs" in text or "versus" in text or "compared to" in text or "better than" in text
    result["is_pricing"] = any(w in text for w in ["price", "cost", "cheap", "expensive", "$", "per liter", "bulk"])

    # Intent score: higher = more actionable for TBF/DFT
    if result["is_supplier_seeking"]:
        result["intent_score"] += 30
    if result["is_complaint"]:
        result["intent_score"] += 20
    if result["competitors_mentioned"]:
        result["intent_score"] += 15
    if result["is_comparison"]:
        result["intent_score"] += 10
    if result["is_pricing"]:
        result["intent_score"] += 5
    # Boost for multiple signals
    result["intent_score"] += len(result["complaints"]) * 3
    result["intent_score"] += len(result["switching"]) * 5

    return result


# ═══════════════════════════════════════════════════════════
# REDDIT CATEGORY SCAN
# ═══════════════════════════════════════════════════════════

def scan_reddit_categories(days_back=30):
    """Scan Reddit using category-based queries instead of brand names."""
    all_posts = []
    seen_urls = set()

    print(f"  ┌─ Reddit Category Scan")
    print(f"  │  {len(CATEGORY_SEARCHES)} categories × {len(REDDIT_SUBS)} subreddits")

    for category, queries in CATEGORY_SEARCHES.items():
        category_count = 0

        for query in queries:
            for sub in REDDIT_SUBS:
                url = f"https://www.reddit.com/r/{sub}/search.json"
                params = {
                    "q": query,
                    "restrict_sr": "1",
                    "sort": "new",
                    "limit": 15,
                    "t": "month" if days_back <= 30 else "year",
                }

                try:
                    resp = requests.get(url, params=params,
                                       headers={"User-Agent": "NexusBDR/2.0 (market research)"},
                                       timeout=12)
                    if resp.status_code == 429:
                        time.sleep(3)
                        continue
                    if resp.status_code != 200:
                        continue

                    cutoff = datetime.utcnow() - timedelta(days=days_back)
                    posts = resp.json().get("data", {}).get("children", [])

                    for post in posts:
                        p = post.get("data", {})
                        post_url = f"https://reddit.com{p.get('permalink', '')}"
                        if post_url in seen_urls:
                            continue
                        seen_urls.add(post_url)

                        created = datetime.utcfromtimestamp(p.get("created_utc", 0))
                        if created < cutoff:
                            continue

                        title = p.get("title", "")
                        body = p.get("selftext", "")
                        classification = classify_post(title, body)

                        # Only keep posts with some signal
                        if classification["intent_score"] < 5:
                            continue

                        post_data = {
                            "subreddit": sub,
                            "title": title,
                            "body": body[:800],
                            "author": p.get("author", ""),
                            "score": p.get("score", 0),
                            "comments": p.get("num_comments", 0),
                            "url": post_url,
                            "created": created.isoformat(),
                            "search_query": query,
                            "search_category": category,
                            **classification,
                        }
                        all_posts.append(post_data)
                        category_count += 1

                except Exception:
                    continue

                time.sleep(0.6)  # Rate limit

        print(f"  │  {category}: {category_count} signals")

    # Sort by intent score
    all_posts.sort(key=lambda x: x["intent_score"], reverse=True)

    # Summarize
    supplier_seeking = [p for p in all_posts if p["is_supplier_seeking"]]
    complaints = [p for p in all_posts if p["is_complaint"]]
    comparisons = [p for p in all_posts if p["is_comparison"]]
    with_competitor = [p for p in all_posts if p["competitors_mentioned"]]

    print(f"  │")
    print(f"  │  Total signals: {len(all_posts)}")
    print(f"  │  Supplier-seeking: {len(supplier_seeking)}")
    print(f"  │  Complaints: {len(complaints)}")
    print(f"  │  Comparisons: {len(comparisons)}")
    print(f"  │  Naming competitors: {len(with_competitor)}")
    print(f"  └─ ✅ Reddit scan complete")

    return {
        "total_signals": len(all_posts),
        "supplier_seeking": len(supplier_seeking),
        "complaints": len(complaints),
        "comparisons": len(comparisons),
        "with_competitor_mention": len(with_competitor),
        "posts": all_posts,
        "top_actionable": all_posts[:20],
    }


# ═══════════════════════════════════════════════════════════
# TRUSTPILOT DEEP SCAN
# ═══════════════════════════════════════════════════════════

def scan_trustpilot():
    """Pull Trustpilot ratings for all competitors."""
    print(f"\n  ┌─ Trustpilot Review Analysis")
    results = {}

    for name, info in COMPETITORS.items():
        domain = info["domain"]
        tp_url = f"https://www.trustpilot.com/review/{domain}"
        try:
            resp = requests.get(tp_url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                rating_match = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', resp.text)
                count_match = re.search(r'"reviewCount"\s*:\s*"?(\d+)"?', resp.text)
                rating = float(rating_match.group(1)) if rating_match else None
                count = int(count_match.group(1)) if count_match else None

                if rating:
                    results[name] = {"rating": rating, "count": count, "url": tp_url}
                    emoji = "🔴" if rating < 3.5 else "🟡" if rating < 4.0 else "🟢"
                    print(f"  │  {emoji} {name}: {rating}/5.0 ({count or '?'} reviews)")
                else:
                    print(f"  │  · {name}: No Trustpilot profile")
            else:
                print(f"  │  · {name}: Not on Trustpilot")
        except:
            print(f"  │  · {name}: Error")

    print(f"  └─ ✅ Trustpilot scan complete")
    return results


# ═══════════════════════════════════════════════════════════
# WEBSITE INTELLIGENCE
# ═══════════════════════════════════════════════════════════

def scan_websites():
    """Check competitor websites for pricing, hiring, and product changes."""
    print(f"\n  ┌─ Website Intelligence")
    results = {}

    for name, info in COMPETITORS.items():
        domain = info["domain"]
        result = {"domain": domain, "status": None, "prices": [], "hiring": False}

        try:
            resp = requests.get(f"https://{domain}", headers=HEADERS, timeout=10)
            result["status"] = resp.status_code
            if resp.status_code == 200:
                text_lower = resp.text.lower()
                # Prices
                prices = re.findall(r'\$[\d,]+\.?\d*(?:\s*/\s*[a-zA-Z]+)?', resp.text)
                result["prices"] = list(set(prices))[:10]
                # Hiring
                result["hiring"] = any(w in text_lower for w in ["careers", "hiring", "job opening", "join our team"])
                # Product count hints
                product_indicators = len(re.findall(r'add.to.cart|buy.now|shop.now', text_lower))
                result["product_indicators"] = product_indicators

            status = "UP" if result["status"] == 200 else f"HTTP {result['status']}"
            hiring = " | HIRING ⚠️" if result["hiring"] else ""
            prices = f" | {len(result['prices'])} prices" if result["prices"] else ""
            print(f"  │  {name}: {status}{hiring}{prices}")

        except Exception as e:
            result["error"] = str(e)[:60]
            print(f"  │  {name}: Error")

        results[name] = result

        # Check careers pages
        for path in ["/careers", "/jobs", "/pages/careers"]:
            try:
                r = requests.get(f"https://{domain}{path}", headers=HEADERS, timeout=5)
                if r.status_code == 200 and any(w in r.text.lower() for w in ["apply", "position", "role"]):
                    results[name]["hiring"] = True
                    results[name]["careers_url"] = f"https://{domain}{path}"
                    break
            except:
                continue

    print(f"  └─ ✅ Website scan complete")
    return results


# ═══════════════════════════════════════════════════════════
# NEWS & INDUSTRY SCAN
# ═══════════════════════════════════════════════════════════

def scan_industry_news(days_back=30):
    """Scan Google News for terpene industry intelligence."""
    print(f"\n  ┌─ Industry News Scan")

    queries = [
        "terpene supplier market 2026",
        "cannabis terpene industry",
        "terpene extraction company",
        "botanical terpene market",
        "cannabis derived terpene regulation",
        "terpene company funding acquisition",
    ]

    all_articles = []
    seen = set()

    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>.*?</item>', resp.text, re.DOTALL)
                for title, link, date in items[:5]:
                    title = re.sub(r'<.*?>', '', title).strip()
                    if title not in seen:
                        seen.add(title)
                        # Check for competitor mentions
                        mentioned = [n for n in COMPETITORS if n.lower() in title.lower()]
                        all_articles.append({
                            "title": title,
                            "url": link.strip(),
                            "date": date.strip(),
                            "competitors_mentioned": mentioned,
                        })
        except:
            pass
        time.sleep(1)

    print(f"  │  {len(all_articles)} unique articles")
    print(f"  └─ ✅ News scan complete")
    return all_articles


# ═══════════════════════════════════════════════════════════
# MASTER SCAN + REPORT
# ═══════════════════════════════════════════════════════════

def full_scan(days_back=30):
    """Run full competitive intelligence sweep."""
    print(f"\n{'═'*60}")
    print(f"  COMPETITOR VULNERABILITY ENGINE v2")
    print(f"  Category-based intelligence | {days_back}-day lookback")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═'*60}")

    # Run all scans
    reddit = scan_reddit_categories(days_back)
    trustpilot = scan_trustpilot()
    websites = scan_websites()
    news = scan_industry_news(days_back)

    # Build competitor vulnerability scores
    competitor_scores = {}
    for name, info in COMPETITORS.items():
        score = 0
        signals = []

        # Trustpilot penalty
        tp = trustpilot.get(name, {})
        if tp.get("rating"):
            if tp["rating"] < 3.5:
                score += 20
                signals.append(f"Trustpilot {tp['rating']}/5 ({tp.get('count','?')} reviews) — below average")
            elif tp["rating"] < 4.0:
                score += 10
                signals.append(f"Trustpilot {tp['rating']}/5 — room for competitor displacement")

        # Website hiring = possible instability or scaling pain
        ws = websites.get(name, {})
        if ws.get("hiring"):
            score += 5
            signals.append("Active hiring — possible scaling challenges or turnover")

        # Reddit mentions (complaints about them specifically)
        reddit_mentions = [p for p in reddit["posts"] if name in p.get("competitors_mentioned", [])]
        complaint_mentions = [p for p in reddit_mentions if p["is_complaint"]]
        score += len(complaint_mentions) * 8
        if complaint_mentions:
            signals.append(f"{len(complaint_mentions)} Reddit complaints mentioning {name}")

        # Known weakness severity
        score += len(info.get("known_weaknesses", [])) * 2

        competitor_scores[name] = {
            "score": score,
            "risk": "HIGH" if score >= 20 else "MEDIUM" if score >= 10 else "LOW",
            "signals": signals,
            "trustpilot": tp,
            "hiring": ws.get("hiring", False),
            "reddit_mentions": len(reddit_mentions),
            "reddit_complaints": len(complaint_mentions),
        }

    # ═══ GENERATE REPORT ═══
    report = {
        "scan_date": datetime.utcnow().isoformat(),
        "period_days": days_back,
        "reddit": reddit,
        "trustpilot": trustpilot,
        "websites": websites,
        "news": news,
        "competitor_scores": competitor_scores,
        "ranked": sorted(competitor_scores.items(), key=lambda x: x[1]["score"], reverse=True),
    }

    # Save JSON
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    json_path = VULN_DIR / f"vuln_v2_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Generate markdown
    md_path = generate_report(report)

    # Print summary
    print(f"\n{'═'*60}")
    print(f"  INTELLIGENCE SUMMARY")
    print(f"  Reddit: {reddit['total_signals']} signals ({reddit['supplier_seeking']} seeking suppliers)")
    print(f"\n  COMPETITOR RANKING:")
    for name, data in report["ranked"]:
        emoji = "🔴" if data["risk"] == "HIGH" else "🟡" if data["risk"] == "MEDIUM" else "🟢"
        print(f"  {emoji} {name}: {data['risk']} (score {data['score']})")
        for s in data["signals"][:2]:
            print(f"     → {s}")
    print(f"\n  💾 Data: {json_path}")
    print(f"  📄 Report: {md_path}")
    print(f"{'═'*60}\n")

    return report


def generate_report(report):
    """Generate premium markdown report."""
    date = report["scan_date"][:10]
    days = report["period_days"]
    reddit = report["reddit"]
    ranked = report["ranked"]

    L = []
    L.append(f"# Terpene Market Competitive Intelligence Report")
    L.append(f"**Week of {date}** | {days}-day lookback | Nexus BDR Intelligence Engine v2\n")
    L.append(f"---\n")

    # Executive Summary
    L.append(f"## Executive Summary\n")
    L.append(f"Scanned {len(REDDIT_SUBS)} subreddits, Trustpilot reviews, competitor websites, and industry news.\n")
    L.append(f"| Metric | Count |")
    L.append(f"|--------|-------|")
    L.append(f"| Reddit signals detected | **{reddit['total_signals']}** |")
    L.append(f"| Supplier-seeking posts | **{reddit['supplier_seeking']}** |")
    L.append(f"| Quality complaints | **{reddit['complaints']}** |")
    L.append(f"| CDT vs BDT discussions | **{reddit['comparisons']}** |")
    L.append(f"| Posts naming competitors | **{reddit['with_competitor_mention']}** |")
    L.append(f"| Industry news articles | **{len(report.get('news', []))}** |\n")

    # Competitor ranking
    L.append(f"## Competitor Vulnerability Ranking\n")
    L.append(f"| Rank | Competitor | Trustpilot | Hiring | Vuln Score | Risk |")
    L.append(f"|------|-----------|------------|--------|------------|------|")
    for i, (name, data) in enumerate(ranked, 1):
        tp = data.get("trustpilot", {})
        tp_str = f"{tp['rating']}/5 ({tp.get('count','?')})" if tp.get("rating") else "—"
        hiring = "Yes ⚠️" if data["hiring"] else "No"
        L.append(f"| {i} | **{name}** | {tp_str} | {hiring} | {data['score']} | {data['risk']} |")
    L.append("")

    # Per-competitor detail
    for name, data in ranked:
        info = COMPETITORS.get(name, {})
        L.append(f"---\n")
        L.append(f"### {name}\n")
        L.append(f"**Position:** {info.get('market_position', '?')}")
        L.append(f"**Botanical:** {info.get('pricing_botanical', '?')} | **CDT:** {info.get('pricing_cdt', 'N/A')}")
        L.append(f"**Risk Level:** {data['risk']} (score: {data['score']})\n")

        if data["signals"]:
            L.append(f"**Active Vulnerabilities:**")
            for s in data["signals"]:
                L.append(f"- {s}")
            L.append("")

        L.append(f"**Known Weaknesses:** {', '.join(info.get('known_weaknesses', []))}\n")
        L.append(f"**TBF displacement:** {info.get('tbf_angle', '—')}")
        L.append(f"**DFT displacement:** {info.get('dft_angle', '—')}\n")

    # Top Reddit signals
    top = reddit.get("top_actionable", [])
    if top:
        L.append(f"---\n")
        L.append(f"## Top Actionable Reddit Signals\n")
        L.append(f"*Posts where prospects are actively seeking suppliers or complaining about existing ones*\n")

        for i, p in enumerate(top[:15], 1):
            intent = "🔴" if p["intent_score"] >= 40 else "🟡" if p["intent_score"] >= 20 else "🔵"
            L.append(f"**{i}. [{p['title'][:90]}]({p['url']})** {intent}")
            L.append(f"r/{p['subreddit']} | Score: {p['score']} | {p['comments']} comments | Intent: {p['intent_score']}")

            tags = []
            if p["is_supplier_seeking"]:
                tags.append("SEEKING SUPPLIER")
            if p["is_complaint"]:
                tags.append("COMPLAINT")
            if p["is_comparison"]:
                tags.append("COMPARING")
            if p["competitors_mentioned"]:
                tags.append(f"MENTIONS: {', '.join(p['competitors_mentioned'])}")
            if tags:
                L.append(f"*{' | '.join(tags)}*")

            if p.get("body"):
                preview = p["body"][:200].replace("\n", " ")
                L.append(f"> {preview}...")
            L.append("")

    # Pricing matrix
    L.append(f"---\n")
    L.append(f"## Competitive Pricing Matrix\n")
    L.append(f"| Supplier | Botanical/L | CDT/L | Weakness |")
    L.append(f"|----------|-----------|-------|----------|")
    L.append(f"| **TBF (ours)** | Enterprise pricing | N/A (cannabis oils) | — |")
    L.append(f"| **DFT (ours)** | $45-80 | N/A | — |")
    for name, info in COMPETITORS.items():
        weakness = info.get("known_weaknesses", ["—"])[0]
        L.append(f"| {name} | {info['pricing_botanical']} | {info['pricing_cdt']} | {weakness} |")
    L.append("")

    # Action items
    seeking = [p for p in reddit.get("posts", []) if p["is_supplier_seeking"]]
    L.append(f"---\n")
    L.append(f"## This Week's Action Items\n")
    if seeking:
        L.append(f"### {len(seeking)} Prospects Seeking Suppliers\n")
        for i, p in enumerate(seeking[:10], 1):
            L.append(f"{i}. **r/{p['subreddit']}**: [{p['title'][:70]}]({p['url']}) — engage with DFT/TBF positioning")
    else:
        L.append(f"No active supplier-seeking posts this period. Expand to 60-day lookback or try --days 60.")

    L.append(f"\n---")
    L.append(f"\n*Generated by Nexus Competitor Vulnerability Engine v2 | Category-based intelligence | Zero API cost*")

    md = "\n".join(L)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    path = VULN_DIR / f"competitor_report_v2_{ts}.md"
    with open(path, "w") as f:
        f.write(md)

    return path


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Competitor Vulnerability Engine v2")
    parser.add_argument("--scan", action="store_true", help="Full competitive intelligence scan")
    parser.add_argument("--days", type=int, default=30, help="Lookback period")
    args = parser.parse_args()

    if args.scan:
        full_scan(days_back=args.days)
    else:
        parser.print_help()
        print(f"\n  Try: python3 competitor_vuln_v2.py --scan --days 30")


if __name__ == "__main__":
    main()
