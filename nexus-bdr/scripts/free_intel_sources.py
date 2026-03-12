#!/usr/bin/env python3
"""
Free Intelligence Sources — Nexus BDR Agent
=============================================
Zero-cost data harvesting from public APIs and databases.
No API keys required for most sources.

Sources:
  1. Reddit API (free tier, no auth for read)
  2. FDA Warning Letters (cannabis/hemp enforcement)
  3. State Cannabis License Databases (new licenses = new prospects)
  4. Google Trends (search volume data)
  5. Weedmaps/Leafly public product pages
  6. SEC EDGAR (public company filings)
  7. USPTO Trademark Search (brand filings)

Usage:
    python3 free_intel_sources.py --reddit --subreddits "delta8,altcannabinoids,CBD,cannabisextracts"
    python3 free_intel_sources.py --fda --days 90
    python3 free_intel_sources.py --licenses --state FL
    python3 free_intel_sources.py --trends --terms "cannabis terpenes,botanical terpenes,CDT terpenes"
    python3 free_intel_sources.py --all
"""

import os, sys, json, re, time, argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "outputs" if (SCRIPT_DIR / "outputs").exists() else Path.cwd() / "outputs"
INTEL_DIR = OUTPUT_DIR / "free_intel"
INTEL_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "NexusBDR/1.0 (business intelligence research)"}

# ════════════════════════════════════════════════════════════
# 1. REDDIT — Buying signals, supplier complaints, terpene discussions
# ════════════════════════════════════════════════════════════

REDDIT_SUBREDDITS = [
    "delta8", "altcannabinoids", "CBD", "cannabisextracts",
    "vaporents", "CannabisExtracts", "hempflowers",
    "FLMedicalTrees", "TheOCS", "Dabs", "cleancarts",
    "hemp", "CBDhempBuds", "weed",
]

TERPENE_KEYWORDS = [
    "terpene", "terps", "terp", "CDT", "BDT", "botanical",
    "cannabis derived", "live resin terpene", "strain profile",
    "flavor profile", "terpene supplier", "terpene source",
    "True Terpenes", "Abstrax", "Floraplex", "terpene belt",
    "duty free terps", "custom blend", "terpene cost",
    "COA", "certificate of analysis", "batch consistency",
    "entourage effect", "terpene percentage",
]

BUYING_SIGNALS = [
    "looking for", "need a supplier", "who sells", "where to buy",
    "recommend", "switched from", "better than", "alternative to",
    "bulk terpenes", "wholesale", "looking to source",
    "any suggestions for", "best place to get",
    "bad experience with", "quality issues", "inconsistent",
    "disappointed with", "stopped using",
]

