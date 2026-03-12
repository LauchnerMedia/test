const { useState, useEffect, useCallback, useMemo, useRef } = React;

// ═══════════════════════════════════════════════════════════
// NEXUS BDR — Unified Intelligence Dashboard
// Pitch-ready single interface combining all agent intelligence
// ═══════════════════════════════════════════════════════════

// ─── THEME ───
const C = {
  gold: "#C5A55A", goldDim: "#9a7d3a", goldGlow: "rgba(197,165,90,0.15)",
  bg: "#06060d", void: "#020208", surface: "#0d0d1a", surface2: "#14142a",
  border: "#1a1a2e", borderHover: "#2a2a4e",
  text: "#e8e8f0", dim: "#666680", muted: "#444460",
  hot: "#ff2d2d", warm: "#ff8c00", cool: "#2d7fff", cold: "#555570",
  green: "#00e09a", red: "#ef4444",
  tbf: "#C5A55A", dft: "#ff3333",
};

const FONT = { display: "'JetBrains Mono', monospace", body: "'Outfit', sans-serif" };

// ─── DEMO DATA (fallback when API unavailable) ───
const DEMO_COMPANIES = [
  { name:"Mellow Fellow", contacts:25, score:96, brand:"DFT", region:"FL", domain:"mellowfellow.fun", topPerson:"JJ Coombs (PharmD)", topTitle:"CEO", emails:3, products:"Vapes · Edibles · THCa · Beverages", intel:"#1 target. Pharmacist-founded. Self-extracts CDT at Arvida Labs. 40+ states. 3.0/5 Trustpilot = quality issues. Federal THC ban = existential threat. Good Fellows coalition (Urb, Zombi, Pushin P's) = 4 accounts.", briefStatus:"complete", tier:"hot", currentSupplier:"True Terpenes" },
  { name:"Urb", contacts:0, score:90, brand:"DFT", region:"US", domain:"urbextracts.com", topPerson:"TBD", topTitle:"", emails:0, products:"Vapes · Gummies · Disposables", intel:"Good Fellows coalition member. Warm intro via Mellow Fellow.", briefStatus:"pending", tier:"hot" },
  { name:"Zombi", contacts:0, score:88, brand:"DFT", region:"US", domain:"zombibrand.com", topPerson:"TBD", topTitle:"", emails:0, products:"Vapes · Edibles · Delta-8", intel:"Good Fellows coalition member. Warm intro via Mellow Fellow.", briefStatus:"pending", tier:"hot" },
  { name:"Pushin P's", contacts:0, score:86, brand:"DFT", region:"US", domain:"pushinps.com", topPerson:"TBD", topTitle:"", emails:0, products:"Vapes · Concentrates", intel:"Good Fellows coalition member. Warm intro via Mellow Fellow.", briefStatus:"pending", tier:"hot" },
  { name:"Alpha Brands", contacts:1, score:100, brand:"DFT", region:"US", domain:"alphabrands.co", topPerson:"J. Lazoff (CEO)", topTitle:"CEO", emails:1, products:"Multi-brand", intel:"Multi-brand operator. Single decision maker. High intent.", briefStatus:"pending", tier:"hot" },
  { name:"CBD Alchemy", contacts:10, score:88, brand:"DFT", region:"ES", domain:"cbdalchemy.com", topPerson:"Django (CEO)", topTitle:"CEO", emails:2, products:"CBD Oils · Topicals", intel:"Spanish CBD brand. European market entry for DFT.", briefStatus:"pending", tier:"warm" },
  { name:"Cannvital", contacts:8, score:85, brand:"TBF", region:"DE", domain:"cannvital.de", topPerson:"TBD", topTitle:"", emails:1, products:"CBD · Wellness", intel:"German wellness brand. TBF enterprise fit for EU scale.", briefStatus:"pending", tier:"warm" },
  { name:"A-Sense", contacts:18, score:73, brand:"DFT", region:"PL", domain:"a-sense.com", topPerson:"TBD", topTitle:"", emails:16, products:"Extraction · Terpenes", intel:"Polish extraction company. Strong email coverage.", briefStatus:"pending", tier:"warm" },
];

const DEMO_AGENTS = [
  { name:"Sales Intel Brief v4", status:"active", desc:"6-phase AI research + cost optimization", file:"sales_intel_brief_v4.py", lines:506 },
  { name:"Free Intel Harvester", status:"active", desc:"Reddit, FDA, news — zero API cost", file:"free_intel_sources.py", lines:516 },
  { name:"Model Router", status:"active", desc:"Claude ↔ OpenRouter, 40-60% cost savings", file:"model_router.py", lines:401 },
  { name:"Social Intel v2", status:"active", desc:"Intent-driven social monitoring across 6 platforms", file:"social_intel_engine_v2.py", lines:1257 },
  { name:"War Room", status:"active", desc:"Knowledge graph + signal processing + learning", file:"war_room.py", lines:1067 },
  { name:"Competitor Intel v2", status:"ready", desc:"7+ competitors tracked, displacement playbooks", file:"competitor_vuln_v2.py", lines:748 },
  { name:"Trigger Monitor", status:"ready", desc:"Buying signals across 10+ event types", file:"trigger_monitor.py", lines:650 },
  { name:"Kill Shot Bundle", status:"ready", desc:"One-command complete outreach package", file:"kill_shot_bundle.py", lines:700 },
  { name:"Apollo Pipeline", status:"deployed", desc:"Lead discovery → scoring → CRM import", file:"apollo_pipeline.py", lines:1056 },
  { name:"GHL Sync v2", status:"deployed", desc:"53-field CRM architecture + automation", file:"ghl_sync_v2.py", lines:656 },
  { name:"Enrichment Pipeline v2", status:"deployed", desc:"Email verification + data enrichment", file:"enrich_pipeline_v2.py", lines:727 },
  { name:"HeyGen Scripts", status:"ready", desc:"1 recording → 50+ personalized videos", file:"heygen_scripts.py", lines:391 },
  { name:"Customer Intel", status:"standby", desc:"Churn, upsell, reactivation engine", file:"customer_intel.py", lines:629 },
  { name:"Terpene Research v2", status:"active", desc:"PubMed, patents, FDA — cumulative knowledge base", file:"terpene_research_v2.py", lines:869 },
  { name:"Master Orchestrator", status:"active", desc:"CLI entry point for entire system", file:"nexus.py", lines:543 },
];

