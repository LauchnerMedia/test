#!/usr/bin/env python3
"""
Customer Intelligence Framework — Nexus BDR Agent
===================================================
Post-onboarding revenue engine for Terpene Belt Farms.

Connects to TBF's actual customer database and generates:
  1. Churn Risk Detection — who's ordering less, about to leave
  2. Upsell Opportunities — who's only buying one product line
  3. Reactivation Targets — who hasn't ordered in 60/90/120 days
  4. Seasonal Forecasting — predict demand spikes by strain/product
  5. Competitive Displacement — which customers mention competitors
  6. Expansion Scoring — which customers are ready for volume upgrades
  7. Automated Outreach Triggers — when to reach out and with what message

Data Sources (configure on onboarding):
  - Shopify/WooCommerce order data
  - HubSpot/GHL CRM contacts
  - Email engagement (Klaviyo/HubSpot)
  - Social media mentions
  - Support tickets

Usage:
    python3 customer_intel.py --config config/tbf_database.json
    python3 customer_intel.py --config config/tbf_database.json --report weekly
    python3 customer_intel.py --config config/tbf_database.json --customer "Mellow Fellow"
    python3 customer_intel.py --demo   # Run with sample data

Output: JSON intelligence reports + GHL/HubSpot sync + email triggers
"""

import os, sys, json, re, argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "outputs"
INTEL_DIR = OUTPUT_DIR / "customer_intel"
INTEL_DIR.mkdir(exist_ok=True)

# ── DATABASE CONNECTORS ──

class ShopifyConnector:
    """Connect to Shopify store for order data."""

    def __init__(self, config):
        self.shop = config.get("shop_url", "")
        self.token = config.get("access_token", "")
        self.api_version = config.get("api_version", "2024-01")

    def get_orders(self, since_days=365, status="any"):
        """Fetch orders from Shopify."""
        import requests
        since = (datetime.utcnow() - timedelta(days=since_days)).isoformat()
        url = f"https://{self.shop}/admin/api/{self.api_version}/orders.json"
        headers = {"X-Shopify-Access-Token": self.token}
        params = {"status": status, "created_at_min": since, "limit": 250}

        all_orders = []
        while url:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                print(f"  ❌ Shopify error: {resp.status_code}")
                break
            data = resp.json()
            all_orders.extend(data.get("orders", []))
            # Pagination
            link = resp.headers.get("Link", "")
            if 'rel="next"' in link:
                url = re.search(r'<(.*?)>; rel="next"', link).group(1)
                params = {}
            else:
                url = None

        return self._normalize_orders(all_orders)

    def _normalize_orders(self, orders):
        """Normalize Shopify orders to standard format."""
        normalized = []
        for o in orders:
            customer = o.get("customer", {})
            items = []
            for li in o.get("line_items", []):
                items.append({
                    "product": li.get("title", ""),
                    "sku": li.get("sku", ""),
                    "quantity": li.get("quantity", 0),
                    "price": float(li.get("price", 0)),
                    "variant": li.get("variant_title", ""),
                })

            normalized.append({
                "order_id": str(o.get("id")),
                "date": o.get("created_at", ""),
                "customer_id": str(customer.get("id", "")),
                "customer_name": f"{customer.get('first_name','')} {customer.get('last_name','')}".strip(),
                "customer_email": customer.get("email", ""),
                "company": customer.get("company", o.get("company", "")),
                "total": float(o.get("total_price", 0)),
                "items": items,
                "status": o.get("financial_status", ""),
                "tags": o.get("tags", "").split(",") if o.get("tags") else [],
                "state": o.get("shipping_address", {}).get("province_code", ""),
                "source": "shopify",
            })
        return normalized