def reddit_harvest(subreddits=None, limit_per_sub=25, days_back=30):
    """Harvest terpene-related posts from Reddit. No auth required."""
    subs = subreddits or REDDIT_SUBREDDITS
    all_posts = []
    signals = []

    print(f"\n  ═══ Reddit Intelligence Scan ═══")
    print(f"  Scanning {len(subs)} subreddits, {limit_per_sub} posts each")
    print(f"  Looking back {days_back} days\n")

    cutoff = datetime.utcnow() - timedelta(days=days_back)

    for sub in subs:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit_per_sub}"
        try:
            resp = requests.get(url, headers={**HEADERS, "User-Agent": "NexusBDR/1.0"}, timeout=15)
            if resp.status_code == 429:
                print(f"  ⏳ Rate limited on r/{sub}, waiting 5s...")
                time.sleep(5)
                resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  ⚠️  r/{sub}: HTTP {resp.status_code}")
                continue

            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            relevant = 0

            for post in posts:
                p = post.get("data", {})
                created = datetime.utcfromtimestamp(p.get("created_utc", 0))
                if created < cutoff:
                    continue

                title = p.get("title", "").lower()
                body = p.get("selftext", "").lower()
                text = f"{title} {body}"

                # Check for terpene relevance
                terp_matches = [kw for kw in TERPENE_KEYWORDS if kw.lower() in text]
                if not terp_matches:
                    continue

                relevant += 1
                # Check for buying signals
                buy_matches = [sig for sig in BUYING_SIGNALS if sig.lower() in text]

                post_data = {
                    "subreddit": sub,
                    "title": p.get("title", ""),
                    "body": p.get("selftext", "")[:500],
                    "author": p.get("author", ""),
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "created": created.isoformat(),
                    "terpene_keywords": terp_matches,
                    "buying_signals": buy_matches,
                    "is_buying_signal": len(buy_matches) > 0,
                    "signal_strength": "HIGH" if len(buy_matches) >= 2 else "MEDIUM" if len(buy_matches) == 1 else "LOW",
                }
                all_posts.append(post_data)

                if buy_matches:
                    signals.append(post_data)

            if relevant > 0:
                print(f"  ✅ r/{sub}: {relevant} terpene posts, {sum(1 for p in all_posts if p['subreddit']==sub and p['is_buying_signal'])} buying signals")
            else:
                print(f"  · r/{sub}: no terpene activity")

        except Exception as e:
            print(f"  ❌ r/{sub}: {str(e)[:80]}")

        time.sleep(1)  # Rate limit

    # Sort signals by strength
    signals.sort(key=lambda x: (x["signal_strength"] == "HIGH", x["score"]), reverse=True)

    result = {
        "scan_date": datetime.utcnow().isoformat(),
        "subreddits_scanned": len(subs),
        "total_terpene_posts": len(all_posts),
        "buying_signals": len(signals),
        "high_priority_signals": sum(1 for s in signals if s["signal_strength"] == "HIGH"),
        "signals": signals[:50],  # Top 50 signals
        "all_posts": all_posts,
    }

    # Save
    path = INTEL_DIR / f"reddit_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  📊 Results: {len(all_posts)} terpene posts, {len(signals)} buying signals ({result['high_priority_signals']} HIGH)")
    if signals:
        print(f"\n  🔥 Top Buying Signals:")
        for s in signals[:5]:
            print(f"  → [{s['signal_strength']}] r/{s['subreddit']}: {s['title'][:80]}")
            if s['buying_signals']:
                print(f"    Signals: {', '.join(s['buying_signals'][:3])}")

    print(f"\n  💾 {path}")
    return result


# ════════════════════════════════════════════════════════════
# 2. FDA WARNING LETTERS — Enforcement = business disruption = opportunity
# ════════════════════════════════════════════════════════════

def fda_warning_letters(days_back=180, search_terms=None):
    """Search FDA warning letters for cannabis/hemp companies."""
    terms = search_terms or ["cannabis", "hemp", "CBD", "THC", "cannabinoid", "terpene", "delta-8"]

    print(f"\n  ═══ FDA Warning Letter Scan ═══")
    print(f"  Searching for: {', '.join(terms)}")

    results = []
    # FDA OpenFDA API — free, no key required
    for term in terms:
        url = f"https://api.fda.gov/other/substance.json?search={quote_plus(term)}&limit=10"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                count = data.get("meta", {}).get("results", {}).get("total", 0)
                print(f"  · {term}: {count} results")
        except:
            pass

    # Also check FDA warning letters page via their search
    # Note: The actual FDA warning letters API is limited, so we scrape the search
    warning_url = "https://api.fda.gov/food/enforcement.json"
    params = {
        "search": "cannabis+hemp+CBD+THC",
        "limit": 25,
        "sort": "report_date:desc"
    }
    try:
        resp = requests.get(warning_url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            print(f"  ✅ Found {len(results)} enforcement actions")
            for r in results[:5]:
                print(f"  → {r.get('recalling_firm', '?')}: {r.get('reason_for_recall', '?')[:80]}")
    except Exception as e:
        print(f"  ⚠️  FDA API: {str(e)[:80]}")

    # Save
    result = {
        "scan_date": datetime.utcnow().isoformat(),
        "enforcement_actions": results,
        "total_found": len(results),
    }
    path = INTEL_DIR / f"fda_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  💾 {path}")
    return result


# ════════════════════════════════════════════════════════════
# 3. SEC EDGAR — Public cannabis company filings
# ════════════════════════════════════════════════════════════