const DEMO_PIPELINE = { total:138, hot:61, warm:32, cool:28, cold:17, companies:22, verified:37 };

const DEMO_COMPETITORS = [
  { name:"True Terpenes", trustpilot:3.0, risk:"HIGH", vulnerability:"Batch consistency complaints, 3.0 Trustpilot, pricing pressure" },
  { name:"Abstrax", trustpilot:4.2, risk:"MEDIUM", vulnerability:"Premium pricing, limited botanical line" },
  { name:"Floraplex", trustpilot:3.8, risk:"MEDIUM", vulnerability:"Quality inconsistency reports, limited product education" },
  { name:"Denver Terpenes", trustpilot:3.5, risk:"MEDIUM", vulnerability:"Small operation, fulfillment delays reported" },
  { name:"Peak Supply", trustpilot:3.2, risk:"HIGH", vulnerability:"Price-focused, quality concerns in forums" },
  { name:"Terps USA", trustpilot:2.8, risk:"HIGH", vulnerability:"Multiple Reddit complaints, suspected synthetic" },
  { name:"Mr Extractor", trustpilot:3.1, risk:"HIGH", vulnerability:"Consumer-grade positioning, B2B credibility gap" },
];

const DEMO_BUNDLES = {
  "mellow_fellow": {
    company: "Mellow Fellow",
    generatedAt: "2026-03-04T06:21:00Z",
    playbook: "COMPETITOR_STRIKE",
    confidence: "HIGH",
    artifacts: {
      whyNow: "## Why Mellow Fellow, Why Now\n\n**Trigger Signals:**\n- True Terpenes (current supplier) at 3.0/5 Trustpilot — below displacement threshold\n- 3 switching triggers identified: batch consistency, CDT pricing pressure, scaling supply needs\n- Federal hemp THC ban creates existential threat to CDT-dependent product lines\n\n**Switch Economics:**\n- Current CDT cost: ~$5,000-8,000/L for premium\n- DFT Botanical alternative: $45-80/L\n- Potential savings: $95K+ annually on non-vape lines\n\n**Decision Maker:**\n- JJ Coombs, PharmD (CEO) — science-driven, will respond to data\n- Pharmacist background = values quality documentation + COAs",
      email: "Subject: The math on your terpene spend (from a fellow formulator)\n\nJJ,\n\nI noticed Mellow Fellow is scaling into beverages and edibles — congrats on the expansion.\n\nQuick question: are you still running CDT across all product lines? I ask because we work with brands doing 40+ state distribution (like yours) who've found that for non-vape applications, consumers can't distinguish CDT from properly profiled botanicals.\n\nThe math: brands your size typically spend $100K+/yr on terpenes. Converting edible + beverage lines to botanical profiles reclaims 90%+ of that margin without any consumer-perceptible difference.\n\nWe're Terpene Belt Farms — our botanical profiles are built by extraction chemists, not flavor houses. Every lot comes with full COA + terpene analysis.\n\nWorth a 15-minute call to see if the numbers work for Mellow Fellow?\n\nBest,\n[Name]\nDuty Free Terpenes",
      linkedin: "JJ — saw Mellow Fellow is pushing into beverages. Smart move.\n\nQuick thought: brands scaling into non-vape categories are finding 25-100x margin improvement by switching those specific lines to botanical terpene profiles. The science is clear that consumer perception is identical for edibles/beverages/topicals.\n\nWould love to share the data. Mind if I send over a quick analysis specific to MF's product mix?",
      callOpener: "Hey JJ, this is [Name] from Duty Free Terpenes. I'll be quick — I know you're busy scaling Mellow Fellow.\n\nReason I'm calling: we work with brands doing multi-state distribution like yours, and I noticed you're expanding into beverages and edibles. Most brands your size are spending $100K+ a year on terpenes, and we've been helping similar companies reclaim 90% of that margin on non-vape lines by switching to pharmaceutical-grade botanical profiles.\n\n**If they push back:** Totally get it — I'd be skeptical too. That's why we send free evaluation kits with full COAs. You can run your own blind tests. The data speaks for itself.\n\n**If they're interested:** Great — I'd love to send over a custom analysis for Mellow Fellow's product mix. What's the best email?",
      heygenScript: "Hey JJ — I put this together specifically for Mellow Fellow.\n\nI noticed you're scaling into beverages and edibles across 40+ states. That's exciting.\n\nHere's what caught my attention: brands your size typically spend over $100K a year on terpenes. But for non-vape applications — edibles, beverages, topicals — consumers genuinely cannot distinguish CDT from properly profiled botanicals.\n\nWe've helped brands similar to yours reclaim 90% of their terpene spend on those product lines. And every lot comes with full COA and terpene analysis from our extraction chemists.\n\nI'd love to send you a free evaluation kit so you can run your own tests. Would that be worth exploring?",
      competitorWedge: "## Competitor Displacement: True Terpenes → DFT\n\n**Current Supplier Profile:**\n- True Terpenes: 3.0/5 Trustpilot (below industry avg)\n- Known issues: batch consistency, pricing opacity, slow support\n\n**Displacement Strategy:**\n1. Lead with economics (not quality attacks)\n2. Position as \"addition\" not \"replacement\" initially\n3. Free evaluation kit — let product speak\n4. Target non-vape lines first (lowest switching risk)\n\n**2-Week Switch Timeline:**\n- Day 1-3: Evaluation kit ships + COA documentation\n- Day 4-7: JJ runs internal blind tests\n- Day 8-10: Custom profile matching to existing formulations\n- Day 11-14: First production order (edible/beverage lines only)",
    }
  }
};

