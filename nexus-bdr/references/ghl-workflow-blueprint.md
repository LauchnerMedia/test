# 🔧 GHL Workflow Blueprint — Nexus BDR Automation
*Build these workflows in GHL UI. Each one triggers automatically.*
*Generated: March 04, 2026*

---

## Overview

Your CRM has 53 custom fields, a scoring system, and brand assignment.
These workflows make it all AUTOMATIC — when a contact enters or changes,
the right things happen without manual intervention.

Build these in order. Each takes 5-10 minutes in GHL Workflow Builder.

---

## Workflow 1: 🏷️ Auto-Tag by Score Tier

**Trigger:** Contact Tag Added contains "nexus-bdr-agent"
**Purpose:** Ensure every imported contact gets properly categorized

**Actions:**
1. IF custom field "Nexus Lead Score" >= 80:
   - Add tag: "priority:hot"
   - Add tag: "action:outreach-now"
   - Send Internal Notification → "🔥 HOT LEAD: {{contact.name}} at {{contact.company}} — Score: {{custom.nexus_lead_score}}"

2. ELSE IF "Nexus Lead Score" >= 60:
   - Add tag: "priority:warm"
   - Add tag: "action:outreach-this-week"

3. ELSE IF "Nexus Lead Score" >= 40:
   - Add tag: "priority:cool"
   - Add tag: "action:nurture"

4. ELSE:
   - Add tag: "priority:cold"
   - Add tag: "action:research-needed"

---

## Workflow 2: 📧 New Lead Welcome Sequence — TBF

**Trigger:** Contact Tag Added = "brand:tbf" AND "priority:hot" OR "priority:warm"
**Purpose:** Auto-enroll hot/warm TBF leads in outreach sequence

**Actions:**
1. Wait 1 hour (avoid looking automated)
2. Send Email: TBF Introduction
   - Subject: "Quick question about {{contact.company}}'s terpene sourcing"
   - Template: Professional, science-forward, reference their specific products
   - FROM: Your TBF sales email

3. Wait 3 days
4. IF Email Opened:
   - Send Email: TBF Value Prop
   - Subject: "Batch consistency data from TBF"
   - Attach: TBF COA sample or consistency report

5. Wait 4 days
6. IF No Reply:
   - Send Email: TBF Sample Offer
   - Subject: "Complimentary sample kit for {{contact.company}}"

7. Wait 7 days
8. IF No Reply:
   - Add tag: "status:sequence-complete-no-reply"
   - Move opportunity to "Outreach Sent" stage

9. IF Reply at any point:
   - Remove from sequence
   - Add tag: "status:replied"
   - Move opportunity to "Engaged"
   - Send Internal Notification → "🎉 REPLY from {{contact.name}} at {{contact.company}}"

---

## Workflow 3: 📧 New Lead Welcome Sequence — DFT

**Trigger:** Contact Tag Added = "brand:dft" AND "priority:hot" OR "priority:warm"
**Purpose:** Auto-enroll hot/warm DFT leads in outreach sequence

**Actions:**
Same structure as Workflow 2 but:
- DFT brand voice (edgy, direct, anti-corporate)
- Subject lines: more casual, reference hype strains
- FROM: Your DFT sales email
- Email 1: "Your [product they make] deserves better terps"
- Email 2: "Why craft extractors are ditching [competitor]"
- Email 3: "Free Runtz + Biscotti sample kit"

---

## Workflow 4: 🔄 Engagement Escalation

**Trigger:** Contact Email Opened >= 3 times OR Contact Email Link Clicked
**Purpose:** Escalate engaged prospects for immediate follow-up

**Actions:**
1. Update custom field "Prospect Temperature" → "Warm" (or "Hot" if already Warm)
2. Add tag: "signal:engaged"
3. Move opportunity → "Engaged" stage
4. Send Internal Notification → "👀 {{contact.name}} is engaging — opened {{email.opens}} times"
5. IF Click:
   - Add tag: "signal:clicked"
   - Send Internal Notification → "🖱️ {{contact.name}} clicked — follow up NOW"

---

## Workflow 5: 📞 Reply Handler

**Trigger:** Contact Replied to Email
**Purpose:** Immediately alert on replies and update CRM

**Actions:**
1. Remove all sequence tags
2. Add tag: "status:replied"
3. Update "Response Status" → "Replied"
4. Update "Last Touch Date" → {{current_date}}
5. Increment "Total Touches"
6. Move opportunity → "Engaged"
7. Send Internal Notification (URGENT) → "📨 REPLY from {{contact.name}}: Preview of reply text"

---

## Workflow 6: ⏰ Re-engagement (Stale Leads)

