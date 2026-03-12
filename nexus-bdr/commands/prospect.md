---
description: Run a prospecting cycle for Nexus Agriscience brands
argument-hint: [icp-profile-name]
---

Run a full prospecting cycle using the nexus-bdr-agent skill.

1. Ask which brand to prospect for if not specified: Terpene Belt Farms (TBF) or Duty Free Terpenes (DFT)
2. Select the appropriate ICP profile from config/icp-profiles.json
3. Execute Apollo lead discovery: `python3 scripts/apollo_search.py --icp $ARGUMENTS --max-leads 50`
4. Score and tier the results
5. Present the top 10 leads in a table with: Name | Title | Company | Score | Tier
6. Ask which leads to enrich with Hunter.io
7. Run enrichment: `python3 scripts/hunter_enrich.py --input [lead file]`
8. For verified hot leads, generate personalized outreach drafts
9. Present outreach for approval before any sending
10. On approval, log contacts to HubSpot: `python3 scripts/hubspot_sync.py bulk-import --input [enriched file]`