const PRICING = {
  cdt_premium: "$5,000–8,000/L",
  cdt_self_extract: "$1,500–3,000/L",
  botanical_dft: "$45–80/L",
};

const BOOT_LINES = [
  { text: "NEXUS BDR SYSTEM v5.0 — INITIALIZING", color: C.gold },
  { text: "Loading agent fleet... 15 agents / 12,000+ lines", color: C.text },
  { text: "Pipeline data: 138 contacts / 22 companies / 61 hot", color: C.green },
  { text: "Model Router: Anthropic ✓  OpenRouter ✓", color: C.text },
  { text: "War Room: 53 entities / 35 signal types / learning active", color: C.green },
  { text: "Free Intel: Reddit ✓  FDA ✓  PubMed ✓  Google Trends ✓", color: C.green },
  { text: "CRM Sync: GoHighLevel ✓  53 custom fields deployed", color: C.green },
  { text: "Research KB: terpene knowledge base loaded", color: C.text },
  { text: "Kill Shot Bundles: 3 demo packages ready", color: C.warm },
  { text: "Signal taxonomy: 15 types / decay + reliability scoring", color: C.text },
  { text: "SYSTEM ONLINE — All agents operational", color: C.green },
];

const TICKER_ITEMS = [
  "138 contacts scored and imported to GHL (96% success)",
  "Mellow Fellow brief COMPLETE — 6-phase intel + outreach ready",
  "Good Fellows coalition: Urb + Zombi + Pushin P's = $150-350K pipeline",
  "Federal hemp THC ban — existential threat = botanical opportunity",
  "Model Router saves 40-60% on every brief ($0.40 vs $1.00+)",
  "50% of intelligence gathered at zero API cost (Reddit, PubMed, FDA)",
  "HeyGen: 1 recording → 50+ personalized video outreach",
  "Signal learning: weights adjust based on real deal outcomes",
];

// ─── UTILITY COMPONENTS ───

function Badge({ color, children }) {
  return (
    <span style={{ display:"inline-block", padding:"2px 8px", borderRadius:4, fontSize:10, fontWeight:700, fontFamily:FONT.display, letterSpacing:"0.05em", background:`${color}18`, color, border:`1px solid ${color}30` }}>
      {children}
    </span>
  );
}

function StatCard({ value, label, color }) {
  return (
    <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:10, padding:"14px 12px", textAlign:"center", transition:"all 0.3s" }}>
      <div style={{ fontSize:28, fontWeight:800, color, fontFamily:FONT.display }}>{value}</div>
      <div style={{ fontSize:10, color:C.dim, textTransform:"uppercase", letterSpacing:"0.1em", marginTop:2 }}>{label}</div>
    </div>
  );
}

