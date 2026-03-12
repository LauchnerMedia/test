import { useState, useEffect, useCallback, useMemo, useRef } from "react";

// ═══════════════════════════════════════════════════════════
// REEF MODE v3 — NEXUS BDR Intelligence Operating System
// The single interface Shareef sees every morning
//
// v3 adds: Bundle Artifact Viewer, Provenance UI,
//          Playbook tagging, live snapshot + rich demo fallback
// ═══════════════════════════════════════════════════════════

// ─── DEMO DATA (rich fallback when command_center isn't running) ───

const DEMO_BUNDLES = {
  "mellow_fellow": {
    company: "Mellow Fellow",
    generatedAt: "2026-03-04T06:21:00Z",
    playbook: "COMPETITOR_STRIKE",
    confidence: "HIGH",
    confidenceScore: 87,
    actionId: "9387eb0d51dd",
    triggerSignals: [
      { id: "sig_tp01", type: "trustpilot_below_3.5", source: "Trustpilot", summary: "True Terpenes rated 3.0/5 (below displacement threshold)", timestamp: "2026-03-03T14:22:00Z", strength: 8, url: "https://trustpilot.com/review/trueterpenes.com" },
      { id: "sig_sw01", type: "switching_triggers", source: "Sales Intel Brief", summary: "3 switching triggers: batch consistency, CDT pricing, scaling supply", timestamp: "2026-03-04T05:45:00Z", strength: 7 },
    ],
    artifacts: {
      whyNow: "# Why now: Mellow Fellow\n\nGenerated: 2026-03-04T06:21:00Z\n\n## Top triggers\n- **trustpilot_below_3.5** | w=15 s=8 | True Terpenes 3.0/5 Trustpilot\n- **switching_triggers** | w=12 s=7 | Batch consistency, CDT pricing, scaling supply\n- **brief_completed** | w=3 s=3 | Full 6-phase brief available\n\n## Supplier vulnerability\nTrue Terpenes: 3.0/5 Trustpilot, 14 news articles (brand noise), active hiring (churn signal)\n\n## Switch economics\n- CDT market: $5,000–8,000/L\n- TBF CDT: $1,500–3,000/L (vertically integrated)\n- Savings: 40–80% on CDT alone\n- Botanical (DFT): $45–80/L vs competitor $80–150/L",
      email: `Subject: Quick question on terpene consistency for Mellow Fellow

Hi JJ,

I pulled a quick brief on Mellow Fellow and noticed a few signals that usually show up right before teams re-evaluate their terpene/flavor stack — specifically around batch consistency and CDT pricing at scale.

If you're open to it, we can send a small R&D kit plus a 2-week validation plan so your team can compare:
- sensory consistency batch-to-batch
- lead times / supply reliability
- documentation readiness (COAs/specs)

Worth a 10-minute call this week to see if it's relevant?

— Shareef`,
      linkedinDm: `Hey JJ — I put together a quick brief on Mellow Fellow and a short validation plan for terpene/flavor consistency. Based on your current direction with proprietary blends (Creativity, Dream, Euphoria), our CDT profiles might be worth a side-by-side. Want the 1-pager?`,
      callOpener: `Call opener:
"Hey JJ — quick one. We pulled an account brief on Mellow Fellow and saw a few signals that usually show up right before teams re-check their terpene supplier — batch consistency at scale, CDT pricing, and documentation readiness.

If I send a small R&D kit + a 2-week validation plan, would you be the right person to compare it to what you're using now?"

Objection handling:
- "We're happy with our supplier" → "Totally fair. Most of our best customers said the same thing before they did a side-by-side. The kit is free — worst case you validate that your current setup is solid."
- "What's your pricing?" → "Depends on volume and profile type. For CDT at your scale, we're typically 40-80% below market. But the real differentiator is batch consistency — that's what the validation plan tests."
- "Send me info" → "Will do. I'll include the brief, a comparison matrix, and the 2-week pilot plan. What email should I use?"`,
      heygenScript: `Hey JJ — Shareef here from Terpene Belt Farms.

I'm reaching out because we pulled a quick account brief on Mellow Fellow and saw a few signals that usually show up right before teams re-evaluate their terpene supplier.

Your proprietary blends — Creativity, Dream, Euphoria — those are effects-based profiles. That's exactly where CDT consistency matters most.

Rather than pitch, I'd rather make this easy: we can send a small R&D kit plus a 2-week validation plan so your team can compare sensory consistency, lead times, and documentation readiness side-by-side.

If it's relevant, open to a quick 10 minutes this week?`,
      competitorWedge: `# Supplier Wedge: Mellow Fellow

## Current supplier
- True Terpenes (likely) — 3.0/5 Trustpilot, vulnerability HIGH

## Displacement strategy
Lead with: batch consistency + CDT pricing advantage + documentation readiness

## 2-week switch plan
1. Day 1-3: Sensory match validation — send R&D kit matching their top 3 SKU profiles
2. Day 4-7: COGS + lead time comparison — side-by-side pricing matrix
3. Day 8-11: Small pilot on 1-2 SKUs — their team validates in-house
4. Day 12-14: Rollout decision + reorder cadence setup`,
      briefDocx: true,
      taskPayload: { campaign: "competitor_strike", steps: ["email_day1", "linkedin_day2", "call_day4", "video_day5", "followup_day8", "break_day12"], ghl_ready: true },
    },
  },
};

