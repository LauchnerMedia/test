# Exhale Wellness + Budpop audits: handoff

Taken over from the session "Client audits: Exhale Wellness and Budpop" (Oct 8–10, 2026), which stopped at 22:58 UTC on Oct 10 on the weekly usage limit.

**Client meeting: Tue Oct 13, 2026, 1 PM.**

## Where the work lives

Everything was built on Andrew's Mac. None of it is in this repo or in Google Drive.

- Root: `~/Wavy Studios/client-dashboards/exhale-budpop/`
- Deck: `deck-2026-10-13/Exhale-Budpop-Retention-Update-2026-10-13.pptx` (53 slides). Build: `collect_numbers.py`, `build_deck.js`, `qa_deck.py`, `numbers.json`, `README.md` (fix table per issue), `previews/`
- Monthly report: `monthly-report/2026-09/` (`numbers.json`)
- BFCM war room: `bfcm-2026/war-room/` (`index.html`, `calendar-exhale.csv`, `calendar-budpop.csv`, `product-name-map.csv`, `PLAN-NOTES.md`, `qa/lint.json`, `src/plan_data.py`)
- Opportunity register: `deep-dive/opportunities/REGISTER/` (`register.json`, `register-{exhale,budpop}.csv`, `merge-log.csv`, `overlap-map.json`, `situations-*.csv`, `client-shortlist-*.csv`, `register.html`, `scripts/build_register.py`)
- Measurement plan: `tests.json` v2.0.0, plus `render_tables.py`, `make_manifest.py` and `MANIFEST.json` (16 files with sha256)
- Adversarial audit: `adversarial-audit/` (`exbp-audit-pack.zip` for round 1, `exbp-audit-pack-r2.zip` for round 2, `round1-chatgpt/`)

## Status at handoff

| Workstream | State |
|---|---|
| Round-1 ChatGPT audit (40 issues) | Done. Fixes applied across the deck, report, measurement plan, subscription spec and BFCM plan |
| Client deck | Rebuilt, 53 slides (25 spoken path + appendix), QA clean. Slide 23 and the new slide 49 match measurement plan v2 |
| Measurement plan v2 | Self-tests pass. Only causal January read is checkout (5.5 pts Exhale / 6.1 Budpop). Subscription recovery reads in July at the earliest. THCA replenishment test dropped |
| BFCM war room | Gates-first plan. New "uc" unique-code gate (live Oct 30) and "BFCM26 · Consent hold" segment added |
| Opportunity sweeps A–E | All five done (Exhale 89 items, Budpop 84) |
| De-duplicated register | Done: **68 Exhale / 65 Budpop** (from 120 / 119). Ranked by safety, then pool size, then effort. Client top 15 per brand |
| **Round-2 ChatGPT audit** | **Sent Oct 10, 22:28 UTC. Still running when the session stopped.** Chat "Audit Pack Review", chatgpt.com/c/6acaa11b-e9e8-83e8-b041-ee011914afa2. Result never collected |

## Next steps, in order

1. **Collect the round-2 result** from the ChatGPT chat above. It was asked for: Fixed / Partial / Not fixed / Regressed on all 40 round-1 issues, with evidence; new issues the fixes introduced; a run of the measurement code; a register audit (merges, overlaps, de-dup math, ranking, client safety); a spot-check of the 15 highest-impact sweep claims; and a go/no-go with the minimum must-fix list for Tuesday.
2. **Triage and fix** the must-fix items in the deck, register, BFCM plan and measurement plan. Re-run each build's QA: deck `qa_deck.py`, BFCM lint + Playwright, register `build_register.py`.
3. **Monday Oct 12 morning:** re-run the pulse for the week ending Oct 11, then `collect_numbers.py` + `build_deck.js`.
4. **Open the PPTX in PowerPoint once.** The previews are HTML renders; there was no PowerPoint or LibreOffice on the Mac.
5. **Daniel:** confirm each "In progress [confirm before meeting]" status row on slides 3–5 against the live accounts, with the time checked.
6. **Decide on capacity:** the BFCM plan adds 46 sends, about 248 hours through Dec 14 (27–28 h/week). An 11-step cut list in `PLAN-NOTES.md` saves up to 34 hours.
7. **Decide on the client cut:** 7 of Exhale's and 9 of Budpop's client top-15 are safety or infrastructure items. A revenue-only cut is a quick change if wanted.

## Decisions on the deck (slide 24) for the client

- Retention.com welcome pause: decide **Oct 13**, live Oct 14 (complaints are above 0.3% on both brands).
- Inbox and Postmaster monitoring access by Oct 14–15.
- Permission and account check, plus stop rules, by Oct 16.
- Counsel: the 11,143 Exhale buyers imported into Budpop as subscribed (Sep 2025), and the Retention.com profiles that never subscribed. Both are held out of BFCM audiences until decided.

## Top safety items ("this week")

- **Exhale:** EX-01 flower/vape in live emails, feeds and nav · EX-02 Retention.com welcome · EX-03 consent gate · EX-04 postal address missing (116 templates) · EX-05 Postmaster · EX-06 DMARC · EX-08 "[Pending] order on hold" subjects · EX-09 paid review incentive · EX-10 broken links
- **Budpop:** BP-01 flower/vape exposure · BP-02 Retention.com welcome · BP-03 browse flows with no category filter · BP-04 consent gate · BP-05 Postmaster · BP-06 DMARC · BP-08 review incentive · BP-09 misleading subject · BP-10 cross-brand import · BP-11 SPF · BP-13 links
- Hemp-law wording library (EX-07 / BP-07) is tagged "Before BFCM".

## Facts to carry forward

- Both checkouts already have the email opt-in box. This corrects diagnostics #11 and EX-A-16 / BP-A-17.
- Per-person codes barely work: 7 of 2,174 (Exhale) and 4 of 1,762 (Budpop) were redeemed. The "uc" gate must pass before the honest-timer capture and 8 early-access sends.
- Welcome-code leakage: Exhale $46.3k a year (EXSW4U alone $29.1k). Budpop's pop-up shows WCS20BPM but the emails give SD209, which has no minimum.
- Never mix Woo and Klaviyo on-hold subscription censuses. Never add pools across different value bases or across brands (see "What can't be combined" in the register output).