**Trigger:** Contact custom field "Last Touch Date" is more than 30 days ago
         AND "Response Status" != "Replied"
         AND "Total Touches" < 5
**Purpose:** Re-engage cold leads with fresh angle

**Actions:**
1. Wait until 9:00 AM contact's timezone
2. Send Email: Re-engagement
   - New angle — don't repeat original sequence
   - Reference something new (industry news, new product, trade show)
3. Add tag: "status:re-engaged"
4. Update "Total Touches" + 1

---

## Workflow 7: 📦 Sample Follow-Up

**Trigger:** Custom field "Sample Sent" = true
**Purpose:** Follow up after samples are delivered

**Actions:**
1. Wait 5 days
2. Send Email: "How'd the samples turn out?"
3. Wait 3 days
4. IF No Reply:
   - Send Email: "Quick check — did the {{custom.sample_products}} samples arrive?"
5. Wait 5 days
6. IF No Reply:
   - Add tag: "status:sample-no-response"
   - Send Internal Notification → "Sample sent to {{contact.company}} — no response after 13 days"

---

## Workflow 8: 🎪 Trade Show Pre-Event

**Trigger:** Custom field "Trade Shows" is not empty
         AND event date is within 14 days (manual tag trigger)
**Purpose:** Warm outreach before industry events

**Actions:**
1. Add tag: "event:pre-outreach"
2. Send Email: "See you at [Event]?"
   - Reference their trade show attendance
   - Suggest meeting at the event
3. Wait 3 days
4. IF Reply → Internal notification + move to "Meeting Booked"

---

## Workflow 9: 📊 Weekly Pipeline Report

**Trigger:** Every Monday at 8:00 AM
**Purpose:** Weekly summary of pipeline health

**Actions:**
1. Send Internal Notification with pipeline stats:
   - New leads this week
   - Leads in each stage
   - Replies received
   - Meetings booked
   - Top 5 hottest prospects

---

## Workflow 10: 🚨 High-Value Lead Alert

**Trigger:** Contact Created with custom field "Nexus Lead Score" >= 80
**Purpose:** Immediate alert for hot leads

**Actions:**
1. Send Internal Notification (SMS + Email):
   "🔥 HIGH-VALUE LEAD ALERT
   {{contact.name}} — {{contact.title}} at {{contact.company}}
   Score: {{custom.nexus_lead_score}} | Brand: {{custom.nexus_brand}}
   {{contact.email}} | {{contact.phone}}
   State: {{contact.state}} | Industry: {{custom.content_themes}}"

2. Add tag: "priority:immediate-outreach"
3. Create Task: "Call {{contact.name}} at {{contact.company}} within 24 hours"

---

## Tag Taxonomy Reference

### Source Tags (auto-applied on import)
- source:apollo-export
- source:claude-research
- source:instagram
- source:trade-show
- source:csv-import
- source:license-db
- source:reddit
- source:social-intel

### Brand Tags
- brand:tbf
- brand:dft

### Priority Tags
- priority:hot (score 80+)
- priority:warm (score 60-79)
- priority:cool (score 40-59)
- priority:cold (score 0-39)

### Status Tags
- status:new
- status:researched
- status:outreach-sent
- status:replied
- status:engaged
- status:sequence-complete-no-reply
- status:re-engaged
- status:sample-no-response

### Signal Tags
- signal:engaged (3+ opens)
- signal:clicked
- signal:expanding
- signal:hiring
- signal:new-product

### Role Tags
- role:c-suite
- role:vp
- role:director
- role:manager
- role:individual

### Email Quality Tags
- email:verified
- email:invalid
- email:catch-all

### Vertical Tags
- vertical:cannabis
- vertical:hemp
- vertical:extraction
- vertical:vape

---

## Email Template Checklist

Create these email templates in GHL before activating workflows:

### TBF Templates
1. **TBF Intro** — Science-forward, professional, references their products
2. **TBF Value Prop** — Batch consistency data, COA example
3. **TBF Sample Offer** — Complimentary sample kit, specific strains
4. **TBF Re-engagement** — Fresh angle, industry news hook

### DFT Templates
1. **DFT Intro** — Edgy, direct, references their craft approach
2. **DFT Value Prop** — Hype strain accuracy, small-batch focus
3. **DFT Sample Offer** — Free sample kit, exotic strains
4. **DFT Re-engagement** — Fresh angle, underground market insight

### Shared Templates
1. **Sample Follow-Up** — "How'd the samples turn out?"
2. **Trade Show Pre-Event** — "See you at [Event]?"
3. **Meeting Confirmation** — Calendar link + prep notes
4. **Proposal Follow-Up** — After sending pricing/proposal

---

*Build workflows in this order. Test each with a single contact before activating for all.*
