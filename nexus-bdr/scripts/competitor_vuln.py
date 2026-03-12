#!/usr/bin/env python3
"""
Competitor Vulnerability Engine — Nexus BDR Agent
===================================================
Monitors TBF/DFT competitors across every public channel.
Surfaces unhappy customers, quality complaints, pricing frustrations,
and switching signals. Generates actionable weekly reports.

THIS IS THE MONEY TOOL. Every vulnerability = a prospect.

Competitors Tracked:
  True Terpenes    — Market leader, premium, slow
  Abstrax Tech     — Science-focused, expensive, complex
  Floraplex        — Budget, inconsistent quality
  Denver Terpenes  — Regional, limited scale
  Peak Supply Co   — DTC, limited B2B
  Terps USA        — Budget alternative
  Extract Consultants — Formulation focused

Sources:
  1. Reddit (14 subreddits, real-time)
  2. Google News (industry coverage)
  3. Trustpilot / review sites
  4. Forums (Future4200, ICMag, Grasscity)
  5. Job postings (hiring = scaling problems or pivots)
  6. Social media mentions

Usage:
    python3 competitor_vuln.py --scan              # Full scan all competitors
    python3 competitor_vuln.py --competitor "True Terpenes"
    python3 competitor_vuln.py --report             # Generate weekly report
    python3 competitor_vuln.py --report --format md  # Markdown report

Zero API cost — runs entirely on public data.
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

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# ═══════════════════════════════════════════════════════════
# COMPETITOR DATABASE
# ═══════════════════════════════════════════════════════════

COMPETITORS = {
    "True Terpenes": {
        "domain": "trueterpenes.com",
        "reddit_terms": ["true terpenes", "trueterpenes", "true terps"],
        "pricing_botanical": "$80-150/L",
        "pricing_cdt": "$2,000-4,000/L",
        "known_weaknesses": ["slow custom orders (4-6 weeks)", "quality complaints on recent batches", "corporate feel", "price increases 2024-2025"],
        "market_position": "Market leader, premium botanical + CDT",
        "tbf_angle": "TBF offers faster custom turnaround, better batch consistency, competitive pricing at scale",
        "dft_angle": "DFT offers hype strains True Terpenes doesn't carry, faster shipping, no minimum BS",
    },
    "Abstrax Tech": {
        "domain": "abstraxtech.com",
        "reddit_terms": ["abstrax", "abstrax tech", "abstraxtech"],
        "pricing_botanical": "$120-200/L",
        "pricing_cdt": "$3,000-6,000/L",
        "known_weaknesses": ["expensive", "complex ordering process", "slow response times", "overengineered for small operators"],
        "market_position": "Science/R&D focused, premium CDT",
        "tbf_angle": "TBF matches scientific rigor with simpler ordering and faster turnaround at better prices",
        "dft_angle": "DFT is for operators who want great terps without the PhD-level ordering process",
    },
    "Floraplex": {
        "domain": "floraplex.com",
        "reddit_terms": ["floraplex", "flora plex"],
        "pricing_botanical": "$40-80/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["inconsistent quality", "synthetic undertones", "batch variation", "no custom blending", "poor customer service"],
        "market_position": "Budget botanical, 200+ strains",
        "tbf_angle": "TBF delivers consistency Floraplex can't at competitive volume pricing",
        "dft_angle": "DFT offers authentic strain profiles without the synthetic aftertaste at comparable pricing",
    },
    "Denver Terpenes": {
        "domain": "denverterpenes.com",
        "reddit_terms": ["denver terpenes", "denverterpenes"],
        "pricing_botanical": "$60-120/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["limited strain selection", "can't scale", "regional only", "small team"],
        "market_position": "Regional CO supplier",
        "tbf_angle": "TBF offers national scale and consistency Denver can't match",
        "dft_angle": "DFT has 3x the strain library with exotic/hype profiles Denver doesn't offer",
    },
    "Peak Supply Co": {
        "domain": "peaksupplyco.com",
        "reddit_terms": ["peak supply", "peaksupplyco", "peak supply co"],
        "pricing_botanical": "$50-90/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["limited B2B infrastructure", "DTC focused", "inconsistent availability"],
        "market_position": "DTC terpene supplier",
        "tbf_angle": "TBF offers real B2B infrastructure, dedicated account management, volume pricing",
        "dft_angle": "DFT offers better hype strain accuracy and craft-level attention Peak can't provide",
    },
    "Terps USA": {
        "domain": "terpsusa.com",
        "reddit_terms": ["terps usa", "terpsusa"],
        "pricing_botanical": "$35-70/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["bottom-tier quality", "synthetic", "no COAs", "unreliable shipping"],
        "market_position": "Budget/discount",
        "tbf_angle": "TBF provides actual cannabis-origin quality at enterprise pricing",
        "dft_angle": "DFT delivers real strain profiles at only slight premium over synthetic garbage",
    },
    "Extract Consultants": {
        "domain": "extractconsultants.com",
        "reddit_terms": ["extract consultants"],
        "pricing_botanical": "$70-120/L",
        "pricing_cdt": "N/A",
        "known_weaknesses": ["formulation focused, not production", "limited strain library", "slow innovation"],
        "market_position": "Formulation consulting + terpenes",
        "tbf_angle": "TBF offers comparable formulation support with actual production scale",
        "dft_angle": "DFT offers fresher, trendier profiles that Extract Consultants' catalog can't match",
    },
}

REDDIT_SUBS = [
    "delta8", "altcannabinoids", "CBD", "cannabisextracts",
    "CannabisExtracts", "vaporents", "hempflowers", "cleancarts",
    "Dabs", "FLMedicalTrees", "hemp", "concentrates",
    "DIY_eJuice", "oilpen",
]

# Sentiment signals
NEGATIVE_SIGNALS = [
    "disappointed", "terrible", "awful", "worst", "horrible", "trash",
    "never again", "switched from", "stopped using", "used to use",
    "quality dropped", "not what it used to be", "went downhill",
    "inconsistent", "batch variation", "different every time",
    "synthetic", "chemical taste", "artificial", "off taste",
    "overpriced", "too expensive", "not worth", "rip off",
    "slow shipping", "took forever", "still waiting", "no response",
    "bad customer service", "won't respond", "ghosted",
    "would not recommend", "stay away", "don't buy", "avoid",
    "looking for alternative", "better option", "switched to",
    "anyone else have problems", "am I the only one",
]

POSITIVE_COMPETITOR_SIGNALS = [
    "love", "amazing", "best", "recommend", "switched to",
    "way better than", "so much better", "finally found",
]

SWITCHING_SIGNALS = [
    "looking for alternative", "need new supplier", "switching from",
    "anyone recommend", "better than", "replacement for",
    "tired of", "fed up with", "done with",
    "who else sells", "where else can I get", "other options",
]

# ═══════════════════════════════════════════════════════════
# REDDIT COMPETITOR SCAN
# ═══════════════════════════════════════════════════════════

def scan_reddit_competitor(competitor_name, search_terms, days_back=30):
    """Scan Reddit for mentions of a specific competitor."""
    mentions = []
    vulnerabilities = []
    positive = []

    for sub in REDDIT_SUBS:
        for term in search_terms:
            url = f"https://www.reddit.com/r/{sub}/search.json?q={quote_plus(term)}&restrict_sr=1&sort=new&limit=25&t=month"
            try:
                resp = requests.get(url, headers={**HEADERS, "User-Agent": f"NexusBDR/1.0 (competitor research)"}, timeout=15)
                if resp.status_code == 429:
                    time.sleep(3)
                    continue
                if resp.status_code != 200:
                    continue

                posts = resp.json().get("data", {}).get("children", [])
                cutoff = datetime.utcnow() - timedelta(days=days_back)

                for post in posts:
                    p = post.get("data", {})
                    created = datetime.utcfromtimestamp(p.get("created_utc", 0))
                    if created < cutoff:
                        continue

                    title = p.get("title", "")
                    body = p.get("selftext", "")
                    text = f"{title} {body}".lower()
                    url_link = f"https://reddit.com{p.get('permalink', '')}"

                    # Check for negative sentiment
                    neg_matches = [s for s in NEGATIVE_SIGNALS if s in text]
                    switch_matches = [s for s in SWITCHING_SIGNALS if s in text]
                    pos_matches = [s for s in POSITIVE_COMPETITOR_SIGNALS if s in text]

                    mention = {
                        "subreddit": sub,
                        "title": p.get("title", ""),
                        "body": p.get("selftext", "")[:600],
                        "author": p.get("author", ""),
                        "score": p.get("score", 0),
                        "comments": p.get("num_comments", 0),
                        "url": url_link,
                        "created": created.isoformat(),
                        "negative_signals": neg_matches,
                        "switching_signals": switch_matches,
                        "positive_signals": pos_matches,
                        "sentiment": "NEGATIVE" if len(neg_matches) >= 2 else "SWITCHING" if switch_matches else "NEGATIVE" if neg_matches else "POSITIVE" if pos_matches else "NEUTRAL",
                    }

                    mentions.append(mention)

                    if neg_matches or switch_matches:
                        mention["vulnerability_score"] = len(neg_matches) * 2 + len(switch_matches) * 3
                        vulnerabilities.append(mention)
                    elif pos_matches:
                        positive.append(mention)

            except Exception as e:
                continue

            time.sleep(0.5)  # Rate limit between searches

    # Deduplicate by URL
    seen = set()
    unique_vulns = []
    for v in sorted(vulnerabilities, key=lambda x: x.get("vulnerability_score", 0), reverse=True):
        if v["url"] not in seen:
            seen.add(v["url"])
            unique_vulns.append(v)

    unique_mentions = []
    seen2 = set()
    for m in mentions:
        if m["url"] not in seen2:
            seen2.add(m["url"])
            unique_mentions.append(m)

    return {
        "total_mentions": len(unique_mentions),
        "vulnerabilities": unique_vulns,
        "positive_mentions": positive,
        "vulnerability_count": len(unique_vulns),
    }


# ═══════════════════════════════════════════════════════════
# GOOGLE NEWS SCAN
# ═══════════════════════════════════════════════════════════

def scan_news_competitor(competitor_name, days_back=30):
    """Scan Google News for competitor mentions."""
    results = []
    queries = [
        f'"{competitor_name}" terpene',
        f'"{competitor_name}" complaint OR recall OR warning',
        f'"{competitor_name}" review',
    ]

    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>.*?</item>', resp.text, re.DOTALL)
                for title, link, date in items[:5]:
                    title = re.sub(r'<.*?>', '', title).strip()
                    results.append({"title": title, "url": link.strip(), "date": date.strip(), "query": q})
        except:
            pass
        time.sleep(1)

    # Deduplicate
    seen = set()
    unique = []
    for r in results:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)

    return unique


# ═══════════════════════════════════════════════════════════
# REVIEW SITE SCAN
# ═══════════════════════════════════════════════════════════

def scan_reviews_competitor(competitor_name, domain):
    """Check Trustpilot and other review sites."""
    results = {"trustpilot": None, "bbb": None}

    # Trustpilot
    slug = domain.replace(".com", "").replace("www.", "")
    tp_url = f"https://www.trustpilot.com/review/{domain}"
    try:
        resp = requests.get(tp_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            # Extract rating
            rating_match = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)"?', resp.text)
            review_count_match = re.search(r'"reviewCount"\s*:\s*"?(\d+)"?', resp.text)
            rating = float(rating_match.group(1)) if rating_match else None
            count = int(review_count_match.group(1)) if review_count_match else None
            results["trustpilot"] = {"rating": rating, "review_count": count, "url": tp_url}
    except:
        pass

    return results


# ═══════════════════════════════════════════════════════════
# WEBSITE CHANGE DETECTION
# ═══════════════════════════════════════════════════════════

def scan_website_competitor(competitor_name, domain):
    """Check competitor website for pricing, product changes, hiring."""
    result = {"status": None, "prices": [], "hiring": False, "new_products": []}

    try:
        resp = requests.get(f"https://{domain}", headers=HEADERS, timeout=10)
        result["status"] = resp.status_code
        if resp.status_code == 200:
            text = resp.text.lower()
            # Find prices
            prices = re.findall(r'\$\d+[\d,.]*(?:\s*/\s*[a-zA-Z]+)?', resp.text)
            result["prices"] = list(set(prices))[:15]
            # Check for hiring signals
            result["hiring"] = any(w in text for w in ["careers", "hiring", "job opening", "join our team", "we're hiring"])
            # Check for new product signals
            result["new_products_signals"] = any(w in text for w in ["new", "just launched", "introducing", "now available"])
    except Exception as e:
        result["error"] = str(e)[:80]

    # Check careers page
    for path in ["/careers", "/jobs", "/about/careers", "/pages/careers"]:
        try:
            resp = requests.get(f"https://{domain}{path}", headers=HEADERS, timeout=8)
            if resp.status_code == 200 and ("position" in resp.text.lower() or "apply" in resp.text.lower()):
                result["hiring"] = True
                result["careers_url"] = f"https://{domain}{path}"
                break
        except:
            continue

    return result


# ═══════════════════════════════════════════════════════════
# FULL COMPETITOR SCAN
# ═══════════════════════════════════════════════════════════

def full_scan(days_back=30, target_competitor=None):
    """Run full vulnerability scan across all competitors."""
    print(f"\n{'═'*60}")
    print(f"  COMPETITOR VULNERABILITY ENGINE")
    print(f"  Scanning {len(COMPETITORS) if not target_competitor else 1} competitors")
    print(f"  Lookback: {days_back} days")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═'*60}\n")

    targets = {target_competitor: COMPETITORS[target_competitor]} if target_competitor else COMPETITORS
    all_results = {}
    total_vulns = 0

    for name, info in targets.items():
        print(f"  ┌─ {name}")
        print(f"  │  {info['market_position']}")

        result = {
            "competitor": name,
            "info": info,
            "reddit": {},
            "news": [],
            "reviews": {},
            "website": {},
            "vulnerability_summary": {},
        }

        # Reddit scan
        print(f"  │  Scanning Reddit...")
        reddit = scan_reddit_competitor(name, info["reddit_terms"], days_back)
        result["reddit"] = reddit
        print(f"  │  Reddit: {reddit['total_mentions']} mentions, {reddit['vulnerability_count']} vulnerabilities")

        # News scan
        print(f"  │  Scanning news...")
        news = scan_news_competitor(name, days_back)
        result["news"] = news
        print(f"  │  News: {len(news)} articles")

        # Review sites
        print(f"  │  Checking reviews...")
        reviews = scan_reviews_competitor(name, info["domain"])
        result["reviews"] = reviews
        tp = reviews.get("trustpilot", {})
        if tp and tp.get("rating"):
            print(f"  │  Trustpilot: {tp['rating']}/5 ({tp.get('review_count', '?')} reviews)")

        # Website
        print(f"  │  Checking website...")
        website = scan_website_competitor(name, info["domain"])
        result["website"] = website
        hiring_status = "HIRING" if website.get("hiring") else "No hiring signals"
        print(f"  │  Website: {website.get('status', '?')} | {hiring_status} | {len(website.get('prices', []))} prices found")

        # Vulnerability summary
        vuln_score = reddit["vulnerability_count"] * 3
        if tp and tp.get("rating") and tp["rating"] < 4.0:
            vuln_score += int((4.0 - tp["rating"]) * 10)
        if website.get("hiring"):
            vuln_score += 5  # Hiring = potential instability

        result["vulnerability_summary"] = {
            "vulnerability_score": vuln_score,
            "risk_level": "HIGH" if vuln_score >= 15 else "MEDIUM" if vuln_score >= 8 else "LOW",
            "top_vulnerabilities": [v["title"][:80] for v in reddit["vulnerabilities"][:5]],
            "displacement_opportunity": info["tbf_angle"],
            "dft_angle": info["dft_angle"],
            "actionable_leads": len([v for v in reddit["vulnerabilities"] if v.get("switching_signals")]),
        }

        total_vulns += reddit["vulnerability_count"]
        level = result["vulnerability_summary"]["risk_level"]
        print(f"  │  Vulnerability: {level} (score: {vuln_score})")
        print(f"  └─ ✅ Complete\n")

        all_results[name] = result
        time.sleep(2)  # Rate limit between competitors

    # ═══ GENERATE REPORT ═══
    report = {
        "scan_date": datetime.utcnow().isoformat(),
        "period_days": days_back,
        "competitors_scanned": len(all_results),
        "total_vulnerabilities": total_vulns,
        "total_actionable_leads": sum(r["vulnerability_summary"]["actionable_leads"] for r in all_results.values()),
        "competitors": all_results,
        "ranked_by_vulnerability": sorted(
            [(name, r["vulnerability_summary"]["vulnerability_score"]) for name, r in all_results.items()],
            key=lambda x: x[1], reverse=True
        ),
    }

    # Save JSON
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    json_path = VULN_DIR / f"competitor_vuln_{ts}.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print(f"{'═'*60}")
    print(f"  VULNERABILITY SUMMARY")
    print(f"  Total vulnerabilities found: {total_vulns}")
    print(f"  Actionable switching leads: {report['total_actionable_leads']}")
    print(f"\n  RANKED BY VULNERABILITY:")
    for name, score in report["ranked_by_vulnerability"]:
        level = all_results[name]["vulnerability_summary"]["risk_level"]
        emoji = "🔴" if level == "HIGH" else "🟡" if level == "MEDIUM" else "🟢"
        print(f"  {emoji} {name}: {level} (score: {score})")
        vulns = all_results[name]["vulnerability_summary"]["top_vulnerabilities"]
        for v in vulns[:2]:
            print(f"     → {v}")

    print(f"\n  💾 {json_path}")
    print(f"{'═'*60}\n")

    return report


# ═══════════════════════════════════════════════════════════
# MARKDOWN REPORT GENERATOR
# ═══════════════════════════════════════════════════════════

def generate_markdown_report(report_data=None, json_path=None):
    """Generate a premium markdown report from scan data."""
    if json_path:
        with open(json_path) as f:
            report_data = json.load(f)

    if not report_data:
        # Load latest
        files = sorted(VULN_DIR.glob("competitor_vuln_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("  No scan data found. Run --scan first.")
            return
        with open(files[0]) as f:
            report_data = json.load(f)

    date = report_data.get("scan_date", "")[:10]
    period = report_data.get("period_days", 30)
    competitors = report_data.get("competitors", {})

    lines = []
    lines.append(f"# Terpene Market Competitor Vulnerability Report")
    lines.append(f"**Week of {date}** | {period}-day lookback | Prepared by Nexus BDR Intelligence\n")
    lines.append(f"---\n")

    # Executive summary
    lines.append(f"## Executive Summary\n")
    total_vulns = report_data.get("total_vulnerabilities", 0)
    actionable = report_data.get("total_actionable_leads", 0)
    lines.append(f"**{total_vulns} competitor vulnerabilities** identified across {len(competitors)} competitors.")
    lines.append(f"**{actionable} actionable switching leads** detected — prospects actively seeking alternatives.\n")

    # Ranking
    ranked = report_data.get("ranked_by_vulnerability", [])
    if ranked:
        lines.append(f"### Vulnerability Ranking\n")
        lines.append(f"| Rank | Competitor | Score | Risk | Actionable Leads |")
        lines.append(f"|------|-----------|-------|------|-----------------|")
        for i, (name, score) in enumerate(ranked, 1):
            c = competitors.get(name, {})
            vs = c.get("vulnerability_summary", {})
            level = vs.get("risk_level", "?")
            leads = vs.get("actionable_leads", 0)
            lines.append(f"| {i} | {name} | {score} | {level} | {leads} |")
        lines.append("")

    # Per-competitor detail
    for name, score in ranked:
        c = competitors.get(name, {})
        info = c.get("info", {})
        vs = c.get("vulnerability_summary", {})
        reddit = c.get("reddit", {})
        reviews = c.get("reviews", {})
        website = c.get("website", {})

        lines.append(f"---\n")
        lines.append(f"## {name}\n")
        lines.append(f"**Position:** {info.get('market_position', '?')}")
        lines.append(f"**Botanical Pricing:** {info.get('pricing_botanical', '?')} | **CDT Pricing:** {info.get('pricing_cdt', 'N/A')}")

        tp = reviews.get("trustpilot", {})
        if tp and tp.get("rating"):
            lines.append(f"**Trustpilot:** {tp['rating']}/5.0 ({tp.get('review_count', '?')} reviews)")

        if website.get("hiring"):
            lines.append(f"**Hiring:** Active job postings detected ⚠️")

        lines.append(f"**Vulnerability Score:** {vs.get('vulnerability_score', 0)} ({vs.get('risk_level', '?')})\n")

        # Known weaknesses
        weaknesses = info.get("known_weaknesses", [])
        if weaknesses:
            lines.append(f"### Known Weaknesses")
            for w in weaknesses:
                lines.append(f"- {w}")
            lines.append("")

        # Reddit vulnerabilities
        vulns = reddit.get("vulnerabilities", [])
        if vulns:
            lines.append(f"### Reddit Vulnerabilities ({len(vulns)} found)\n")
            for v in vulns[:5]:
                sentiment = v.get("sentiment", "?")
                lines.append(f"**[{sentiment}]** r/{v.get('subreddit', '?')} — [{v.get('title', '?')[:80]}]({v.get('url', '')})")
                if v.get("switching_signals"):
                    lines.append(f"  - Switching signals: {', '.join(v['switching_signals'][:3])}")
                if v.get("negative_signals"):
                    lines.append(f"  - Complaints: {', '.join(v['negative_signals'][:3])}")
                body = v.get("body", "")[:200]
                if body:
                    lines.append(f"  > {body}...")
                lines.append("")

        # Displacement strategy
        lines.append(f"### How TBF/DFT Wins\n")
        lines.append(f"**TBF angle:** {info.get('tbf_angle', 'TBD')}")
        lines.append(f"**DFT angle:** {info.get('dft_angle', 'TBD')}\n")

    # Action items
    lines.append(f"---\n")
    lines.append(f"## This Week's Action Items\n")
    action_num = 1
    for name, score in ranked:
        c = competitors.get(name, {})
        reddit = c.get("reddit", {})
        switching = [v for v in reddit.get("vulnerabilities", []) if v.get("switching_signals")]
        if switching:
            for s in switching[:2]:
                lines.append(f"{action_num}. **Engage on Reddit** — r/{s.get('subreddit')}: user looking for alternative to {name}. [Link]({s.get('url', '')})")
                action_num += 1

    lines.append(f"\n---\n")
    lines.append(f"*Generated by Nexus BDR Competitor Vulnerability Engine | Zero API cost | Public data only*")

    md_content = "\n".join(lines)

    # Save
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    md_path = VULN_DIR / f"competitor_report_{ts}.md"
    with open(md_path, "w") as f:
        f.write(md_content)

    print(f"  📄 Report: {md_path}")
    return md_path, md_content


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Competitor Vulnerability Engine")
    parser.add_argument("--scan", action="store_true", help="Full competitor scan")
    parser.add_argument("--competitor", help="Scan specific competitor")
    parser.add_argument("--report", action="store_true", help="Generate markdown report")
    parser.add_argument("--days", type=int, default=30, help="Lookback period")
    parser.add_argument("--format", default="md", help="Report format: md")
    args = parser.parse_args()

    if args.scan:
        report = full_scan(days_back=args.days, target_competitor=args.competitor)
        if args.report or True:  # Always generate report after scan
            generate_markdown_report(report)

    elif args.competitor:
        if args.competitor not in COMPETITORS:
            print(f"  Unknown competitor. Options: {', '.join(COMPETITORS.keys())}")
            return
        report = full_scan(days_back=args.days, target_competitor=args.competitor)
        generate_markdown_report(report)

    elif args.report:
        generate_markdown_report()

    else:
        parser.print_help()
        print(f"\n  Tracked competitors:")
        for name, info in COMPETITORS.items():
            print(f"  · {name} — {info['market_position']}")
        print(f"\n  Try: python3 competitor_vuln.py --scan")


if __name__ == "__main__":
    main()