function PipelineBar({ stats }) {
  const segs = [
    { label:"HOT", count:stats.hot, color:C.hot, pct:Math.round(stats.hot/stats.total*100) },
    { label:"WARM", count:stats.warm, color:C.warm, pct:Math.round(stats.warm/stats.total*100) },
    { label:"COOL", count:stats.cool, color:C.cool, pct:Math.round(stats.cool/stats.total*100) },
    { label:"COLD", count:stats.cold, color:C.cold, pct:Math.round(stats.cold/stats.total*100) },
  ];
  return (
    <div>
      <div style={{ display:"flex", height:40, borderRadius:8, overflow:"hidden", gap:2, marginBottom:8 }}>
        {segs.map(s => (
          <div key={s.label} style={{ width:`${s.pct}%`, background:s.color, display:"flex", alignItems:"center", justifyContent:"center", transition:"width 0.8s", minWidth:s.count > 0 ? 44 : 0 }}>
            <span style={{ fontWeight:800, fontSize:14, color:"#000", fontFamily:FONT.display }}>{s.count}</span>
          </div>
        ))}
      </div>
      <div style={{ display:"flex", gap:6 }}>
        {segs.map(s => (
          <div key={s.label} style={{ flex:1, textAlign:"center", padding:"5px 0", borderRadius:6, background:`${s.color}12`, border:`1px solid ${s.color}25` }}>
            <div style={{ fontSize:11, color:s.color, fontWeight:700, fontFamily:FONT.display }}>{s.label}</div>
            <div style={{ fontSize:10, color:C.dim }}>{s.pct}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── TAB: DASHBOARD (Overview) ───

function DashboardTab({ companies, pipeline, competitors, snapshot }) {
  const systemStatus = snapshot?.systemStatus || {};
  return (
    <div style={{ padding:24, overflow:"auto", height:"100%" }}>
      {/* Stats Row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(130px, 1fr))", gap:12, marginBottom:24 }}>
        <StatCard value={pipeline.total} label="Total Contacts" color={C.gold} />
        <StatCard value={pipeline.hot} label="Hot" color={C.hot} />
        <StatCard value={pipeline.warm} label="Warm" color={C.warm} />
        <StatCard value={pipeline.cool} label="Cool" color={C.cool} />
        <StatCard value={pipeline.companies} label="Companies" color={C.gold} />
        <StatCard value={pipeline.verified} label="Verified" color={C.green} />
      </div>

      {/* Pipeline Bar */}
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginBottom:24 }}>
        <div style={{ display:"flex", justifyContent:"space-between", marginBottom:12 }}>
          <span style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display }}>PIPELINE DISTRIBUTION</span>
          <span style={{ color:C.dim, fontSize:12 }}>{pipeline.verified} verified emails · {pipeline.total} in CRM</span>
        </div>
        <PipelineBar stats={pipeline} />
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20 }}>
        {/* Coalition Card */}
        <div style={{ background:C.surface, border:`1px solid ${C.gold}40`, borderRadius:12, padding:20 }}>
          <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:4 }}>GOOD FELLOWS COALITION</div>
          <div style={{ color:C.dim, fontSize:12, marginBottom:12 }}>Land Mellow Fellow → warm intro to 3 brands</div>
          {[
            { name:"Mellow Fellow", status:"BRIEF COMPLETE", color:C.green, value:"$14-96K/yr" },
            { name:"Urb", status:"WARM INTRO", color:C.warm, value:"$20-60K/yr" },
            { name:"Zombi", status:"WARM INTRO", color:C.warm, value:"$15-45K/yr" },
            { name:"Pushin P's", status:"WARM INTRO", color:C.warm, value:"$10-30K/yr" },
          ].map(b => (
            <div key={b.name} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"8px 0", borderBottom:`1px solid ${C.border}` }}>
              <span style={{ color:C.text, fontWeight:600, fontSize:13 }}>{b.name}</span>
              <div style={{ display:"flex", gap:10, alignItems:"center" }}>
                <Badge color={b.color}>{b.status}</Badge>
                <span style={{ color:C.text, fontWeight:700, fontSize:13, fontFamily:FONT.display }}>{b.value}</span>
              </div>
            </div>
          ))}
          <div style={{ marginTop:14, padding:14, background:`${C.gold}10`, borderRadius:8, textAlign:"center" }}>
            <div style={{ fontSize:10, color:C.dim, textTransform:"uppercase", letterSpacing:"0.1em" }}>Total Coalition Pipeline</div>
            <div style={{ fontSize:28, fontWeight:800, color:C.gold, fontFamily:FONT.display }}>$150K–$350K/yr</div>
          </div>
        </div>

        {/* Competitor Grid */}
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20 }}>
          <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:12 }}>COMPETITOR VULNERABILITY</div>
          {competitors.map(c => (
            <div key={c.name} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"7px 0", borderBottom:`1px solid ${C.border}40` }}>
              <div>
                <span style={{ color:C.text, fontWeight:600, fontSize:13 }}>{c.name}</span>
                <div style={{ color:C.dim, fontSize:11, marginTop:1 }}>{c.vulnerability?.substring(0, 50)}...</div>
              </div>
              <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                <span style={{ fontFamily:FONT.display, fontSize:12, color: c.trustpilot < 3.5 ? C.red : c.trustpilot < 4.0 ? C.warm : C.dim }}>{c.trustpilot}/5</span>
                <Badge color={c.risk === "HIGH" ? C.red : C.warm}>{c.risk}</Badge>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pricing */}
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginTop:20 }}>
        <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:14 }}>CDT vs BOTANICAL ECONOMICS</div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:14, marginBottom:16 }}>
          <div style={{ textAlign:"center", padding:16, background:`${C.hot}08`, borderRadius:8, border:`1px solid ${C.hot}25` }}>
            <div style={{ fontSize:20, fontWeight:800, color:C.hot, fontFamily:FONT.display }}>{PRICING.cdt_premium}</div>
            <div style={{ fontSize:10, color:C.dim, marginTop:4, textTransform:"uppercase" }}>Premium CDT (Market)</div>
          </div>
          <div style={{ textAlign:"center", padding:16, background:`${C.warm}08`, borderRadius:8, border:`1px solid ${C.warm}25` }}>
            <div style={{ fontSize:20, fontWeight:800, color:C.warm, fontFamily:FONT.display }}>{PRICING.cdt_self_extract}</div>
            <div style={{ fontSize:10, color:C.dim, marginTop:4, textTransform:"uppercase" }}>Self-Extraction</div>
          </div>
          <div style={{ textAlign:"center", padding:16, background:`${C.green}08`, borderRadius:8, border:`1px solid ${C.green}25` }}>
            <div style={{ fontSize:20, fontWeight:800, color:C.green, fontFamily:FONT.display }}>{PRICING.botanical_dft}</div>
            <div style={{ fontSize:10, color:C.dim, marginTop:4, textTransform:"uppercase" }}>DFT Botanical</div>
          </div>
        </div>
        <div style={{ fontSize:13, color:C.text, lineHeight:1.6 }}>
          <strong style={{ color:C.gold }}>The pitch:</strong> For non-flagship products (edibles, beverages, wellness, topicals), consumers cannot distinguish CDT from botanical. A brand spending $100K/yr on terpenes can reclaim <strong style={{ color:C.green }}>$95K+ in margin</strong> by converting non-vape lines to DFT botanical blends.
        </div>
      </div>
    </div>
  );
}