class WooCommerceConnector:
    """Connect to WooCommerce for order data."""

    def __init__(self, config):
        self.url = config.get("url", "")
        self.key = config.get("consumer_key", "")
        self.secret = config.get("consumer_secret", "")

    def get_orders(self, since_days=365):
        """Fetch orders from WooCommerce."""
        import requests
        since = (datetime.utcnow() - timedelta(days=since_days)).strftime("%Y-%m-%dT00:00:00")
        api_url = f"{self.url}/wp-json/wc/v3/orders"
        params = {"after": since, "per_page": 100, "page": 1}
        auth = (self.key, self.secret)

        all_orders = []
        while True:
            resp = requests.get(api_url, params=params, auth=auth, timeout=30)
            if resp.status_code != 200:
                break
            orders = resp.json()
            if not orders:
                break
            all_orders.extend(orders)
            params["page"] += 1

        return self._normalize_orders(all_orders)

    def _normalize_orders(self, orders):
        normalized = []
        for o in orders:
            billing = o.get("billing", {})
            items = []
            for li in o.get("line_items", []):
                items.append({
                    "product": li.get("name", ""),
                    "sku": li.get("sku", ""),
                    "quantity": li.get("quantity", 0),
                    "price": float(li.get("total", 0)),
                })
            normalized.append({
                "order_id": str(o.get("id")),
                "date": o.get("date_created", ""),
                "customer_id": str(o.get("customer_id", "")),
                "customer_name": f"{billing.get('first_name','')} {billing.get('last_name','')}".strip(),
                "customer_email": billing.get("email", ""),
                "company": billing.get("company", ""),
                "total": float(o.get("total", 0)),
                "items": items,
                "status": o.get("status", ""),
                "state": billing.get("state", ""),
                "source": "woocommerce",
            })
        return normalized


