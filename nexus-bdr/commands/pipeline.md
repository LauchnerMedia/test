---
description: Show current Nexus sales pipeline status from HubSpot
---

Pull and display the current pipeline status.

1. Run: `python3 scripts/hubspot_sync.py pipeline-report`
2. Present results grouped by stage with deal values
3. Highlight any deals that need attention (stale, missing next steps)
4. Show total pipeline value and deal count
5. If there are overdue follow-ups in outputs/follow-ups.json, flag them