// ─── TAB: PIPELINE (Target Accounts) ───

function PipelineTab({ companies }) {
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let list = companies;
    if (filter !== "ALL") {
      if (filter === "TBF" || filter === "DFT") list = list.filter(c => c.brand === filter);
      else list = list.filter(c => c.tier === filter.toLowerCase());
    }
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(c => c.name.toLowerCase().includes(q) || c.domain?.toLowerCase().includes(q) || c.topPerson?.toLowerCase().includes(q));
    }
    return list;
  }, [companies, filter, search]);

  return (
    <div style={{ padding:24, overflow:"auto", height:"100%" }}>
      {/* Filters */}
      <div style={{ display:"flex", gap:8, marginBottom:20, flexWrap:"wrap", alignItems:"center" }}>
        {["ALL","HOT","WARM","COOL","COLD","TBF","DFT"].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            background: filter === f ? C.gold : C.surface,
            color: filter === f ? C.void : C.dim,
            border:`1px solid ${filter === f ? C.gold : C.border}`,
            padding:"6px 14px", borderRadius:6, cursor:"pointer", fontSize:11, fontWeight:700,
            fontFamily:FONT.display, letterSpacing:"0.05em", transition:"all 0.2s"
          }}>{f}</button>
        ))}
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search companies..."
          style={{ background:C.surface, border:`1px solid ${C.border}`, color:C.text, padding:"6px 14px", borderRadius:6, fontSize:13, fontFamily:FONT.body, outline:"none", width:220, marginLeft:"auto" }} />
      </div>

      {/* Cards Grid */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(350px, 1fr))", gap:14 }}>
        {filtered.map(c => {
          const scoreColor = c.score >= 90 ? C.hot : c.score >= 70 ? C.warm : c.score >= 50 ? C.cool : C.dim;
          return (
            <div key={c.name} style={{ background:C.surface, borderRadius:10, border:`1px solid ${C.border}`, overflow:"hidden", transition:"all 0.3s" }}>
              <div style={{ background:`linear-gradient(135deg, ${scoreColor}15, ${C.surface})`, padding:"12px 16px", borderBottom:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                <div>
                  <div style={{ color:C.text, fontWeight:700, fontSize:15 }}>{c.name}</div>
                  <div style={{ color:C.dim, fontSize:11, marginTop:2 }}>{c.domain} · {c.region}</div>
                </div>
                <div style={{ textAlign:"right" }}>
                  <div style={{ fontSize:24, fontWeight:800, color:scoreColor, fontFamily:FONT.display }}>{c.score}</div>
                  <Badge color={c.brand === "TBF" ? C.tbf : C.dft}>{c.brand}</Badge>
                </div>
              </div>
              <div style={{ padding:14 }}>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr 1fr", gap:8, marginBottom:10 }}>
                  {[
                    { v:c.contacts, l:"Contacts" },
                    { v:c.emails, l:"Emails" },
                    { v:c.briefStatus === "complete" ? "Done" : "Pending", l:"Brief" },
                    { v:c.tier?.toUpperCase(), l:"Tier" },
                  ].map(m => (
                    <div key={m.l} style={{ textAlign:"center" }}>
                      <div style={{ fontSize:15, fontWeight:700, color:C.text, fontFamily:FONT.display }}>{m.v}</div>
                      <div style={{ fontSize:9, color:C.dim, textTransform:"uppercase" }}>{m.l}</div>
                    </div>
                  ))}
                </div>
                {c.topPerson && c.topPerson !== "TBD" && (
                  <div style={{ background:`${C.gold}08`, border:`1px solid ${C.gold}25`, borderRadius:6, padding:"6px 10px", marginBottom:8 }}>
                    <div style={{ fontSize:9, color:C.gold, textTransform:"uppercase", fontWeight:700 }}>Decision Maker</div>
                    <div style={{ fontSize:12, color:C.text }}>{c.topPerson}</div>
                  </div>
                )}
                <div style={{ fontSize:11, color:C.dim, marginBottom:6 }}>{c.products}</div>
                <div style={{ fontSize:11, color:C.text, lineHeight:1.5, paddingTop:6, borderTop:`1px solid ${C.border}40` }}>{c.intel}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── TAB: BUNDLES (Kill Shot Outreach Packages) ───

function BundlesTab() {
  const [activeBundle] = useState("mellow_fellow");
  const [activeArtifact, setActiveArtifact] = useState("whyNow");
  const bundle = DEMO_BUNDLES[activeBundle];
  if (!bundle) return null;

  const tabs = [
    { key:"whyNow", label:"Why Now", icon:"⚡" },
    { key:"email", label:"Email", icon:"✉" },
    { key:"linkedin", label:"LinkedIn", icon:"💬" },
    { key:"callOpener", label:"Call Script", icon:"📞" },
    { key:"heygenScript", label:"HeyGen Video", icon:"🎬" },
    { key:"competitorWedge", label:"Competitor Wedge", icon:"🗡" },
  ];

  return (
    <div style={{ padding:24, overflow:"auto", height:"100%" }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20 }}>
        <div>
          <div style={{ color:C.gold, fontWeight:700, fontSize:16, fontFamily:FONT.display }}>KILL SHOT BUNDLE</div>
          <div style={{ color:C.dim, fontSize:12 }}>One command generates complete outreach package for any target</div>
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
          <Badge color={C.green}>{bundle.company}</Badge>
          <Badge color={C.hot}>{bundle.playbook}</Badge>
          <Badge color={C.warm}>Confidence: {bundle.confidence}</Badge>
        </div>
      </div>

      {/* Artifact Tabs */}
      <div style={{ display:"flex", gap:4, marginBottom:16, flexWrap:"wrap" }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveArtifact(t.key)} style={{
            background: activeArtifact === t.key ? C.gold : C.surface,
            color: activeArtifact === t.key ? C.void : C.dim,
            border:`1px solid ${activeArtifact === t.key ? C.gold : C.border}`,
            padding:"8px 16px", borderRadius:6, cursor:"pointer", fontSize:12, fontWeight:600,
            fontFamily:FONT.body, transition:"all 0.2s"
          }}>{t.icon} {t.label}</button>
        ))}
      </div>

      {/* Artifact Content */}
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:24, minHeight:400 }}>
        <pre style={{ color:C.text, fontSize:13, lineHeight:1.7, fontFamily:FONT.body, whiteSpace:"pre-wrap", wordWrap:"break-word" }}>
          {bundle.artifacts[activeArtifact]}
        </pre>
      </div>

      <div style={{ marginTop:16, padding:14, background:`${C.gold}08`, border:`1px solid ${C.gold}25`, borderRadius:8 }}>
        <div style={{ color:C.gold, fontSize:11, fontWeight:700, fontFamily:FONT.display, marginBottom:4 }}>HOW IT WORKS</div>
        <div style={{ color:C.dim, fontSize:12, lineHeight:1.6 }}>
          <code style={{ color:C.green, fontFamily:FONT.display }}>python3 scripts/kill_shot_bundle.py --company "Mellow Fellow" --domain mellowfellow.fun</code>
          <br />→ Generates 9 files: Why Now, Account Brief (.docx), Competitor Wedge, Email, LinkedIn DM, Call Opener, HeyGen Script, Task Payload, Attribution JSON
        </div>
      </div>
    </div>
  );
}