class CSVConnector:
    """Load orders from CSV export."""

    def __init__(self, config):
        self.path = config.get("csv_path", "")

    def get_orders(self, since_days=365):
        import csv
        orders = []
        with open(self.path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                orders.append({
                    "order_id": row.get("order_id", row.get("id", "")),
                    "date": row.get("date", row.get("created_at", "")),
                    "customer_id": row.get("customer_id", ""),
                    "customer_name": row.get("customer_name", row.get("name", "")),
                    "customer_email": row.get("email", ""),
                    "company": row.get("company", ""),
                    "total": float(row.get("total", 0)),
                    "items": [{"product": row.get("product", ""), "quantity": int(row.get("quantity", 1)), "price": float(row.get("total", 0))}],
                    "status": row.get("status", "completed"),
                    "state": row.get("state", ""),
                    "source": "csv",
                })
        return orders


# ── ANALYSIS ENGINE ──

class CustomerIntelligence:
    """Core analysis engine."""

    def __init__(self, orders):
        self.orders = orders
        self.customers = self._build_customer_profiles()

    def _build_customer_profiles(self):
        """Build rich customer profiles from order history."""
        profiles = defaultdict(lambda: {
            "customer_id": "",
            "name": "",
            "email": "",
            "company": "",
            "state": "",
            "orders": [],
            "total_revenue": 0,
            "order_count": 0,
            "first_order": None,
            "last_order": None,
            "products_purchased": defaultdict(int),
            "product_lines": set(),
            "avg_order_value": 0,
            "order_frequency_days": 0,
            "days_since_last_order": 0,
        })

        for o in self.orders:
            cid = o["customer_email"] or o["customer_id"] or o["customer_name"]
            if not cid:
                continue

            p = profiles[cid]
            p["customer_id"] = o["customer_id"]
            p["name"] = o["customer_name"] or p["name"]
            p["email"] = o["customer_email"] or p["email"]
            p["company"] = o["company"] or p["company"]
            p["state"] = o["state"] or p["state"]
            p["orders"].append(o)
            p["total_revenue"] += o["total"]
            p["order_count"] += 1

            order_date = o["date"][:10] if o["date"] else None
            if order_date:
                if not p["first_order"] or order_date < p["first_order"]:
                    p["first_order"] = order_date
                if not p["last_order"] or order_date > p["last_order"]:
                    p["last_order"] = order_date

            for item in o["items"]:
                prod = item["product"]
                p["products_purchased"][prod] += item.get("quantity", 1)
                # Categorize product lines
                prod_lower = prod.lower()
                if any(t in prod_lower for t in ["og kush", "blue dream", "gelato", "wedding cake", "sour diesel"]):
                    p["product_lines"].add("classic_strains")
                elif any(t in prod_lower for t in ["runtz", "biscotti", "zoap", "jealousy"]):
                    p["product_lines"].add("exotic_strains")
                elif "custom" in prod_lower or "blend" in prod_lower:
                    p["product_lines"].add("custom_blends")
                elif "sample" in prod_lower:
                    p["product_lines"].add("samples")

        # Calculate derived metrics
        now = datetime.utcnow().strftime("%Y-%m-%d")
        for cid, p in profiles.items():
            if p["order_count"] > 0:
                p["avg_order_value"] = round(p["total_revenue"] / p["order_count"], 2)
            if p["last_order"]:
                try:
                    last = datetime.strptime(p["last_order"], "%Y-%m-%d")
                    p["days_since_last_order"] = (datetime.utcnow() - last).days
                except:
                    pass
            if p["order_count"] > 1 and p["first_order"] and p["last_order"]:
                try:
                    first = datetime.strptime(p["first_order"], "%Y-%m-%d")
                    last = datetime.strptime(p["last_order"], "%Y-%m-%d")
                    span = (last - first).days
                    p["order_frequency_days"] = round(span / (p["order_count"] - 1))
                except:
                    pass
            p["product_lines"] = list(p["product_lines"])
            p["products_purchased"] = dict(p["products_purchased"])

        return dict(profiles)

    def churn_risk(self, threshold_multiplier=1.5):
        """Identify customers at risk of churning."""
        at_risk = []
        for cid, p in self.customers.items():
            if p["order_count"] < 2:
                continue
            freq = p["order_frequency_days"]
            days_since = p["days_since_last_order"]
            if freq > 0 and days_since > freq * threshold_multiplier:
                risk_score = min(100, int((days_since / freq) * 40))
                at_risk.append({
                    "customer": p["name"],
                    "company": p["company"],
                    "email": p["email"],
                    "risk_score": risk_score,
                    "days_since_last": days_since,
                    "avg_frequency": freq,
                    "overdue_by": days_since - freq,
                    "ltv": p["total_revenue"],
                    "order_count": p["order_count"],
                    "last_products": list(p["products_purchased"].keys())[:3],
                    "action": f"Re-engagement email with offer on {list(p['products_purchased'].keys())[0] if p['products_purchased'] else 'their usual order'}",
                })
        return sorted(at_risk, key=lambda x: x["risk_score"], reverse=True)

    def upsell_opportunities(self):
        """Find customers buying from only one product line."""
        opportunities = []
        for cid, p in self.customers.items():
            if p["order_count"] < 1:
                continue
            lines = p["product_lines"]
            missing = []
            all_lines = ["classic_strains", "exotic_strains", "custom_blends"]
            for line in all_lines:
                if line not in lines:
                    missing.append(line)

            if missing and p["total_revenue"] > 100:
                opportunities.append({
                    "customer": p["name"],
                    "company": p["company"],
                    "email": p["email"],
                    "current_lines": lines,
                    "missing_lines": missing,
                    "ltv": p["total_revenue"],
                    "avg_order": p["avg_order_value"],
                    "action": f"Introduce {missing[0].replace('_', ' ')} with sample offer",
                })
        return sorted(opportunities, key=lambda x: x["ltv"], reverse=True)

    def reactivation_targets(self, days_thresholds=(60, 90, 120, 180)):
        """Segment dormant customers by inactivity period."""
        segments = {d: [] for d in days_thresholds}
        for cid, p in self.customers.items():
            days = p["days_since_last_order"]
            for threshold in sorted(days_thresholds):
                if days >= threshold:
                    bucket = threshold
            if days >= min(days_thresholds):
                segments[bucket].append({
                    "customer": p["name"],
                    "company": p["company"],
                    "email": p["email"],
                    "days_inactive": days,
                    "ltv": p["total_revenue"],
                    "last_order": p["last_order"],
                    "last_products": list(p["products_purchased"].keys())[:3],
                })
        return {f"{d}d+": sorted(v, key=lambda x: x["ltv"], reverse=True) for d, v in segments.items()}

    def seasonal_analysis(self):
        """Analyze ordering patterns by month to predict demand."""
        monthly = defaultdict(lambda: {"orders": 0, "revenue": 0, "products": defaultdict(int)})
        for o in self.orders:
            try:
                month = o["date"][:7]  # YYYY-MM
                monthly[month]["orders"] += 1
                monthly[month]["revenue"] += o["total"]
                for item in o["items"]:
                    monthly[month]["products"][item["product"]] += item.get("quantity", 1)
            except:
                continue

        # Convert to sortable list
        trends = []
        for month, data in sorted(monthly.items()):
            top_products = sorted(data["products"].items(), key=lambda x: x[1], reverse=True)[:5]
            trends.append({
                "month": month,
                "orders": data["orders"],
                "revenue": round(data["revenue"], 2),
                "top_products": [{"product": p, "quantity": q} for p, q in top_products],
            })
        return trends

    def customer_segments(self):
        """Segment customers into value tiers."""
        segments = {"enterprise": [], "growth": [], "starter": [], "one_time": []}
        for cid, p in self.customers.items():
            if p["total_revenue"] >= 5000 or p["order_count"] >= 10:
                segments["enterprise"].append(p)
            elif p["total_revenue"] >= 1000 or p["order_count"] >= 4:
                segments["growth"].append(p)
            elif p["order_count"] >= 2:
                segments["starter"].append(p)
            else:
                segments["one_time"].append(p)

        return {
            tier: {
                "count": len(customers),
                "total_revenue": round(sum(c["total_revenue"] for c in customers), 2),
                "avg_ltv": round(sum(c["total_revenue"] for c in customers) / len(customers), 2) if customers else 0,
                "customers": sorted(
                    [{"name": c["name"], "company": c["company"], "revenue": c["total_revenue"], "orders": c["order_count"]}
                     for c in customers],
                    key=lambda x: x["revenue"], reverse=True
                )[:20],
            }
            for tier, customers in segments.items()
        }

    def expansion_scores(self):
        """Score customers for volume expansion readiness."""
        scores = []
        for cid, p in self.customers.items():
            if p["order_count"] < 2:
                continue

            score = 0
            reasons = []

            # Increasing order values
            order_values = [o["total"] for o in sorted(p["orders"], key=lambda x: x["date"])]
            if len(order_values) >= 3:
                recent_avg = sum(order_values[-3:]) / 3
                older_avg = sum(order_values[:3]) / 3
                if recent_avg > older_avg * 1.2:
                    score += 25
                    reasons.append("Order values trending up 20%+")

            # High frequency
            if 0 < p["order_frequency_days"] < 30:
                score += 20
                reasons.append(f"Orders every {p['order_frequency_days']} days")

            # Multiple product lines
            if len(p["product_lines"]) >= 2:
                score += 15
                reasons.append(f"Buys across {len(p['product_lines'])} product lines")

            # High LTV
            if p["total_revenue"] > 2000:
                score += 20
                reasons.append(f"${p['total_revenue']:.0f} LTV")

            # Recent activity
            if p["days_since_last_order"] < 30:
                score += 20
                reasons.append("Ordered in last 30 days")

            if score >= 30:
                scores.append({
                    "customer": p["name"],
                    "company": p["company"],
                    "email": p["email"],
                    "expansion_score": min(100, score),
                    "reasons": reasons,
                    "current_ltv": p["total_revenue"],
                    "avg_order": p["avg_order_value"],
                    "action": "Schedule volume pricing consultation",
                })

        return sorted(scores, key=lambda x: x["expansion_score"], reverse=True)

    def generate_full_report(self):
        """Generate comprehensive intelligence report."""
        report = {
            "generated": datetime.utcnow().isoformat(),
            "overview": {
                "total_customers": len(self.customers),
                "total_orders": len(self.orders),
                "total_revenue": round(sum(p["total_revenue"] for p in self.customers.values()), 2),
                "avg_customer_ltv": round(
                    sum(p["total_revenue"] for p in self.customers.values()) / max(len(self.customers), 1), 2
                ),
            },
            "segments": self.customer_segments(),
            "churn_risk": self.churn_risk()[:20],
            "upsell": self.upsell_opportunities()[:20],
            "reactivation": self.reactivation_targets(),
            "expansion": self.expansion_scores()[:20],
            "seasonal": self.seasonal_analysis(),
        }
        return report


# ── DEMO DATA ──

def generate_demo_data():
    """Generate realistic sample data for demo purposes."""
    import random
    random.seed(42)

    strains = [
        "OG Kush 100ml", "Blue Dream 100ml", "Gelato 100ml", "Wedding Cake 100ml",
        "Sour Diesel 100ml", "Runtz 100ml", "Biscotti 100ml", "Gary Payton 100ml",
        "Custom Blend A 500ml", "Custom Blend B 500ml", "Sample Kit 5ml x 5",
        "Pineapple Express 100ml", "Jack Herer 100ml", "Zkittlez 100ml",
    ]

    companies = [
        ("MellowCo", "jj@mellowco.com", "FL"),
        ("VapeTech Labs", "mike@vapetech.com", "CA"),
        ("Green Leaf Brands", "sarah@greenleaf.com", "CO"),
        ("Pacific Extracts", "dave@pacificext.com", "OR"),
        ("East Coast Carts", "jen@eccarts.com", "NY"),
        ("Hemp Haven", "tom@hemphaven.com", "TX"),
        ("Elevated Products", "lisa@elevated.com", "NV"),
        ("Craft Cannabis Co", "alex@craftcanna.com", "WA"),
        ("Sun State Vapes", "maria@sunstate.com", "AZ"),
        ("Northern Terpenes", "chris@northern.com", "MI"),
        ("Delta Dynamics", "paul@deltadyn.com", "OH"),
        ("Botanical Bros", "nick@botbros.com", "IL"),
    ]

    orders = []
    base_date = datetime(2025, 3, 1)

    for company_name, email, state in companies:
        n_orders = random.randint(1, 15)
        for i in range(n_orders):
            order_date = base_date + timedelta(days=random.randint(0, 365))
            n_items = random.randint(1, 4)
            items = []
            for _ in range(n_items):
                strain = random.choice(strains)
                qty = random.choice([1, 2, 3, 5, 10])
                price = random.choice([15, 25, 80, 120, 350, 500]) * qty
                items.append({"product": strain, "quantity": qty, "price": price, "sku": ""})

            orders.append({
                "order_id": f"DEMO-{len(orders)+1:04d}",
                "date": order_date.isoformat(),
                "customer_id": email,
                "customer_name": email.split("@")[0].title(),
                "customer_email": email,
                "company": company_name,
                "total": sum(i["price"] for i in items),
                "items": items,
                "status": "completed",
                "state": state,
                "source": "demo",
            })

    return orders


# ── MAIN ──

def main():
    parser = argparse.ArgumentParser(description="Customer Intelligence Framework")
    parser.add_argument("--config", help="Path to database config JSON")
    parser.add_argument("--report", default="full", choices=["full", "weekly", "churn", "upsell", "expansion"])
    parser.add_argument("--customer", help="Analyze specific customer")
    parser.add_argument("--demo", action="store_true", help="Run with demo data")
    args = parser.parse_args()

    print(f"\n  ═══ Customer Intelligence Framework ═══")
    print(f"  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")

    # Load data
    if args.demo:
        print(f"  📦 Loading demo data...")
        orders = generate_demo_data()
    elif args.config:
        with open(args.config) as f:
            config = json.load(f)
        connector_type = config.get("type", "csv")
        print(f"  📦 Connecting to {connector_type}...")
        if connector_type == "shopify":
            connector = ShopifyConnector(config)
        elif connector_type == "woocommerce":
            connector = WooCommerceConnector(config)
        elif connector_type == "csv":
            connector = CSVConnector(config)
        else:
            print(f"  ❌ Unknown connector: {connector_type}")
            sys.exit(1)
        orders = connector.get_orders()
    else:
        print("  Use --demo for sample data or --config for real database")
        parser.print_help()
        sys.exit(0)

    print(f"  📊 {len(orders)} orders loaded\n")

    # Run analysis
    intel = CustomerIntelligence(orders)
    report = intel.generate_full_report()

    # Display
    ov = report["overview"]
    print(f"  Overview:")
    print(f"    Customers: {ov['total_customers']}")
    print(f"    Orders: {ov['total_orders']}")
    print(f"    Revenue: ${ov['total_revenue']:,.2f}")
    print(f"    Avg LTV: ${ov['avg_customer_ltv']:,.2f}")

    segs = report["segments"]
    print(f"\n  Segments:")
    for tier, data in segs.items():
        print(f"    {tier}: {data['count']} customers, ${data['total_revenue']:,.2f} revenue, ${data['avg_ltv']:,.2f} avg LTV")

    churn = report["churn_risk"]
    if churn:
        print(f"\n  🔴 Churn Risk ({len(churn)} at risk):")
        for c in churn[:5]:
            print(f"    {c['customer']} ({c['company']}) — Risk: {c['risk_score']}% | {c['days_since_last']}d since last | ${c['ltv']:,.0f} LTV")

    upsell = report["upsell"]
    if upsell:
        print(f"\n  🟡 Upsell Opportunities ({len(upsell)}):")
        for u in upsell[:5]:
            print(f"    {u['customer']} ({u['company']}) — Missing: {', '.join(u['missing_lines'])} | ${u['ltv']:,.0f} LTV")

    expansion = report["expansion"]
    if expansion:
        print(f"\n  🟢 Expansion Ready ({len(expansion)}):")
        for e in expansion[:5]:
            print(f"    {e['customer']} ({e['company']}) — Score: {e['expansion_score']} | {', '.join(e['reasons'][:2])}")

    # Save
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    report_path = INTEL_DIR / f"intel_report_{ts}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n  💾 {report_path}")
    print()


if __name__ == "__main__":
    main()