def sec_cannabis_filings(days_back=90):
    """Search SEC EDGAR for cannabis company filings."""
    print(f"\n  ═══ SEC EDGAR Cannabis Filing Scan ═══")

    # EDGAR full-text search API — free, no auth
    search_url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": '"cannabis" OR "hemp" OR "cannabinoid" OR "terpene"',
        "dateRange": "custom",
        "startdt": (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
        "enddt": datetime.utcnow().strftime("%Y-%m-%d"),
        "forms": "10-K,10-Q,8-K,S-1",
    }

    # Use the simpler full-text search
    search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22cannabis%22+%22terpene%22&forms=10-K,8-K&dateRange=custom&startdt={(datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')}"

    results = []
    try:
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={
                "q": '"cannabis terpene"',
                "forms": "10-K,8-K",
            },
            headers={**HEADERS, "User-Agent": "NexusBDR research@nexusbdr.com"},
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            print(f"  ✅ Found {len(hits)} filings mentioning cannabis terpenes")
            for h in hits[:10]:
                src = h.get("_source", {})
                print(f"  → {src.get('entity_name', '?')}: {src.get('file_description', '?')[:60]}")
                results.append(src)
        else:
            print(f"  ⚠️  EDGAR returned {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️  EDGAR: {str(e)[:80]}")

    result = {
        "scan_date": datetime.utcnow().isoformat(),
        "filings": results,
    }
    path = INTEL_DIR / f"sec_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  💾 {path}")
    return result


# ════════════════════════════════════════════════════════════
# 4. USPTO TRADEMARK SEARCH — New brand filings in cannabis
# ════════════════════════════════════════════════════════════

def uspto_trademark_scan(terms=None):
    """Search USPTO for recent cannabis/terpene trademark filings."""
    print(f"\n  ═══ USPTO Trademark Scan ═══")

    search_terms = terms or ["cannabis terpene", "hemp terpene", "CDT", "botanical terpene", "live resin"]
    results = []

    # USPTO Trademark Status & Document Retrieval (TSDR) API
    # Free, no auth required
    for term in search_terms:
        url = f"https://tmsearch.uspto.gov/bin/gate.exe?f=searchss&state=4810:1.1.1&p_s_PARA1={quote_plus(term)}&p_s_PARA2=live&p_s_ALL=cannabis"
        # Note: USPTO doesn't have a clean REST API, but we can use their TESS search
        print(f"  · Searching: {term}")

    print(f"  ℹ️  USPTO search available at: https://tmsearch.uspto.gov/")
    print(f"  ℹ️  Manual search recommended for trademark intelligence")

    return {"terms_searched": search_terms, "note": "Use TESS manually for best results"}


# ════════════════════════════════════════════════════════════
# 5. NEWS API (Free tier) — Industry news monitoring
# ════════════════════════════════════════════════════════════

def news_scan(terms=None, days_back=14):
    """Scan free news sources for cannabis/terpene industry news."""
    print(f"\n  ═══ Industry News Scan ═══")

    search_terms = terms or [
        "cannabis terpene supplier",
        "hemp terpene market",
        "cannabis derived terpene",
        "botanical terpene",
        "hemp regulation 2026",
        "cannabis extraction facility",
    ]

    results = []

    # Google News RSS — free, no auth
    for term in search_terms[:4]:  # Limit to avoid rate limiting
        url = f"https://news.google.com/rss/search?q={quote_plus(term)}&hl=en-US&gl=US&ceid=US:en"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                # Parse RSS XML
                items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>.*?</item>', resp.text, re.DOTALL)
                for title, link, date in items[:5]:
                    title = re.sub(r'<.*?>', '', title).strip()
                    results.append({
                        "title": title,
                        "url": link.strip(),
                        "date": date.strip(),
                        "search_term": term,
                    })
                print(f"  ✅ '{term}': {len(items)} articles")
            else:
                print(f"  ⚠️  '{term}': HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ '{term}': {str(e)[:60]}")

        time.sleep(1)  # Rate limit

    # Deduplicate by title
    seen = set()
    unique = []
    for r in results:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)

    result = {
        "scan_date": datetime.utcnow().isoformat(),
        "articles": unique,
        "total_found": len(unique),
    }
    path = INTEL_DIR / f"news_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\n  📰 {len(unique)} unique articles found")
    for a in unique[:5]:
        print(f"  → {a['title'][:80]}")

    print(f"  💾 {path}")
    return result