// ─── TAB: AGENTS ───

function AgentsTab({ agents }) {
  const totalLines = agents.reduce((s, a) => s + a.lines, 0);
  const statusColors = { active:C.green, deployed:C.cool, ready:C.warm, standby:C.dim };

  return (
    <div style={{ padding:24, overflow:"auto", height:"100%" }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20 }}>
        <div>
          <div style={{ color:C.gold, fontWeight:700, fontSize:16, fontFamily:FONT.display }}>AGENT FLEET</div>
          <div style={{ color:C.dim, fontSize:12 }}>{agents.length} specialized agents · {totalLines.toLocaleString()} lines of code</div>
        </div>
        <div style={{ display:"flex", gap:12 }}>
          {Object.entries(statusColors).map(([s, color]) => (
            <div key={s} style={{ display:"flex", alignItems:"center", gap:4 }}>
              <span style={{ width:8, height:8, borderRadius:"50%", background:color, display:"inline-block" }} />
              <span style={{ fontSize:11, color:C.dim, textTransform:"capitalize" }}>{s} ({agents.filter(a => a.status === s).length})</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(320px, 1fr))", gap:12 }}>
        {agents.map(a => (
          <div key={a.name} style={{ background:C.surface, borderRadius:10, border:`1px solid ${C.border}`, padding:16, transition:"all 0.3s" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
              <span style={{ color:C.text, fontWeight:700, fontSize:14 }}>{a.name}</span>
              <Badge color={statusColors[a.status] || C.dim}>{a.status.toUpperCase()}</Badge>
            </div>
            <div style={{ color:C.dim, fontSize:12, marginBottom:10, lineHeight:1.4 }}>{a.desc}</div>
            <div style={{ color:C.muted, fontSize:11, fontFamily:FONT.display }}>{a.file} · {a.lines}L</div>
          </div>
        ))}
      </div>

      {/* Architecture Diagram */}
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginTop:20 }}>
        <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:14 }}>SYSTEM ARCHITECTURE</div>
        <pre style={{ color:C.dim, fontSize:11, fontFamily:FONT.display, lineHeight:1.6, textAlign:"center" }}>{`
┌─────────────────────────────────────────────────────────────┐
│                    WAR ROOM (Central Brain)                  │
│  Knowledge Graph (53+ entities) · Signal Processing (35+)   │
│  Decision Engine · Learning Loop · Outcome Attribution       │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
  INTELLIGENCE         PIPELINE            OUTPUT
  · Sales Intel v4     · Apollo Pipeline   · Kill Shot Bundle
  · Free Intel         · CSV Importer v2   · HeyGen Scripts
  · Social Intel v2    · Enrich Pipeline   · GHL CRM Sync
  · Competitor v2      · Model Router      · Brief → DOCX
  · Terpene Research                       · Dashboard
  · Trigger Monitor
        `}</pre>
      </div>
    </div>
  );
}

// ─── TAB: RESEARCH ───