const DEMO_DATA = {
  systemStatus: {
    entities: 53, signals: 35, connections: 40, events: 87,
    entitiesTracked: 53, signalsToday: 35, actionsQueued: 12, outcomesRecordedToday: 0,
    lastIngest: "2026-03-04T05:28:00Z",
    learningStats: { actionsTracked: 12, outcomesRecorded: 0, signalsWeightUpdated: 0 },
    researchPapers: 121, activeTrials: 35, competitorsTracked: 7,
  },
  priorities: [
    { rank: 1, company: "Mellow Fellow", domain: "mellowfellow.fun", score: 52.6, tier: "hot", contacts: 28, verified: 0, briefComplete: true, topContact: "JJ Coombs", topTitle: "CEO & Co-Founder", features: ["brief_completed", "pipeline_score:96", "switching_triggers:3"], nextAction: "outreach", currentSupplier: "True Terpenes", actionId: "9387eb0d51dd", playbook: "COMPETITOR_STRIKE", playbookConfidence: "HIGH", angle: "supplier_switch_wedge", whyNow: "Brief completed. Current supplier True Terpenes has 3.0/5 Trustpilot. 3 switching triggers identified. CDT pricing advantage: 25-100x savings vs botanical.", bundleKey: "mellow_fellow",
      whyNowStructured: [
        { signalId: "sig_tp01", type: "trustpilot_below_3.5", source: "Trustpilot", timestamp: "2026-03-03T14:22:00Z", summary: "True Terpenes rated 3.0/5 — below displacement threshold", strength: 8 },
        { signalId: "sig_sw01", type: "switching_triggers", source: "Sales Intel Brief v4", timestamp: "2026-03-04T05:45:00Z", summary: "3 triggers: batch consistency, CDT pricing, scaling supply", strength: 7 },
        { signalId: "sig_br01", type: "brief_completed", source: "Brief Engine", timestamp: "2026-03-04T05:50:00Z", summary: "Full 6-phase brief generated — ready for outreach", strength: 3 },
      ],
    },
    { rank: 2, company: "Cannvital", domain: "cannvital.com", score: 26.8, tier: "hot", contacts: 4, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:89"], nextAction: "run_brief", currentSupplier: "", actionId: "b2c3d4e5f6a7", whyNow: "High pipeline score. European CBD manufacturer — potential terpene buyer. No brief yet." },
    { rank: 3, company: "Phytograde Labs", domain: "phytograde.com", score: 26.6, tier: "hot", contacts: 4, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:88"], nextAction: "run_brief", currentSupplier: "", actionId: "c3d4e5f6a7b8", whyNow: "Pharmaceutical-grade extraction company. Brief needed." },
    { rank: 4, company: "CBD Alchemy", domain: "cbdalchemy.com", score: 26.5, tier: "hot", contacts: 11, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:88", "contacts:11"], nextAction: "run_brief", currentSupplier: "", actionId: "d4e5f6a7b8c9", whyNow: "Large contact pool (11). European CBD brand. Possible DFT customer for botanical profiles." },
    { rank: 5, company: "Canatura", domain: "canatura.com", score: 26.3, tier: "hot", contacts: 5, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:87"], nextAction: "run_brief", currentSupplier: "", actionId: "e5f6a7b8c9d0", whyNow: "European cannabis brand. Strong pipeline score. Needs deep research brief." },
    { rank: 6, company: "Deli Hemp", domain: "delihemp.com", score: 23.6, tier: "warm", contacts: 9, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:78", "contacts:9"], nextAction: "run_brief", currentSupplier: "", actionId: "f6a7b8c9d0e1", whyNow: "Hemp retailer with 9 contacts. Potential DFT customer." },
    { rank: 7, company: "Canna Capital Group", domain: "cannacapital.com", score: 22.5, tier: "warm", contacts: 2, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:75"], nextAction: "run_brief", currentSupplier: "", actionId: "a7b8c9d0e1f2", whyNow: "Cannabis investment group. Gateway to portfolio companies." },
    { rank: 8, company: "A-Sense Brand", domain: "a-sense.co", score: 21.9, tier: "warm", contacts: 22, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:73", "contacts:22"], nextAction: "run_brief", currentSupplier: "", actionId: "b8c9d0e1f2a3", whyNow: "Largest contact pool (22). Sensory brand — strong terpene angle." },
    { rank: 9, company: "Alplant", domain: "alplant.ch", score: 21.4, tier: "warm", contacts: 4, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:71"], nextAction: "run_brief", currentSupplier: "", actionId: "c9d0e1f2a3b4", whyNow: "Swiss plant-based company. Precision terpene applications." },
    { rank: 10, company: "Euphoria Trade", domain: "euphoria.nl", score: 21.2, tier: "warm", contacts: 3, verified: 0, briefComplete: false, topContact: "—", topTitle: "—", features: ["pipeline_score:70"], nextAction: "run_brief", currentSupplier: "", actionId: "d0e1f2a3b4c5", whyNow: "European cannabis accessories/products. Effects-based brand name." },
  ],
  competitors: [
    { name: "True Terpenes", trustpilot: 3.0, risk: "HIGH", score: 15, hiring: true, vulnerability: "Low Trustpilot (3.0/5), active hiring suggests churn, 14 news articles — brand noise" },
    { name: "Abstrax Tech", trustpilot: 4.7, risk: "LOW", score: 5, hiring: true, vulnerability: "Strong brand but premium pricing. Hiring = growth or backfill?" },
    { name: "Floraplex", trustpilot: null, risk: "LOW", score: 2, hiring: false, vulnerability: "Budget player. Low visibility. Not a direct threat to CDT positioning" },
    { name: "Peak Supply Co", trustpilot: 3.7, risk: "MEDIUM", score: 8, hiring: false, vulnerability: "Below-average reviews (3.7/5). Potential displacement target for quality-focused buyers" },
    { name: "Denver Terpenes", trustpilot: null, risk: "LOW", score: 0, hiring: false, vulnerability: "Regional player. Limited online presence" },
    { name: "Extract Consultants", trustpilot: null, risk: "LOW", score: 0, hiring: false, vulnerability: "Consulting model. Different positioning than supply" },
    { name: "Terps USA", trustpilot: null, risk: "LOW", score: 0, hiring: false, vulnerability: "Limited data available. Small market share" },
  ],
  redditSignals: [
    { type: "SUPPLIER SEEKING", subreddit: "hempflowers", title: "Anxiety & Sensitivity to THC — looking for alternatives", url: "#", score: 8 },
    { type: "SUPPLIER SEEKING", subreddit: "FLMedicalTrees", title: "What to actually look for in COAs", url: "#", score: 7 },
    { type: "SUPPLIER SEEKING", subreddit: "TheOCS", title: "Looking for Hash Recommendations", url: "#", score: 6 },
    { type: "DISCUSSION", subreddit: "TheOCS", title: "HUT - Dual Z (RS11 & Souffle) 28g", url: "#", score: 4 },
  ],
  researchHighlights: [
    { title: "Therapeutic use of cannabinoids in age-related pain management", journal: "Pharmacological Research", year: 2026, terpenes: ["beta-caryophyllene", "linalool"], score: 89 },
    { title: "Beta-caryophyllene enhances transdermal drug delivery via CB2 activation", journal: "J Pharmaceutical Sciences", year: 2026, terpenes: ["beta-caryophyllene"], score: 78 },
    { title: "Limonene anxiolytic effects in clinical trial settings", journal: "Phytomedicine", year: 2025, terpenes: ["limonene"], score: 72 },
    { title: "Synergistic anti-inflammatory activity of terpene blends", journal: "Cannabis and Cannabinoid Research", year: 2025, terpenes: ["beta-pinene", "alpha-pinene", "linalool"], score: 68 },
    { title: "Entourage effect mechanisms: terpene-cannabinoid interactions", journal: "Frontiers in Pharmacology", year: 2025, terpenes: ["myrcene", "limonene", "beta-caryophyllene"], score: 65 },
  ],
  signalWeights: [
    { signal: "Trustpilot Below 3.5", weight: 15.0 },
    { signal: "Quality Complaint (Competitor)", weight: 12.0 },
    { signal: "Regulatory Change", weight: 12.0 },
    { signal: "Reddit: Supplier Seeking", weight: 10.0 },
    { signal: "Leadership Change", weight: 9.0 },
    { signal: "Trustpilot Below 4.0", weight: 8.0 },
    { signal: "Funding News", weight: 8.0 },
    { signal: "Reddit: Complaint", weight: 7.0 },
    { signal: "Price Discussion", weight: 7.0 },
    { signal: "New Product Launch", weight: 6.0 },
  ],
};

// ─── API helpers ───

const API = (typeof window !== "undefined" && window.__REEF_API__) || {
  snapshot: "/api/reef/snapshot",
  run: "/api/reef/run",
  job: "/api/reef/job",
  outcome: "/api/reef/outcome",
};

async function jfetch(url, opts = {}) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opts });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
  if (!res.ok) { const err = new Error((data && (data.error || data.message)) || res.statusText); err.status = res.status; err.payload = data; throw err; }
  return data;
}

// ─── Design tokens ───

const C = {
  bg: "#0A0A0A", surface: "rgba(255,255,255,0.02)", surfaceHover: "rgba(255,255,255,0.04)",
  border: "rgba(255,255,255,0.06)", borderGold: "rgba(197,165,90,0.25)",
  gold: "#C5A55A", goldDim: "rgba(197,165,90,0.12)", goldBg: "rgba(197,165,90,0.06)",
  text: "#E8E0D0", textDim: "#AAA", textMuted: "#666", textDark: "#444",
  red: "#FF4136", orange: "#FF851B", blue: "#0074D9", green: "#2ECC40",
  font: "'DM Sans', system-ui, -apple-system, sans-serif",
  fontDisplay: "'Playfair Display', Georgia, serif",
  mono: "'SF Mono', 'Fira Code', monospace",
};
const tierColors = { hot: C.red, warm: C.orange, cool: C.blue, cold: "#AAA" };
const riskColors = { HIGH: C.red, MEDIUM: C.orange, LOW: C.green };
const playbookLabels = {
  COMPETITOR_STRIKE: { label: "Competitor Strike", color: C.red, icon: "⚔" },
  VAPE_MARGIN_DEFENSE: { label: "Vape Margin Defense", color: C.orange, icon: "◈" },
  BEVERAGE_INNOVATION: { label: "Beverage Innovation", color: C.blue, icon: "◉" },
  COMAN_ENABLEMENT: { label: "Co-Man Enablement", color: C.green, icon: "◎" },
  REGULATORY_READINESS: { label: "Regulatory Ready", color: "#9B59B6", icon: "△" },
};

// ─── Shared components ───

function GoldDivider() {
  return <div style={{ height: 1, background: "linear-gradient(90deg, transparent, #C5A55A 20%, #C5A55A 80%, transparent)", margin: "28px 0", opacity: 0.35 }} />;
}

function StatCard({ label, value, sub }) {
  return (
    <div style={{ background: C.goldBg, border: `1px solid ${C.borderGold}`, borderRadius: 8, padding: "14px 18px", minWidth: 120 }}>
      <div style={{ fontSize: 26, fontWeight: 700, color: C.gold, fontFamily: C.fontDisplay }}>{value}</div>
      <div style={{ fontSize: 11, color: "#888", marginTop: 3, textTransform: "uppercase", letterSpacing: 1.5 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false);
  const copy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text).then(() => { setCopied(true); setTimeout(() => setCopied(false), 2000); });
  };
  return (
    <button onClick={copy} style={{
      padding: "5px 12px", borderRadius: 5, fontSize: 10, fontWeight: 700, cursor: "pointer",
      background: copied ? "rgba(46,204,64,0.2)" : "rgba(255,255,255,0.05)",
      color: copied ? C.green : "#888", border: `1px solid ${copied ? "rgba(46,204,64,0.3)" : "rgba(255,255,255,0.1)"}`,
      textTransform: "uppercase", letterSpacing: 0.5, transition: "all 0.2s",
    }}>{copied ? "Copied" : label || "Copy"}</button>
  );
}

function PlaybookBadge({ playbook, confidence }) {
  const info = playbookLabels[playbook];
  if (!info) return null;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span style={{
        fontSize: 10, fontWeight: 800, padding: "3px 10px", borderRadius: 4, letterSpacing: 0.5,
        background: `${info.color}18`, color: info.color, border: `1px solid ${info.color}33`,
      }}>{info.icon} {info.label.toUpperCase()}</span>
      {confidence && (
        <span style={{
          fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 3,
          background: confidence === "HIGH" ? "rgba(46,204,64,0.12)" : confidence === "MEDIUM" ? "rgba(197,165,90,0.12)" : "rgba(255,255,255,0.05)",
          color: confidence === "HIGH" ? C.green : confidence === "MEDIUM" ? C.gold : "#888",
        }}>{confidence}</span>
      )}
    </div>
  );
}

// ─── Provenance panel ───

function ProvenancePanel({ signals }) {
  if (!signals || signals.length === 0) return null;
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontSize: 10, color: C.gold, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>Trigger Signals (provenance)</div>
      {signals.map((s, i) => (
        <div key={i} style={{
          display: "flex", alignItems: "flex-start", gap: 10, padding: "8px 12px", marginBottom: 4,
          background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: 6,
        }}>
          <div style={{
            width: 6, height: 6, borderRadius: "50%", marginTop: 5, flexShrink: 0,
            background: s.strength >= 7 ? C.red : s.strength >= 4 ? C.gold : C.blue,
          }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.5 }}>{s.summary}</div>
            <div style={{ fontSize: 10, color: C.textDark, marginTop: 3, display: "flex", gap: 12, flexWrap: "wrap" }}>
              <span style={{ fontFamily: C.mono }}>{s.type.replace(/_/g, " ")}</span>
              <span>src: {s.source}</span>
              <span>{s.timestamp ? new Date(s.timestamp).toLocaleDateString() : ""}</span>
              {s.url && s.url !== "#" && <a href={s.url} target="_blank" rel="noopener noreferrer" style={{ color: C.gold, textDecoration: "none" }}>source link</a>}
            </div>
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.gold, fontFamily: C.mono, flexShrink: 0 }}>s={s.strength}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Bundle Artifact Viewer ───

function BundleViewer({ bundle, onClose }) {
  const [activeAsset, setActiveAsset] = useState("email");
  if (!bundle) return null;

  const assets = [
    { id: "email", label: "Email", icon: "✉", content: bundle.artifacts?.email },
    { id: "linkedinDm", label: "LinkedIn DM", icon: "💬", content: bundle.artifacts?.linkedinDm },
    { id: "callOpener", label: "Call Script", icon: "📞", content: bundle.artifacts?.callOpener },
    { id: "heygenScript", label: "Video Script", icon: "🎬", content: bundle.artifacts?.heygenScript },
    { id: "whyNow", label: "Why Now", icon: "⚡", content: bundle.artifacts?.whyNow },
    { id: "competitorWedge", label: "Wedge Plan", icon: "⚔", content: bundle.artifacts?.competitorWedge },
  ].filter(a => a.content);

  const current = assets.find(a => a.id === activeAsset) || assets[0];

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 60,
      background: "rgba(0,0,0,0.85)", backdropFilter: "blur(8px)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        width: "90%", maxWidth: 920, maxHeight: "90vh", background: "#111114",
        border: `1px solid ${C.borderGold}`, borderRadius: 14, overflow: "hidden",
        display: "flex", flexDirection: "column",
      }}>
        {/* Header */}
        <div style={{ padding: "18px 24px", borderBottom: `1px solid ${C.borderGold}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: C.gold, fontFamily: C.fontDisplay }}>
              Kill Shot Bundle — {bundle.company}
            </div>
            <div style={{ fontSize: 11, color: C.textMuted, marginTop: 4, display: "flex", gap: 16, alignItems: "center" }}>
              {bundle.playbook && <PlaybookBadge playbook={bundle.playbook} confidence={bundle.confidence} />}
              <span>Generated {bundle.generatedAt ? new Date(bundle.generatedAt).toLocaleString() : "—"}</span>
              <span style={{ fontFamily: C.mono }}>action: {bundle.actionId || "—"}</span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#666", cursor: "pointer", fontSize: 20, padding: "4px 8px" }}>✕</button>
        </div>

        {/* Asset tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(0,0,0,0.3)", overflowX: "auto" }}>
          {assets.map(a => (
            <button key={a.id} onClick={() => setActiveAsset(a.id)} style={{
              padding: "10px 18px", background: "transparent", border: "none",
              borderBottom: activeAsset === a.id ? `2px solid ${C.gold}` : "2px solid transparent",
              color: activeAsset === a.id ? C.gold : "#555", cursor: "pointer",
              fontSize: 12, fontWeight: 600, whiteSpace: "nowrap", transition: "all 0.2s",
            }}>{a.icon} {a.label}</button>
          ))}
          {bundle.artifacts?.briefDocx && (
            <div style={{ padding: "10px 18px", fontSize: 12, color: C.green, fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>
              📄 Brief DOCX ✓
            </div>
          )}
        </div>

        {/* Provenance bar */}
        {bundle.triggerSignals && bundle.triggerSignals.length > 0 && (
          <div style={{ padding: "10px 24px", background: "rgba(197,165,90,0.04)", borderBottom: "1px solid rgba(255,255,255,0.04)", display: "flex", gap: 12, alignItems: "center", overflowX: "auto" }}>
            <span style={{ fontSize: 10, color: C.gold, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, flexShrink: 0 }}>Provenance:</span>
            {bundle.triggerSignals.map((s, i) => (
              <span key={i} style={{ fontSize: 10, color: C.textDim, padding: "3px 10px", background: "rgba(255,255,255,0.03)", borderRadius: 4, border: "1px solid rgba(255,255,255,0.06)", whiteSpace: "nowrap", fontFamily: C.mono }}>
                {s.type.replace(/_/g, " ")} · s={s.strength} · {s.source}
              </span>
            ))}
          </div>
        )}

        {/* Content */}
        <div style={{ flex: 1, overflow: "auto", padding: "20px 24px" }}>
          {current && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{current.icon} {current.label}</div>
                <CopyButton text={current.content} label={`Copy ${current.label}`} />
              </div>
              <pre style={{
                fontFamily: C.mono, fontSize: 12, color: C.textDim, lineHeight: 1.7,
                whiteSpace: "pre-wrap", wordBreak: "break-word",
                background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.04)",
                borderRadius: 8, padding: "18px 20px", margin: 0,
              }}>{current.content}</pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: "12px 24px", borderTop: "1px solid rgba(255,255,255,0.06)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ fontSize: 10, color: C.textDark }}>
            {assets.length} assets · {bundle.triggerSignals?.length || 0} trigger signals · attribution: {bundle.actionId || "none"}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <CopyButton text={assets.map(a => `--- ${a.label} ---\n${a.content}`).join("\n\n")} label="Copy All" />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Account Card ───

function AccountCard({ p, isExpanded, onToggle, onOutcome, onRun, onOpenBundle }) {
  const [showOutcome, setShowOutcome] = useState(false);
  const actionLabels = { outreach: "Send Outreach", run_brief: "Run Brief", verify_emails: "Verify Emails", outreach_prep: "Prep Outreach" };
  const actionColors = { outreach: C.green, run_brief: C.gold, verify_emails: C.blue, outreach_prep: C.orange };

  return (
    <div style={{
      background: isExpanded ? "rgba(197,165,90,0.08)" : C.surface,
      border: `1px solid ${isExpanded ? "rgba(197,165,90,0.3)" : C.border}`,
      borderRadius: 10, marginBottom: 8, overflow: "hidden", transition: "all 0.3s ease",
    }}>
      <div onClick={onToggle} style={{ display: "flex", alignItems: "center", padding: "14px 20px", cursor: "pointer", gap: 16 }}>
        <div style={{
          width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
          background: `rgba(${p.tier === "hot" ? "255,65,54" : "255,133,27"},0.15)`,
          color: tierColors[p.tier], fontWeight: 800, fontSize: 14, flexShrink: 0,
        }}>{p.rank}</div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <span style={{ fontWeight: 700, fontSize: 15, color: C.text }}>{p.company}</span>
            <span style={{ fontSize: 11, color: C.textMuted, fontFamily: C.mono }}>{p.domain}</span>
            {p.briefComplete && <span style={{ fontSize: 10, background: "rgba(46,204,64,0.15)", color: C.green, padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>BRIEF ✓</span>}
            {p.playbook && <PlaybookBadge playbook={p.playbook} confidence={p.playbookConfidence} />}
          </div>
          <div style={{ fontSize: 12, color: "#777", marginTop: 3 }}>
            {p.contacts} contacts · {p.verified} verified · {p.topContact !== "—" ? p.topContact : "No primary contact"}
          </div>
        </div>

        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: p.score >= 50 ? C.red : p.score >= 25 ? C.gold : C.blue, fontFamily: C.fontDisplay }}>{p.score}</div>
          <div style={{ fontSize: 10, color: tierColors[p.tier], textTransform: "uppercase", fontWeight: 700, letterSpacing: 1 }}>{p.tier}</div>
        </div>

        <div style={{
          padding: "6px 14px", borderRadius: 6, fontSize: 11, fontWeight: 700,
          background: `${actionColors[p.nextAction]}22`, color: actionColors[p.nextAction],
          textTransform: "uppercase", letterSpacing: 0.5, whiteSpace: "nowrap", flexShrink: 0,
        }}>{actionLabels[p.nextAction]}</div>

        <div style={{ color: "#555", fontSize: 18, flexShrink: 0, transition: "transform 0.2s", transform: isExpanded ? "rotate(180deg)" : "none" }}>▾</div>
      </div>

      {isExpanded && (
        <div style={{ padding: "0 20px 18px 68px", animation: "fadeIn 0.2s ease" }}>
          {/* Structured provenance (if available) */}
          {p.whyNowStructured ? (
            <ProvenancePanel signals={p.whyNowStructured} />
          ) : (
            <div style={{ fontSize: 13, color: C.textDim, lineHeight: 1.7, marginBottom: 12, borderLeft: "2px solid rgba(197,165,90,0.3)", paddingLeft: 14 }}>
              <strong style={{ color: C.gold }}>Why now:</strong> {p.whyNow}
            </div>
          )}

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
            {(p.features || []).map((f, i) => (
              <span key={i} style={{ fontSize: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", padding: "3px 10px", borderRadius: 4, color: "#888", fontFamily: C.mono }}>{f}</span>
            ))}
          </div>

          {p.currentSupplier && (
            <div style={{ fontSize: 12, color: C.orange, marginBottom: 12 }}>
              ⚠ Current supplier: <strong>{p.currentSupplier}</strong>
              {p.currentSupplier === "True Terpenes" && <span style={{ color: C.red }}> — Trustpilot 3.0/5, vulnerability HIGH</span>}
            </div>
          )}

          <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
            {p.bundleKey && (
              <button onClick={(e) => { e.stopPropagation(); onOpenBundle(p.bundleKey); }} style={{
                padding: "6px 16px", borderRadius: 6, fontSize: 11, fontWeight: 800, cursor: "pointer",
                background: "rgba(197,165,90,0.18)", color: C.gold, border: `1px solid rgba(197,165,90,0.35)`,
                textTransform: "uppercase", letterSpacing: 0.5,
              }}>⚡ Open Kill Shot Bundle</button>
            )}

            {p.nextAction === "run_brief" && (
              <button onClick={(e) => { e.stopPropagation(); onRun && onRun("war_room_brief"); }} style={{
                padding: "6px 16px", borderRadius: 6, fontSize: 11, fontWeight: 800, cursor: "pointer",
                background: "rgba(0,116,217,0.12)", color: C.blue, border: "1px solid rgba(0,116,217,0.25)",
                textTransform: "uppercase", letterSpacing: 0.5,
              }}>Run Brief</button>
            )}

            {p.nextAction === "outreach" && !p.bundleKey && (
              <button onClick={(e) => { e.stopPropagation(); onRun && onRun("bundle", p.domain || p.company); }} style={{
                padding: "6px 16px", borderRadius: 6, fontSize: 11, fontWeight: 800, cursor: "pointer",
                background: C.goldDim, color: C.gold, border: `1px solid ${C.borderGold}`,
                textTransform: "uppercase", letterSpacing: 0.5,
              }}>Generate Bundle</button>
            )}

            {!showOutcome ? (
              <button onClick={(e) => { e.stopPropagation(); setShowOutcome(true); }} style={{
                padding: "6px 16px", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer",
                background: "rgba(255,255,255,0.04)", color: "#888", border: "1px solid rgba(255,255,255,0.1)",
                textTransform: "uppercase", letterSpacing: 0.5,
              }}>Record Outcome</button>
            ) : (
              ["reply", "meeting", "closed", "no_response"].map(o => (
                <button key={o} onClick={(e) => { e.stopPropagation(); onOutcome(p.actionId, o); setShowOutcome(false); }} style={{
                  padding: "5px 12px", borderRadius: 5, fontSize: 10, fontWeight: 700, cursor: "pointer",
                  background: o === "closed" ? "rgba(46,204,64,0.2)" : o === "meeting" ? "rgba(0,116,217,0.2)" : o === "reply" ? "rgba(197,165,90,0.2)" : "rgba(255,255,255,0.05)",
                  color: o === "closed" ? C.green : o === "meeting" ? C.blue : o === "reply" ? C.gold : "#666",
                  border: "1px solid rgba(255,255,255,0.1)", textTransform: "uppercase",
                }}>{o.replace("_", " ")}</button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════

export default function ReefMode() {
  const [data, setData] = useState(null);
  const [dataError, setDataError] = useState("");
  const [expandedCard, setExpandedCard] = useState(0);
  const [activeTab, setActiveTab] = useState("priorities");
  const [outcomes, setOutcomes] = useState({});
  const [jobs, setJobs] = useState([]);
  const [jobDrawerOpen, setJobDrawerOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [activeBundleKey, setActiveBundleKey] = useState(null);

  useEffect(() => { setTimeout(() => setLoaded(true), 100); }, []);

  const showToast = useCallback((kind, message) => {
    setToast({ kind, message, ts: Date.now() });
    setTimeout(() => setToast(null), 3500);
  }, []);

  const refreshSnapshot = useCallback(async () => {
    try {
      setDataError("");
      const payload = await jfetch(API.snapshot);
      if (payload) {
        // Merge: use live data where available, fall back to demo for missing sections
        const merged = { ...DEMO_DATA };
        if (payload.priorities && payload.priorities.length > 0) merged.priorities = payload.priorities;
        if (payload.competitors && payload.competitors.length > 0) merged.competitors = payload.competitors;
        if (payload.redditSignals && payload.redditSignals.length > 0) merged.redditSignals = payload.redditSignals;
        if (payload.researchHighlights && payload.researchHighlights.length > 0) merged.researchHighlights = payload.researchHighlights;
        if (payload.synthesisInsights) merged.synthesisInsights = payload.synthesisInsights;
        if (payload.researchTrends) merged.researchTrends = payload.researchTrends;
        if (payload.researchGaps) merged.researchGaps = payload.researchGaps;
        if (payload.regulatoryHits) merged.regulatoryHits = payload.regulatoryHits;
        if (payload.terpeneMatrix) merged.terpeneMatrix = payload.terpeneMatrix;
        if (payload.systemStatus) merged.systemStatus = { ...merged.systemStatus, ...payload.systemStatus };
        if (payload.learning && Object.keys(payload.learning.signalWeights || {}).length > 0) merged.learning = payload.learning;
        setData(merged);
      } else {
        setData(DEMO_DATA);
      }
    } catch {
      setData(DEMO_DATA);
      setDataError("Live snapshot unavailable — using demo data");
    }
  }, []);

  useEffect(() => { refreshSnapshot(); }, [refreshSnapshot]);

  const pollJob = useCallback(async (job_id) => {
    for (let i = 0; i < 120; i++) {
      await new Promise(r => setTimeout(r, 1000));
      try {
        const payload = await jfetch(`${API.job}?job_id=${encodeURIComponent(job_id)}`);
        setJobs(prev => { const next = prev.slice(); const idx = next.findIndex(j => j.job_id === job_id); if (idx >= 0) next[idx] = payload; else next.unshift(payload); return next.slice(0, 12); });
        if (payload.status && payload.status !== "running") { await refreshSnapshot(); return payload; }
      } catch { /* transient */ }
    }
    return null;
  }, [refreshSnapshot]);

  const runAgent = useCallback(async (command, company = "") => {
    try {
      showToast("info", `Queued: ${command}${company ? ` (${company})` : ""}`);
      const resp = await jfetch(API.run, { method: "POST", body: JSON.stringify({ command, company }) });
      const job_id = resp.job_id;
      setJobDrawerOpen(true);
      setJobs(prev => [{ job_id, run_key: command, status: "running", started_at: new Date().toISOString() }, ...prev].slice(0, 12));
      const final = await pollJob(job_id);
      if (final && final.status === "succeeded") showToast("success", `Completed: ${command}`);
      if (final && final.status === "failed") showToast("error", `Failed: ${command}`);
    } catch (e) { showToast("error", String(e.message || e)); }
  }, [pollJob, showToast]);

  const handleOutcome = useCallback(async (actionId, outcome) => {
    setOutcomes(prev => ({ ...prev, [actionId]: outcome }));
    try {
      await jfetch(API.outcome, { method: "POST", body: JSON.stringify({ action_id: actionId, outcome, notes: "" }) });
      showToast("success", `Outcome saved: ${outcome.toUpperCase()}`);
      await refreshSnapshot();
    } catch (e) { showToast("error", `Outcome not persisted (demo mode): ${String(e.message || e)}`); }
  }, [refreshSnapshot, showToast]);

  const uiData = useMemo(() => data || DEMO_DATA, [data]);

  const weightRows = useMemo(() => {
    const live = uiData.learning && uiData.learning.signalWeights;
    if (live && !Array.isArray(live) && typeof live === "object") {
      return Object.entries(live).map(([k, v]) => ({ signal: k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()), weight: Number(v) || 0 })).sort((a, b) => b.weight - a.weight).slice(0, 12);
    }
    return (uiData.signalWeights || []).slice(0, 12);
  }, [uiData]);

  const tabs = [
    { id: "priorities", label: "Priorities", icon: "◉" },
    { id: "competitors", label: "Competitors", icon: "⚔" },
    { id: "signals", label: "Signals", icon: "◈" },
    { id: "research", label: "Research", icon: "◎" },
    { id: "learning", label: "Learning", icon: "△" },
  ];

  const activeBundle = activeBundleKey ? DEMO_BUNDLES[activeBundleKey] : null;

  return (
    <div style={{ minHeight: "100vh", background: C.bg, color: C.text, fontFamily: C.font, opacity: loaded ? 1 : 0, transition: "opacity 0.6s ease" }}>
      <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet" />
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(197,165,90,0.3); border-radius: 3px; }
      `}</style>

      {/* Bundle Viewer Modal */}
      {activeBundle && <BundleViewer bundle={activeBundle} onClose={() => setActiveBundleKey(null)} />}

      {/* Header */}
      <div style={{ padding: "28px 40px 20px", borderBottom: `1px solid ${C.borderGold}` }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: C.green, animation: "pulse 2s infinite" }} />
              <h1 style={{ margin: 0, fontSize: 26, fontWeight: 900, fontFamily: C.fontDisplay, letterSpacing: -0.5 }}>
                <span style={{ color: C.gold }}>NEXUS</span>
                <span style={{ color: "#555", fontWeight: 400, fontSize: 18, marginLeft: 10 }}>REEF MODE</span>
              </h1>
            </div>
            <div style={{ fontSize: 12, color: "#555", marginTop: 6, marginLeft: 20 }}>
              Terpene Belt Farms — Daily Intelligence Briefing — {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
            </div>
          </div>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            <div style={{ fontSize: 10, color: "#555", textAlign: "right", marginRight: 8 }}>
              {dataError ? <span style={{ color: "#9B3C3C" }}>{dataError}</span> : <span style={{ color: C.green }}>Live snapshot</span>}
            </div>
            <button onClick={() => refreshSnapshot()} style={{
              padding: "8px 10px", borderRadius: 8, border: `1px solid ${C.borderGold}`,
              background: C.goldBg, color: C.gold, cursor: "pointer", fontSize: 12, fontWeight: 700,
            }}>Refresh</button>
            <button onClick={() => setJobDrawerOpen(true)} style={{
              padding: "8px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.10)",
              background: "rgba(255,255,255,0.03)", color: "#AAA", cursor: "pointer", fontSize: 12, fontWeight: 700,
            }}>Jobs ({jobs.length})</button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <StatCard label="Entities" value={uiData.systemStatus?.entitiesTracked ?? uiData.systemStatus?.entities ?? 0} sub="companies + contacts" />
          <StatCard label="Signals" value={uiData.systemStatus?.signalsToday ?? uiData.systemStatus?.signals ?? 0} sub="last 24h" />
          <StatCard label="Actions" value={uiData.systemStatus?.actionsQueued ?? uiData.systemStatus?.learningStats?.actionsTracked ?? 0} sub="queued/executed" />
          <StatCard label="Outcomes" value={uiData.systemStatus?.outcomesRecordedToday ?? Object.keys(outcomes).length} sub="today" />
          <StatCard label="Competitors" value={uiData.systemStatus?.competitorsTracked ?? uiData.competitors?.length ?? 0} sub="monitored" />
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div style={{ position: "fixed", top: 14, right: 14, zIndex: 50, padding: "10px 14px", borderRadius: 10,
          background: toast.kind === "success" ? "rgba(46,204,64,0.15)" : toast.kind === "error" ? "rgba(155,60,60,0.20)" : C.goldDim,
          border: "1px solid rgba(255,255,255,0.10)", color: C.text, fontSize: 12, maxWidth: 360 }}>
          <div style={{ fontWeight: 800, marginBottom: 2, color: toast.kind === "success" ? C.green : toast.kind === "error" ? "#E07171" : C.gold }}>
            {toast.kind === "success" ? "Success" : toast.kind === "error" ? "Error" : "Info"}
          </div>
          <div style={{ color: "#BBB" }}>{toast.message}</div>
        </div>
      )}

      {/* Job Drawer */}
      {jobDrawerOpen && (
        <div style={{ position: "fixed", top: 0, right: 0, height: "100vh", width: 420, background: "rgba(10,10,10,0.98)", borderLeft: `1px solid ${C.borderGold}`, zIndex: 40, padding: 16, overflow: "auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 900, color: C.gold }}>Jobs</div>
            <button onClick={() => setJobDrawerOpen(false)} style={{ background: "transparent", border: "none", color: "#AAA", cursor: "pointer" }}>✕</button>
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
            <button onClick={() => runAgent("war_room_brief")} style={{ padding: "8px 12px", borderRadius: 8, border: `1px solid ${C.borderGold}`, background: C.goldBg, color: C.gold, cursor: "pointer", fontSize: 11, fontWeight: 800 }}>Run War Room Brief</button>
            <button onClick={() => runAgent("daily")} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.10)", background: "rgba(255,255,255,0.03)", color: "#AAA", cursor: "pointer", fontSize: 11, fontWeight: 800 }}>Run Daily</button>
          </div>
          {jobs.length === 0 ? (
            <div style={{ color: C.textMuted, fontSize: 12 }}>No jobs yet.</div>
          ) : jobs.map(j => (
            <div key={j.job_id} style={{ padding: 10, marginBottom: 10, borderRadius: 10, border: `1px solid ${C.border}`, background: C.surface }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: C.text }}>{j.run_key || "job"}</div>
                <div style={{ fontSize: 11, color: j.status === "succeeded" ? C.green : j.status === "failed" ? "#E07171" : C.gold }}>{j.status || "running"}</div>
              </div>
              <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4, fontFamily: C.mono }}>{j.job_id}</div>
              {j.log_tail && <pre style={{ marginTop: 8, padding: 10, borderRadius: 8, background: "rgba(0,0,0,0.35)", color: C.textDim, fontSize: 10, whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>{j.log_tail}</pre>}
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, padding: "0 40px", borderBottom: `1px solid ${C.border}`, background: "rgba(0,0,0,0.3)" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            padding: "14px 24px", background: "transparent", border: "none",
            borderBottom: activeTab === t.id ? `2px solid ${C.gold}` : "2px solid transparent",
            color: activeTab === t.id ? C.gold : "#555", cursor: "pointer",
            fontSize: 13, fontWeight: 600, transition: "all 0.2s", letterSpacing: 0.5,
          }}><span style={{ marginRight: 6 }}>{t.icon}</span>{t.label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "24px 40px 60px", maxWidth: 1100 }}>

        {/* PRIORITIES TAB */}
        {activeTab === "priorities" && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: C.text, fontFamily: C.fontDisplay }}>Priority Accounts</h2>
                <p style={{ margin: "4px 0 0", fontSize: 12, color: C.textMuted }}>
                  Ranked by composite intelligence: pipeline score × signals × source reliability + competitor vulnerability + recency
                </p>
              </div>
              <div style={{ fontSize: 11, color: "#555", textAlign: "right" }}>
                {(uiData.priorities || []).filter(p => p.briefComplete).length}/{(uiData.priorities || []).length} briefed ·{" "}
                {(uiData.priorities || []).filter(p => p.bundleKey).length} bundles ready
              </div>
            </div>

            {(uiData.priorities || []).map((p, i) => (
              <AccountCard key={i} p={p} isExpanded={expandedCard === i} onToggle={() => setExpandedCard(expandedCard === i ? -1 : i)}
                onOutcome={handleOutcome} onRun={runAgent} onOpenBundle={(key) => setActiveBundleKey(key)} />
            ))}

            {Object.keys(outcomes).length > 0 && (
              <div style={{ marginTop: 20, padding: 16, background: "rgba(46,204,64,0.08)", border: "1px solid rgba(46,204,64,0.2)", borderRadius: 8 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: C.green, marginBottom: 8 }}>Outcomes Recorded</div>
                {Object.entries(outcomes).map(([id, outcome]) => {
                  const p = (uiData.priorities || []).find(p => p.actionId === id);
                  return (
                    <div key={id} style={{ fontSize: 12, color: C.textDim, marginBottom: 4 }}>
                      {p?.company}: <strong style={{ color: outcome === "closed" ? C.green : outcome === "meeting" ? C.blue : C.gold }}>{outcome.toUpperCase()}</strong>
                      <span style={{ color: "#555", marginLeft: 8 }}>→ Signal weights adjusting</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* COMPETITORS TAB */}
        {activeTab === "competitors" && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>
            <h2 style={{ margin: "0 0 16px", fontSize: 20, fontWeight: 700, fontFamily: C.fontDisplay }}>Competitor Vulnerability Map</h2>
            <p style={{ fontSize: 12, color: C.textMuted, marginBottom: 20 }}>7 competitors tracked via Trustpilot, hiring signals, news, and Reddit complaints</p>

            {(uiData.competitors || []).map((c, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", padding: "14px 20px", marginBottom: 6,
                background: c.risk === "HIGH" ? "rgba(255,65,54,0.06)" : C.surface,
                border: `1px solid ${c.risk === "HIGH" ? "rgba(255,65,54,0.2)" : C.border}`,
                borderRadius: 8, gap: 16,
              }}>
                <div style={{ width: 110, flexShrink: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{c.name}</div>
                </div>
                <div style={{ width: 70, textAlign: "center", flexShrink: 0 }}>
                  {c.trustpilot ? (
                    <div style={{ fontSize: 18, fontWeight: 800, color: c.trustpilot < 3.5 ? C.red : c.trustpilot < 4.0 ? C.orange : C.green, fontFamily: C.fontDisplay }}>
                      {c.trustpilot}<span style={{ fontSize: 11, color: "#555" }}>/5</span>
                    </div>
                  ) : <div style={{ fontSize: 11, color: C.textDark }}>No data</div>}
                </div>
                <div style={{
                  padding: "4px 12px", borderRadius: 4, fontSize: 10, fontWeight: 800,
                  background: `${riskColors[c.risk]}22`, color: riskColors[c.risk],
                  textTransform: "uppercase", letterSpacing: 1, flexShrink: 0,
                }}>{c.risk}</div>
                <div style={{ fontSize: 12, color: "#777", flex: 1 }}>{c.vulnerability}</div>
                {c.hiring && <div style={{ fontSize: 10, background: "rgba(0,116,217,0.15)", color: C.blue, padding: "3px 10px", borderRadius: 4, fontWeight: 600, flexShrink: 0 }}>HIRING</div>}
              </div>
            ))}

            <GoldDivider />
            <div style={{ fontSize: 12, color: C.textMuted }}>
              <strong style={{ color: C.gold }}>Displacement strategy:</strong> True Terpenes customers are the primary target. Lead with quality consistency, batch-to-batch reliability, and CDT pricing advantage. Peak Supply Co customers are secondary — lead with Trustpilot comparison and COA transparency.
            </div>
          </div>
        )}

        {/* SIGNALS TAB */}
        {activeTab === "signals" && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>
            <h2 style={{ margin: "0 0 16px", fontSize: 20, fontWeight: 700, fontFamily: C.fontDisplay }}>Active Signals</h2>

            <h3 style={{ fontSize: 14, color: C.gold, fontWeight: 700, marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>Reddit Intelligence</h3>
            {(uiData.redditSignals || []).map((s, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 12, padding: "10px 16px", marginBottom: 4,
                background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
              }}>
                <span style={{
                  fontSize: 9, fontWeight: 800, padding: "3px 8px", borderRadius: 3,
                  background: s.type.includes("SUPPLIER") ? "rgba(255,65,54,0.15)" : "rgba(255,255,255,0.05)",
                  color: s.type.includes("SUPPLIER") ? C.red : C.textMuted,
                  whiteSpace: "nowrap", textTransform: "uppercase", letterSpacing: 0.5,
                }}>{s.type}</span>
                <span style={{ fontSize: 11, color: "#888", flexShrink: 0 }}>r/{s.subreddit}</span>
                <span style={{ fontSize: 12, color: C.textDim, flex: 1 }}>{s.title}</span>
                <span style={{ fontSize: 11, color: "#555", fontFamily: C.mono, flexShrink: 0 }}>s={s.score}</span>
              </div>
            ))}

            <GoldDivider />

            <h3 style={{ fontSize: 14, color: C.gold, fontWeight: 700, marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>Competitor Signals</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {(uiData.competitors || []).filter(c => c.trustpilot && c.trustpilot < 4.0).map((c, i) => (
                <div key={i} style={{ padding: "12px 16px", background: "rgba(255,65,54,0.05)", border: "1px solid rgba(255,65,54,0.15)", borderRadius: 6 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: C.red }}>{c.name} — Trustpilot {c.trustpilot}/5</div>
                  <div style={{ fontSize: 11, color: "#888", marginTop: 4 }}>Active vulnerability. Look for their customers in pipeline.</div>
                </div>
              ))}
              {(uiData.competitors || []).filter(c => c.hiring).map((c, i) => (
                <div key={`h${i}`} style={{ padding: "12px 16px", background: "rgba(0,116,217,0.05)", border: "1px solid rgba(0,116,217,0.15)", borderRadius: 6 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: C.blue }}>{c.name} — Hiring Activity</div>
                  <div style={{ fontSize: 11, color: "#888", marginTop: 4 }}>May indicate growth, churn backfill, or strategy shift.</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* RESEARCH TAB — PhD-Grade Intelligence */}
        {activeTab === "research" && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>

            {/* ── THIS WEEK'S BETS (Epic 4.4 — Business Translation) ── */}
            {(uiData.businessInsights || []).filter(b => b.type === "weekly_bet").length > 0 && (<>
              <h2 style={{ margin: "0 0 4px", fontSize: 20, fontWeight: 700, fontFamily: C.fontDisplay }}>This Week's Bets</h2>
              <p style={{ fontSize: 12, color: C.textMuted, marginBottom: 16 }}>Evidence-backed commercial opportunities · compliance-safe framing · citation-backed</p>
              {(uiData.businessInsights || []).filter(b => b.type === "weekly_bet").slice(0, 4).map((bet, i) => (
                <div key={"bet"+i} style={{ padding: "16px 20px", marginBottom: 10, background: "linear-gradient(135deg, rgba(197,165,90,0.08), rgba(197,165,90,0.02))", border: "1px solid rgba(197,165,90,0.25)", borderRadius: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                        <span style={{ fontSize: 10, background: C.goldDim, color: C.gold, padding: "2px 10px", borderRadius: 4, fontWeight: 700 }}>{bet.terpene}</span>
                        <span style={{ fontSize: 10, color: C.textDim }}>{bet.category}</span>
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.5, marginBottom: 6 }}>{bet.safe_framing}</div>
                      <div style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.5 }}>
                        <div><strong style={{ color: C.gold }}>Product angle:</strong> {bet.product_angle}</div>
                        <div><strong style={{ color: C.gold }}>Sales angle:</strong> {bet.sales_angle}</div>
                        <div style={{ marginTop: 4, fontSize: 10, color: C.textDim }}>{bet.why_we_can_say_it}</div>
                      </div>
                    </div>
                    <div style={{ fontSize: 22, fontWeight: 800, color: bet.confidence >= 5 ? C.green : bet.confidence >= 3 ? C.gold : C.textDim, fontFamily: C.fontDisplay, flexShrink: 0 }}>{bet.confidence}<span style={{ fontSize: 10, color: C.textDim }}>/6</span></div>
                  </div>
                  {(bet.citations || []).length > 0 && (
                    <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {bet.citations.map((url, j) => (
                        <a key={j} href={url} target="_blank" rel="noopener" style={{ fontSize: 9, color: C.blue, textDecoration: "none" }}>PubMed [{j+1}]</a>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Trend alerts + R&D opportunities inline */}
              {(uiData.businessInsights || []).filter(b => b.type !== "weekly_bet").slice(0, 3).map((ins, i) => (
                <div key={"bi"+i} style={{ padding: "10px 16px", marginBottom: 6, background: C.surface, border: "1px solid " + C.border, borderRadius: 6, fontSize: 12 }}>
                  <span style={{ fontSize: 9, background: ins.type === "trend_alert" ? "rgba(0,116,217,0.15)" : "rgba(46,204,64,0.15)", color: ins.type === "trend_alert" ? C.blue : C.green, padding: "1px 6px", borderRadius: 3, fontWeight: 700, marginRight: 8 }}>{ins.type === "trend_alert" ? "TREND" : "R&D GAP"}</span>
                  <span style={{ color: C.text }}>{ins.safe_framing}</span>
                </div>
              ))}
              <GoldDivider />
            </>)}
            {(uiData.synthesisInsights || []).length > 0 && (<>
              <h2 style={{ margin: "0 0 4px", fontSize: 20, fontWeight: 700, fontFamily: C.fontDisplay }}>Research Convergences</h2>
              <p style={{ fontSize: 12, color: C.textMuted, marginBottom: 16 }}>Cross-paper synthesis — where multiple studies converge on the same terpene × effect × mechanism triple</p>
              {(uiData.synthesisInsights || []).slice(0, 6).map((ins, i) => {
                const confColor = ins.confidence_1to6 >= 5 ? C.green : ins.confidence_1to6 >= 3 ? C.gold : C.textDim;
                return (
                  <div key={i} style={{ padding: "14px 18px", marginBottom: 8, background: C.surface, border: `1px solid ${ins.contradiction ? "rgba(255,65,54,0.3)" : C.border}`, borderRadius: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.4 }}>{ins.statement}</div>
                        <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap", alignItems: "center" }}>
                          <span style={{ fontSize: 10, background: C.goldDim, color: C.gold, padding: "2px 8px", borderRadius: 4, fontWeight: 700 }}>{ins.terpene}</span>
                          <span style={{ fontSize: 10, background: "rgba(255,255,255,0.05)", color: C.textDim, padding: "2px 8px", borderRadius: 4 }}>{(ins.effect_category || "").replace(/_/g, " ")}</span>
                          {ins.mechanism && ins.mechanism !== "unknown_mechanism" && (
                            <span style={{ fontSize: 10, background: "rgba(0,116,217,0.15)", color: C.blue, padding: "2px 8px", borderRadius: 4 }}>{(ins.mechanism || "").replace(/_/g, " ")}</span>
                          )}
                          {ins.contradiction && (
                            <span style={{ fontSize: 10, background: "rgba(255,65,54,0.15)", color: C.red, padding: "2px 8px", borderRadius: 4 }}>⚠ mixed outcomes</span>
                          )}
                        </div>
                        {(ins.implications || []).length > 0 && (
                          <div style={{ fontSize: 11, color: C.textMuted, marginTop: 6, lineHeight: 1.5 }}>
                            {ins.implications.map((imp, j) => <div key={j}>→ {imp}</div>)}
                          </div>
                        )}
                      </div>
                      <div style={{ textAlign: "right", flexShrink: 0 }}>
                        <div style={{ fontSize: 22, fontWeight: 800, color: confColor, fontFamily: C.fontDisplay }}>{ins.confidence_1to6}<span style={{ fontSize: 10, color: C.textDim }}>/6</span></div>
                        <div style={{ fontSize: 9, color: C.textDim, marginTop: 2 }}>{ins.paper_count} papers · {ins.human_count} human</div>
                        <div style={{ fontSize: 9, color: C.textDim }}>{ins.positive}↑ {ins.negative}↓ {ins.neutral}—</div>
                      </div>
                    </div>
                  </div>
                );
              })}
              <GoldDivider />
            </>)}

            {/* ── TREND VELOCITY ── */}
            {uiData.researchTrends && !uiData.researchTrends.error && (<>
              <h3 style={{ fontSize: 14, color: C.gold, fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Trend Velocity (90-day)</h3>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
                {Object.entries(uiData.researchTrends.terpene_velocity_top || {}).slice(0, 8).map(([terp, v]) => (
                  <div key={terp} style={{ padding: "8px 12px", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, minWidth: 120 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{terp}</div>
                    <div style={{ fontSize: 18, fontWeight: 800, fontFamily: C.fontDisplay, color: v.velocity > 0.2 ? C.green : v.velocity < -0.2 ? C.red : C.textDim }}>{v.velocity > 0 ? "+" : ""}{v.velocity}</div>
                    <div style={{ fontSize: 9, color: C.textDim }}>{v.recent_count} recent · {v.trend}</div>
                  </div>
                ))}
              </div>
              {uiData.researchTrends.rigor && (
                <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 16 }}>
                  Evidence rigor: human study rate {uiData.researchTrends.rigor.human_rate_change > 0 ? "↑" : "↓"} {Math.abs(uiData.researchTrends.rigor.human_rate_change * 100).toFixed(1)}% ({(uiData.researchTrends.rigor.human_rate_recent * 100).toFixed(0)}% of recent papers include human data)
                </div>
              )}
              <GoldDivider />
            </>)}

            {/* ── TOP PAPERS (real data) ── */}
            <h3 style={{ fontSize: 14, color: C.gold, fontWeight: 700, marginBottom: 4, textTransform: "uppercase", letterSpacing: 1 }}>Top Papers by Relevance</h3>
            <p style={{ fontSize: 11, color: C.textMuted, marginBottom: 12 }}>
              {uiData.systemStatus?.researchPapers || (uiData.researchHighlights || []).length} papers indexed · evidence-graded · ranked by commercial relevance
            </p>

            {(uiData.researchHighlights || []).slice(0, 10).map((r, i) => {
              const _gc = {"A": C.green, "B": C.gold, "C": C.blue, "D": C.textDim};
              const _gl = {"A": "Human/RCT", "B": "Cohort", "C": "Animal/In-vitro", "D": "Review"};
              const gradeColor = _gc[r.evidenceGrade] || C.textDim;
              const gradeLabel = _gl[r.evidenceGrade] || r.studyType || "";
              return (
                <div key={i} style={{ padding: "14px 18px", marginBottom: 6, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, cursor: r.url ? "pointer" : "default" }}
                  onClick={() => r.url && window.open(r.url, "_blank")}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.4 }}>{r.title}</div>
                      <div style={{ fontSize: 11, color: C.textMuted, marginTop: 3 }}>
                        {r.journal} · {r.year}
                        {r.modelOrganism && r.modelOrganism !== "unknown" && <span> · {r.modelOrganism}</span>}
                        {r.outcomeDirection && r.outcomeDirection !== "unknown" && (
                          <span style={{ color: r.outcomeDirection === "positive" ? C.green : r.outcomeDirection === "negative" ? C.red : C.textDim }}> · {r.outcomeDirection}</span>
                        )}
                      </div>
                    </div>
                    <div style={{ textAlign: "right", flexShrink: 0 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: r.score >= 80 ? C.red : r.score >= 60 ? C.gold : C.blue, fontFamily: C.fontDisplay }}>{r.score}</div>
                      <div style={{ fontSize: 9, padding: "1px 6px", background: gradeColor + "22", color: gradeColor, borderRadius: 3, fontWeight: 700, marginTop: 2 }}>{r.evidenceGrade || "?"} · {gradeLabel}</div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 5, marginTop: 8, flexWrap: "wrap" }}>
                    {(r.terpenes || []).map((t, j) => (
                      <span key={j} style={{ fontSize: 10, background: C.goldDim, color: C.gold, padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>{t}</span>
                    ))}
                    {(r.mechanisms || []).slice(0, 2).map((m, j) => (
                      <span key={"m"+j} style={{ fontSize: 10, background: "rgba(0,116,217,0.12)", color: C.blue, padding: "2px 8px", borderRadius: 4 }}>{m.replace(/_/g, " ")}</span>
                    ))}
                    {(r.commercialTags || []).slice(0, 2).map((ct, j) => (
                      <span key={"ct"+j} style={{ fontSize: 10, background: "rgba(46,204,64,0.12)", color: C.green, padding: "2px 8px", borderRadius: 4 }}>{ct.replace(/_/g, " ")}</span>
                    ))}
                  </div>
                </div>
              );
            })}

            {/* ── REGULATORY RADAR ── */}
            {(uiData.regulatoryHits || []).length > 0 && (<>
              <GoldDivider />
              <h3 style={{ fontSize: 14, color: C.red, fontWeight: 700, marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>Regulatory Radar</h3>
              {(uiData.regulatoryHits || []).slice(0, 5).map((h, i) => (
                <div key={i} style={{ fontSize: 11, color: C.textMuted, marginBottom: 6, paddingLeft: 12, borderLeft: `2px solid ${C.red}` }}>
                  <span style={{ color: C.text, fontWeight: 600 }}>{h.title}</span>
                  <span style={{ color: C.textDim }}> · {(h.topics || []).join(", ")}</span>
                </div>
              ))}
            </>)}

            <GoldDivider />
            <div style={{ fontSize: 12, color: C.textMuted }}>
              <strong style={{ color: C.gold }}>Engine:</strong> 10 subagents · evidence grading (A-D) · synthesis convergence · trend velocity · effect profiling · gap analysis · regulatory radar
            </div>
          </div>
        )}

        {/* LEARNING TAB */}
        {activeTab === "learning" && (
          <div style={{ animation: "fadeIn 0.3s ease" }}>
            <h2 style={{ margin: "0 0 4px", fontSize: 20, fontWeight: 700, fontFamily: C.fontDisplay }}>Learning Engine</h2>
            <p style={{ fontSize: 12, color: C.textMuted, marginBottom: 20 }}>Signal weights adjust automatically based on outcomes. Positive outcomes boost the signals that triggered the recommendation.</p>

            <h3 style={{ fontSize: 14, color: C.gold, fontWeight: 700, marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>Signal Weights (Current)</h3>
            <div style={{ marginBottom: 24 }}>
              {weightRows.map((s, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                  <div style={{ width: 200, fontSize: 12, color: C.textDim, textAlign: "right", flexShrink: 0 }}>{s.signal}</div>
                  <div style={{ flex: 1, height: 20, background: "rgba(255,255,255,0.04)", borderRadius: 4, overflow: "hidden" }}>
                    <div style={{
                      width: `${Math.min(100, (s.weight / 25) * 100)}%`, height: "100%",
                      background: `linear-gradient(90deg, rgba(197,165,90,0.4), rgba(197,165,90,0.8))`,
                      borderRadius: 4, transition: "width 0.5s ease",
                    }} />
                  </div>
                  <div style={{ width: 36, fontSize: 12, color: C.gold, fontWeight: 700, fontFamily: C.mono, textAlign: "right", flexShrink: 0 }}>{s.weight}</div>
                </div>
              ))}
            </div>

            <GoldDivider />

            <h3 style={{ fontSize: 14, color: C.gold, fontWeight: 700, marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>How It Works</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
              {[
                { step: "1", title: "Signals Collected", desc: "Reddit, Trustpilot, PubMed, news, competitor websites — all fed into the knowledge graph daily" },
                { step: "2", title: "Actions Recommended", desc: "Decision engine cross-pollinates intelligence and ranks companies. Each action links to its trigger signals." },
                { step: "3", title: "Outcomes Recorded", desc: "When you get a reply, meeting, or close — record it. Signal weights adjust: winners get amplified, losers get dampened." },
              ].map((s, i) => (
                <div key={i} style={{ padding: "16px", background: "rgba(197,165,90,0.05)", border: `1px solid ${C.goldDim}`, borderRadius: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 900, color: C.gold, fontFamily: C.fontDisplay, marginBottom: 8 }}>{s.step}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>{s.title}</div>
                  <div style={{ fontSize: 11, color: "#777", lineHeight: 1.6 }}>{s.desc}</div>
                </div>
              ))}
            </div>

            {Object.keys(outcomes).length > 0 && (
              <>
                <GoldDivider />
                <div style={{ padding: 16, background: "rgba(46,204,64,0.06)", border: "1px solid rgba(46,204,64,0.15)", borderRadius: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: C.green, marginBottom: 8 }}>Live Weight Updates</div>
                  <div style={{ fontSize: 12, color: C.textDim }}>
                    {Object.keys(outcomes).length} outcomes recorded this session. Signal weights are recalculating.
                    In production, run <code style={{ color: C.gold, fontFamily: C.mono, fontSize: 11 }}>python3 war_room.py learn --action-id ID --outcome reply</code> to persist.
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0, padding: "10px 40px",
        background: "linear-gradient(transparent, #0A0A0A 40%)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        fontSize: 10, color: "#333", pointerEvents: "none",
      }}>
        <span>NEXUS BDR v5 — 19 scripts · 13,400+ lines · Kill Shot Bundle + 5 Playbooks</span>
        <span>War Room v2 — Source reliability · Learning attribution · Playbook engine</span>
      </div>
    </div>
  );
}