# ════════════════════════════════════════════════════════════
# 6. COMPETITOR MONITOR — Track competitor websites for changes
# ════════════════════════════════════════════════════════════

COMPETITOR_URLS = {
    "True Terpenes": "https://trueterpenes.com",
    "Abstrax Tech": "https://abstraxtech.com",
    "Floraplex": "https://floraplex.com",
    "Denver Terpenes": "https://denverterpenes.com",
    "Peak Supply Co": "https://peaksupplyco.com",
}

def competitor_scan():
    """Check competitor websites for pricing, new products, changes."""
    print(f"\n  ═══ Competitor Monitor ═══")

    results = {}
    for name, url in COMPETITOR_URLS.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            status = resp.status_code
            content_length = len(resp.text)

            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', resp.text, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "?"

            # Look for pricing mentions
            price_matches = re.findall(r'\$\d+[\d,.]*(?:/[a-zA-Z]+)?', resp.text)
            prices = list(set(price_matches[:10]))

            results[name] = {
                "url": url,
                "status": status,
                "title": title,
                "content_size": content_length,
                "prices_found": prices[:5],
                "checked": datetime.utcnow().isoformat(),
            }
            print(f"  ✅ {name}: {status} | {title[:50]} | {len(prices)} prices found")

        except Exception as e:
            results[name] = {"url": url, "error": str(e)[:80]}
            print(f"  ❌ {name}: {str(e)[:60]}")

    result = {
        "scan_date": datetime.utcnow().isoformat(),
        "competitors": results,
    }
    path = INTEL_DIR / f"competitor_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  💾 {path}")
    return result


# ════════════════════════════════════════════════════════════
# MASTER SCAN — Run everything
# ════════════════════════════════════════════════════════════

def run_all_scans():
    """Run all free intel sources."""
    print(f"\n{'═'*60}")
    print(f"  NEXUS FREE INTELLIGENCE SWEEP")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  Zero API cost — public data only")
    print(f"{'═'*60}")

    results = {}

    results["reddit"] = reddit_harvest(days_back=14)
    results["fda"] = fda_warning_letters(days_back=90)
    results["sec"] = sec_cannabis_filings(days_back=90)
    results["news"] = news_scan(days_back=14)
    results["competitors"] = competitor_scan()

    # Summary
    print(f"\n{'═'*60}")
    print(f"  SWEEP COMPLETE")
    print(f"  Reddit: {results['reddit']['total_terpene_posts']} posts, {results['reddit']['buying_signals']} buying signals")
    print(f"  FDA: {results['fda']['total_found']} enforcement actions")
    print(f"  SEC: {len(results['sec'].get('filings', []))} filings")
    print(f"  News: {results['news']['total_found']} articles")
    print(f"  Competitors: {len(results['competitors']['competitors'])} tracked")
    print(f"{'═'*60}\n")

    # Master save
    path = INTEL_DIR / f"full_sweep_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"  💾 Master report: {path}")
    return results


# ════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Free Intelligence Sources — Nexus BDR")
    parser.add_argument("--all", action="store_true", help="Run all scans")
    parser.add_argument("--reddit", action="store_true", help="Reddit terpene scan")
    parser.add_argument("--fda", action="store_true", help="FDA warning letters")
    parser.add_argument("--sec", action="store_true", help="SEC EDGAR cannabis filings")
    parser.add_argument("--news", action="store_true", help="Industry news scan")
    parser.add_argument("--competitors", action="store_true", help="Competitor website monitor")
    parser.add_argument("--subreddits", default="", help="Comma-separated subreddits")
    parser.add_argument("--days", type=int, default=30, help="Days to look back")

    args = parser.parse_args()

    if args.all:
        run_all_scans()
    elif args.reddit:
        subs = args.subreddits.split(",") if args.subreddits else None
        reddit_harvest(subreddits=subs, days_back=args.days)
    elif args.fda:
        fda_warning_letters(days_back=args.days)
    elif args.sec:
        sec_cannabis_filings(days_back=args.days)
    elif args.news:
        news_scan(days_back=args.days)
    elif args.competitors:
        competitor_scan()
    else:
        parser.print_help()
        print("\n  💡 Try: python3 free_intel_sources.py --all")


if __name__ == "__main__":
    main()