function ResearchTab({ snapshot }) {
  const highlights = snapshot?.researchHighlights || [];
  const businessInsights = snapshot?.businessInsights || [];
  const signalWeights = snapshot?.signalWeights || [];

  return (
    <div style={{ padding:24, overflow:"auto", height:"100%" }}>
      <div style={{ color:C.gold, fontWeight:700, fontSize:16, fontFamily:FONT.display, marginBottom:4 }}>RESEARCH INTELLIGENCE</div>
      <div style={{ color:C.dim, fontSize:12, marginBottom:20 }}>PhD-grade terpene research → compliance-safe sales angles</div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:20 }}>
        {/* Signal Learning */}
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20 }}>
          <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:12 }}>SIGNAL WEIGHTS (LEARNING)</div>
          <div style={{ color:C.dim, fontSize:11, marginBottom:12 }}>Weights adjust automatically based on deal outcomes</div>
          {(signalWeights.length > 0 ? signalWeights : [
            { signal:"trustpilot_below_3.5", weight:15.0 },
            { signal:"quality_complaint_about_competitor", weight:12.0 },
            { signal:"regulatory_change", weight:12.0 },
            { signal:"reddit_supplier_seeking", weight:10.0 },
            { signal:"leadership_change", weight:9.0 },
            { signal:"new_facility_or_expansion", weight:8.0 },
            { signal:"reddit_complaint", weight:7.0 },
            { signal:"price_discussion", weight:7.0 },
            { signal:"hiring_extraction_roles", weight:6.5 },
            { signal:"new_product_launch", weight:6.0 },
          ]).slice(0, 10).map((sw, i) => (
            <div key={i} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"5px 0", borderBottom:`1px solid ${C.border}30` }}>
              <span style={{ color:C.text, fontSize:12 }}>{sw.signal.replace(/_/g, " ")}</span>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <div style={{ width:80, height:4, background:C.border, borderRadius:2, overflow:"hidden" }}>
                  <div style={{ width:`${Math.min(sw.weight / 15 * 100, 100)}%`, height:"100%", background:C.gold, borderRadius:2 }} />
                </div>
                <span style={{ color:C.gold, fontFamily:FONT.display, fontSize:11, fontWeight:700, minWidth:30, textAlign:"right" }}>{sw.weight}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Business Insights */}
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20 }}>
          <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:12 }}>RESEARCH → BUSINESS TRANSLATION</div>
          <div style={{ color:C.dim, fontSize:11, marginBottom:12 }}>Science converted to compliance-safe selling points</div>
          {(businessInsights.length > 0 ? businessInsights : [
            { terpene:"Myrcene", category:"pain inflammation", safe_framing:"Formulations featuring Myrcene show strong consumer-perceived comfort and recovery benefits", product_angle:"Topical/transdermal formulations, recovery blends", confidence:5 },
            { terpene:"Linalool", category:"sleep relaxation", safe_framing:"Linalool-forward profiles are associated with consumer-preferred relaxation and restfulness", product_angle:"Evening/nighttime blends, wind-down formulations", confidence:4 },
            { terpene:"Limonene", category:"mental health", safe_framing:"Consumer preference data aligns with Limonene's aromatic profile for mood and wellbeing", product_angle:"Daytime mood blends, uplift profiles", confidence:4 },
          ]).slice(0, 5).map((bi, i) => (
            <div key={i} style={{ padding:"10px 0", borderBottom:`1px solid ${C.border}30` }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:4 }}>
                <Badge color={C.gold}>{bi.terpene}</Badge>
                <span style={{ fontSize:10, color:C.dim }}>{bi.category?.replace(/_/g, " ")}</span>
              </div>
              <div style={{ fontSize:12, color:C.text, lineHeight:1.5, marginBottom:4 }}>{bi.safe_framing}</div>
              <div style={{ fontSize:11, color:C.dim }}>→ {bi.product_angle}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Research Papers */}
      {highlights.length > 0 && (
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:12, padding:20, marginTop:20 }}>
          <div style={{ color:C.gold, fontWeight:700, fontSize:13, fontFamily:FONT.display, marginBottom:12 }}>KNOWLEDGE BASE — {highlights.length} PAPERS</div>
          {highlights.slice(0, 8).map((p, i) => (
            <div key={i} style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", padding:"8px 0", borderBottom:`1px solid ${C.border}30` }}>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:12, color:C.text, lineHeight:1.4 }}>{p.title}</div>
                <div style={{ fontSize:11, color:C.dim, marginTop:2 }}>{p.journal} · {p.year} · {(p.terpenes || []).join(", ")}</div>
              </div>
              <Badge color={p.evidenceGrade === "A" ? C.green : p.evidenceGrade === "B" ? C.warm : C.dim}>Grade {p.evidenceGrade}</Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── MAIN APP ───

function NexusDashboard() {
  const [booted, setBooted] = useState(false);
  const [bootLines, setBootLines] = useState([]);
  const [activeTab, setActiveTab] = useState("DASHBOARD");
  const [snapshot, setSnapshot] = useState(null);

  // Boot sequence
  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < BOOT_LINES.length) {
        const line = BOOT_LINES[i];
        i++;
        setBootLines(prev => [...prev, line]);
      } else {
        clearInterval(timer);
        setTimeout(() => setBooted(true), 500);
      }
    }, 180);
    return () => clearInterval(timer);
  }, []);

  // Fetch live data
  useEffect(() => {
    if (!booted) return;
    const api = window.__REEF_API__;
    if (!api) return;
    fetch(api.snapshot)
      .then(r => r.json())
      .then(data => setSnapshot(data))
      .catch(() => {});
  }, [booted]);

  // Derive data from snapshot or fall back to demo
  const companies = useMemo(() => {
    if (snapshot?.priorities?.length > 0) {
      return snapshot.priorities.map(p => ({
        name: p.company, domain: p.domain, score: p.score, tier: p.tier,
        contacts: p.contacts, emails: p.verified, topPerson: p.topContact,
        topTitle: p.topTitle, briefStatus: p.briefComplete ? "complete" : "pending",
        brand: p.tier === "hot" ? "DFT" : "TBF", region: "",
        products: (p.features || []).join(" · "), intel: p.whyNow || "",
        currentSupplier: p.currentSupplier || "",
      }));
    }
    return DEMO_COMPANIES;
  }, [snapshot]);

  const competitors = useMemo(() => {
    if (snapshot?.competitors?.length > 0) return snapshot.competitors;
    return DEMO_COMPETITORS;
  }, [snapshot]);

  const pipeline = useMemo(() => {
    const hot = companies.filter(c => c.tier === "hot").length;
    const warm = companies.filter(c => c.tier === "warm").length;
    const cool = companies.filter(c => c.tier === "cool").length;
    const cold = companies.filter(c => c.tier === "cold").length;
    return { total: DEMO_PIPELINE.total, hot: DEMO_PIPELINE.hot, warm: DEMO_PIPELINE.warm, cool: DEMO_PIPELINE.cool, cold: DEMO_PIPELINE.cold, companies: companies.length, verified: DEMO_PIPELINE.verified };
  }, [companies]);

  // ── Boot Screen ──
  if (!booted) {
    return (
      <div style={{ background:C.void, minHeight:"100vh", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", fontFamily:FONT.display, padding:24 }}>
        <div style={{ fontSize:36, fontWeight:800, background:`linear-gradient(135deg, ${C.gold}, #e8c55a)`, WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", marginBottom:8, letterSpacing:6 }}>NEXUS</div>
        <div style={{ fontSize:13, color:C.dim, marginBottom:32, letterSpacing:2 }}>BDR INTELLIGENCE SYSTEM</div>
        <div style={{ maxWidth:640, width:"100%" }}>
          {bootLines.filter(Boolean).map((line, i) => (
            <div key={i} style={{ color:line.color || C.text, fontSize:13, padding:"3px 0", opacity:0, animation:"fadeIn 0.3s forwards", animationDelay:`${i*0.05}s` }}>
              <span style={{ color:C.muted, marginRight:8 }}>[{String(i).padStart(2,"0")}]</span>{line.text || ""}
            </div>
          ))}
        </div>
        <style>{`@keyframes fadeIn { to { opacity: 1 } }`}</style>
      </div>
    );
  }

  const TABS = ["DASHBOARD", "PIPELINE", "BUNDLES", "RESEARCH", "AGENTS"];

  // ── Main Interface ──
  return (
    <div style={{ background:C.bg, minHeight:"100vh", fontFamily:FONT.body, color:C.text }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* Ticker */}
      <div style={{ background:C.void, borderBottom:`1px solid ${C.border}`, overflow:"hidden", height:28, display:"flex", alignItems:"center" }}>
        <div style={{ display:"flex", gap:48, whiteSpace:"nowrap", animation:"ticker 60s linear infinite", paddingLeft:"100%" }}>
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((text, i) => (
            <span key={i} style={{ fontSize:11, fontFamily:FONT.display }}>
              <span style={{ color:C.gold, marginRight:6 }}>●</span>
              <span style={{ color:C.dim }}>{text}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Header */}
      <div style={{ padding:"10px 24px", display:"flex", justifyContent:"space-between", alignItems:"center", borderBottom:`1px solid ${C.border}`, background:C.void }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <span style={{ fontSize:22, fontWeight:800, background:`linear-gradient(135deg, ${C.gold}, #e8c55a)`, WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", letterSpacing:4, fontFamily:FONT.display }}>NEXUS</span>
          <span style={{ color:C.dim, fontSize:12, letterSpacing:1 }}>BDR Intelligence System v5.0</span>
          {snapshot && <Badge color={C.green}>LIVE</Badge>}
          {!snapshot && <Badge color={C.warm}>DEMO</Badge>}
        </div>
        <div style={{ display:"flex", gap:3 }}>
          {TABS.map(t => (
            <button key={t} onClick={() => setActiveTab(t)} style={{
              background: activeTab === t ? C.gold : "transparent",
              color: activeTab === t ? C.void : C.dim,
              border:`1px solid ${activeTab === t ? C.gold : C.border}`,
              padding:"7px 18px", borderRadius:5, fontSize:11, fontWeight:700,
              cursor:"pointer", fontFamily:FONT.display, letterSpacing:1, transition:"all 0.2s"
            }}>{t}</button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ height:"calc(100vh - 70px)", overflow:"hidden" }}>
        {activeTab === "DASHBOARD" && <DashboardTab companies={companies} pipeline={pipeline} competitors={competitors} snapshot={snapshot} />}
        {activeTab === "PIPELINE" && <PipelineTab companies={companies} />}
        {activeTab === "BUNDLES" && <BundlesTab />}
        {activeTab === "RESEARCH" && <ResearchTab snapshot={snapshot} />}
        {activeTab === "AGENTS" && <AgentsTab agents={DEMO_AGENTS} />}
      </div>

      <style>{`
        @keyframes ticker { 0% { transform: translateX(0) } 100% { transform: translateX(-50%) } }
        ::-webkit-scrollbar { width:6px }
        ::-webkit-scrollbar-track { background:${C.void} }
        ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:3px }
        ::-webkit-scrollbar-thumb:hover { background:${C.gold}40 }
        * { margin:0; padding:0; box-sizing:border-box; }
      `}</style>
    </div>
  );
}
