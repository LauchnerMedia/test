import { useState, useEffect, useRef, useCallback } from "react";

const GOLD = "#d4a843";
const VOID = "#020208";
const BG = "#06060d";
const SURFACE = "#0d0d1a";
const BORDER = "#1a1a2e";
const TEXT = "#e8e8f0";
const DIM = "#666680";
const HOT = "#ff2d2d";
const WARM = "#ff8c00";
const COOL = "#2d7fff";
const GRN = "#00e09a";

// ── Corrected pricing data ──
const PRICING = {
  cdt_premium: "$5,000–8,000/L",
  cdt_self_extract: "$1,500–3,000/L",
  botanical_dft: "$45–80/L",
  savings: "25–100x",
};

const COMPANIES = [
  { name:"Mellow Fellow", contacts:25, score:96, brand:"DFT", region:"FL", domain:"mellowfellow.fun", topPerson:"JJ Coombs (PharmD)", topScore:100, emails:3, products:"Vapes·Edibles·THCa·Beverages", intel:"#1 target. Pharmacist-founded. Self-extracts CDT at Arvida Labs. 40+ states. 3.0/5 Trustpilot = quality issues. Federal THC ban = existential threat. Good Fellows coalition (Urb, Zombi, Pushin P's) = 4 accounts. Brief COMPLETE.", briefStatus:"complete" },
  { name:"Urb", contacts:0, score:90, brand:"DFT", region:"US", domain:"urbextracts.com", topPerson:"TBD", topScore:90, emails:0, products:"Vapes·Gummies·Disposables", intel:"Good Fellows coalition member. Warm intro via Mellow Fellow. Brief NEEDED.", briefStatus:"pending" },
  { name:"Zombi", contacts:0, score:88, brand:"DFT", region:"US", domain:"zombibrand.com", topPerson:"TBD", topScore:88, emails:0, products:"Vapes·Edibles·Delta-8", intel:"Good Fellows coalition member. Warm intro via Mellow Fellow. Brief NEEDED.", briefStatus:"pending" },
  { name:"Pushin P's", contacts:0, score:86, brand:"DFT", region:"US", domain:"pushinps.com", topPerson:"TBD", topScore:86, emails:0, products:"Vapes·Concentrates", intel:"Good Fellows coalition member. Warm intro via Mellow Fellow. Brief NEEDED.", briefStatus:"pending" },
  { name:"CBD Alchemy", contacts:10, score:88, brand:"DFT", region:"ES", domain:"cbdalchemy.com", topPerson:"Django (CEO)", topScore:100, emails:2, products:"CBD Oils·Topicals", intel:"Spanish CBD brand. European market entry for DFT. Strong CEO relationship potential." },
  { name:"Cannvital", contacts:8, score:85, brand:"TBF", region:"DE", domain:"cannvital.de", topPerson:"TBD", topScore:85, emails:1, products:"CBD·Wellness", intel:"German wellness brand. TBF enterprise fit for EU scale." },
  { name:"A-Sense", contacts:18, score:73, brand:"DFT", region:"PL", domain:"a-sense.com", topPerson:"TBD", topScore:73, emails:16, products:"Extraction·Terpenes", intel:"Polish extraction company. Strong email coverage." },
  { name:"Alpha Brands", contacts:1, score:100, brand:"DFT", region:"US", domain:"alphabrands.co", topPerson:"J. Lazoff (CEO)", topScore:100, emails:1, products:"Multi-brand", intel:"Multi-brand operator. Single decision maker. High intent." },
];

const AGENTS = [
  { name:"Sales Intel Brief v3", status:"active", desc:"6-phase AI research + OpenRouter cost optimization", file:"sales_intel_brief_v3.py", lines:328 },
  { name:"Free Intel Harvester", status:"active", desc:"Reddit, FDA, news, competitors — zero API cost", file:"free_intel_sources.py", lines:380 },
  { name:"Model Router", status:"active", desc:"Anthropic ↔ OpenRouter, 10-50x cost reduction", file:"model_router.py", lines:401 },
  { name:"Social Intel Engine v2", status:"ready", desc:"Reddit deep scan + intent classification + community mapping", file:"social_intel_engine_v2.py", lines:1257 },
  { name:"Trigger Monitor", status:"ready", desc:"Daily buying signal detection across watchlist", file:"trigger_monitor.py", lines:650 },
  { name:"HeyGen Script Gen", status:"ready", desc:"Personalized video scripts from brief data", file:"heygen_scripts.py", lines:391 },
  { name:"Customer Intel", status:"standby", desc:"Post-onboarding: churn, upsell, reactivation engine", file:"customer_intel.py", lines:629 },
  { name:"Apollo Pipeline", status:"deployed", desc:"Lead discovery → scoring → CRM", file:"apollo_pipeline.py", lines:800 },
  { name:"GHL Sync v2", status:"deployed", desc:"53-field CRM architecture + workflow automation", file:"ghl_sync_v2.py", lines:540 },
  { name:"CSV Importer v2", status:"deployed", desc:"Apollo → normalized → scored pipeline", file:"csv_importer_v2.py", lines:420 },
  { name:"Enrichment Pipeline v2", status:"deployed", desc:"Hunter verification + data enrichment", file:"enrich_pipeline_v2.py", lines:560 },
  { name:"Master Orchestrator v7", status:"active", desc:"Single CLI entry point for entire system", file:"nexus.py", lines:480 },
];

const PIPELINE_STATS = { total:138, hot:61, warm:32, cool:28, cold:17, companies:22, verified:37, imported:133 };

const SYSTEM_LINES = [
  { text: "NEXUS BDR SYSTEM v5.0 — INITIALIZING", color: GOLD },
  { text: "Loading agent fleet... 12 agents", color: TEXT },
  { text: "Pipeline data: 138 contacts / 22 companies / 61 hot", color: GRN },
  { text: "Model Router: Anthropic ✅  OpenRouter ⚙️", color: TEXT },
  { text: "Free Intel: Reddit ✅  FDA ✅  News ✅  SEC ✅", color: GRN },
  { text: "CRM Sync: GHL ✅  53 custom fields deployed", color: GRN },
  { text: "Briefs: 1 complete (Mellow Fellow) / 3 pending", color: WARM },
  { text: `CDT Market: ${PRICING.cdt_premium} | Botanical: ${PRICING.botanical_dft}`, color: GOLD },
  { text: "Creative: HeyGen templates loaded / 4 video scripts ready", color: TEXT },
  { text: "SYSTEM ONLINE — All agents operational", color: GRN },
];

const TICKER_ITEMS = [
  { text: "138 contacts scored → GHL imported (96% success)", color: GRN },
  { text: `CDT pricing corrected: Premium ${PRICING.cdt_premium} | Self-extract ${PRICING.cdt_self_extract}`, color: GOLD },
  { text: "Mellow Fellow brief COMPLETE — 6-phase intel + outreach sequence", color: GRN },
  { text: "Good Fellows coalition identified: Urb + Zombi + Pushin P's = $150-350K pipeline", color: GOLD },
  { text: "Federal hemp THC ban (Dec 2025) — existential threat = botanical opportunity", color: HOT },
  { text: "OpenRouter integrated — brief cost: $0.15 vs $1.00 (85% savings)", color: GRN },
  { text: "Reddit monitoring: 14 subreddits / terpene + buying signals", color: COOL },
  { text: "HeyGen: 4 video templates ready — 1 recording → 50+ personalized videos", color: TEXT },
];

// ── Chat logic ──
function processCommand(input, addMsg) {
  const cmd = input.trim().toLowerCase();
  
  if (cmd === "/help") {
    return { type:"system", content:"**Commands:**\n/pipeline — Pipeline overview\n/company [name] — Company intel card\n/top [n] — Top prospects\n/agents — Agent fleet status\n/pricing — CDT vs botanical analysis\n/brief [company] — Brief status\n/coalition — Good Fellows opportunity\n/demo — System capabilities overview\n/status — System health" };
  }
  
  if (cmd === "/pipeline") {
    return { type:"pipeline", data: PIPELINE_STATS };
  }

  if (cmd === "/pricing") {
    return { type:"pricing" };
  }

  if (cmd === "/coalition") {
    return { type:"coalition" };
  }

  if (cmd.startsWith("/top")) {
    const n = parseInt(cmd.split(" ")[1]) || 5;
    return { type:"top", data: COMPANIES.slice(0, n) };
  }

  if (cmd.startsWith("/company") || cmd.startsWith("tell me about")) {
    const query = cmd.replace("/company", "").replace("tell me about", "").trim();
    const match = COMPANIES.find(c => c.name.toLowerCase().includes(query.toLowerCase()));
    if (match) return { type:"company", data: match };
    return { type:"system", content: `No company found matching "${query}". Try /top to see available companies.` };
  }

  if (cmd === "/agents") {
    return { type:"agents" };
  }

  if (cmd === "/demo") {
    return { type:"demo" };
  }

  if (cmd === "/status") {
    return { type:"status" };
  }

  // Natural language fallback
  if (cmd.includes("mellow") || cmd.includes("fellow")) {
    return { type:"company", data: COMPANIES[0] };
  }
  if (cmd.includes("price") || cmd.includes("cost") || cmd.includes("cdt")) {
    return { type:"pricing" };
  }
  if (cmd.includes("coalition") || cmd.includes("urb") || cmd.includes("zombi")) {
    return { type:"coalition" };
  }

  return { type:"system", content: `Processing: "${input}"\n\nI can answer questions about the pipeline, companies, pricing, and system status. Try /help for commands, or ask naturally — "tell me about Mellow Fellow", "what's the CDT pricing", "show me the coalition opportunity".` };
}

// ── Components ──
function PipelineViz({ data }) {
  const total = data.total;
  const segs = [
    { label:"HOT", count:data.hot, color:HOT, pct:Math.round(data.hot/total*100) },
    { label:"WARM", count:data.warm, color:WARM, pct:Math.round(data.warm/total*100) },
    { label:"COOL", count:data.cool, color:COOL, pct:Math.round(data.cool/total*100) },
    { label:"COLD", count:data.cold, color:"#555", pct:Math.round(data.cold/total*100) },
  ];
  return (
    <div style={{ background:SURFACE, borderRadius:8, padding:16, border:`1px solid ${BORDER}` }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
        <span style={{ color:GOLD, fontWeight:700, fontFamily:"'JetBrains Mono',monospace", fontSize:13 }}>PIPELINE: {total} CONTACTS / {data.companies} COMPANIES</span>
        <span style={{ color:DIM, fontSize:12 }}>{data.verified} verified · {data.imported} in GHL</span>
      </div>
      <div style={{ display:"flex", height:44, borderRadius:6, overflow:"hidden", gap:2 }}>
        {segs.map(s => (
          <div key={s.label} style={{ width:`${s.pct}%`, background:s.color, display:"flex", alignItems:"center", justifyContent:"center", transition:"width 0.8s", minWidth:s.count > 0 ? 40 : 0 }}>
            <span style={{ fontWeight:800, fontSize:14, color:"#000", fontFamily:"'JetBrains Mono',monospace" }}>{s.count}</span>
          </div>
        ))}
      </div>
      <div style={{ display:"flex", gap:8, marginTop:8 }}>
        {segs.map(s => (
          <div key={s.label} style={{ flex:1, textAlign:"center", padding:"6px 0", borderRadius:4, background:`${s.color}15`, border:`1px solid ${s.color}30` }}>
            <div style={{ fontSize:11, color:s.color, fontWeight:700, fontFamily:"'JetBrains Mono',monospace" }}>{s.label}</div>
            <div style={{ fontSize:10, color:DIM }}>{s.pct}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CompanyCard({ data }) {
  const scoreColor = data.score >= 90 ? HOT : data.score >= 70 ? WARM : data.score >= 50 ? COOL : DIM;
  return (
    <div style={{ background:SURFACE, borderRadius:8, border:`1px solid ${BORDER}`, overflow:"hidden" }}>
      <div style={{ background:`linear-gradient(135deg, ${scoreColor}20, ${SURFACE})`, padding:"12px 16px", borderBottom:`1px solid ${BORDER}` }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <span style={{ color:TEXT, fontWeight:700, fontSize:16 }}>{data.name}</span>
          <span style={{ color:scoreColor, fontWeight:800, fontSize:20, fontFamily:"'JetBrains Mono',monospace", textShadow: data.score >= 90 ? `0 0 12px ${scoreColor}50` : "none" }}>{data.score}</span>
        </div>
        <div style={{ color:DIM, fontSize:12, marginTop:2 }}>{data.domain} · {data.region} · {data.brand}</div>
      </div>
      <div style={{ padding:16 }}>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr 1fr", gap:12, marginBottom:12 }}>
          {[
            { v:data.contacts, l:"Contacts" },
            { v:data.emails, l:"Emails" },
            { v:data.topScore, l:"Top Score" },
            { v:data.briefStatus === "complete" ? "✅" : "⏳", l:"Brief" },
          ].map(m => (
            <div key={m.l} style={{ textAlign:"center" }}>
              <div style={{ fontSize:18, fontWeight:700, color:TEXT, fontFamily:"'JetBrains Mono',monospace" }}>{m.v}</div>
              <div style={{ fontSize:10, color:DIM, textTransform:"uppercase" }}>{m.l}</div>
            </div>
          ))}
        </div>
        {data.topPerson && (
          <div style={{ background:`${GOLD}10`, border:`1px solid ${GOLD}30`, borderRadius:6, padding:"8px 12px", marginBottom:8 }}>
            <div style={{ fontSize:10, color:GOLD, textTransform:"uppercase", fontWeight:600 }}>Decision Maker</div>
            <div style={{ fontSize:13, color:TEXT }}>{data.topPerson}</div>
          </div>
        )}
        <div style={{ fontSize:12, color:DIM, marginBottom:6 }}>{data.products}</div>
        <div style={{ fontSize:12, color:TEXT, lineHeight:1.5, padding:"8px 0", borderTop:`1px solid ${BORDER}` }}>{data.intel}</div>
      </div>
    </div>
  );
}

function PricingCard() {
  return (
    <div style={{ background:SURFACE, borderRadius:8, border:`1px solid ${BORDER}`, padding:16 }}>
      <div style={{ color:GOLD, fontWeight:700, fontSize:14, marginBottom:12, fontFamily:"'JetBrains Mono',monospace" }}>CDT vs BOTANICAL TERPENE ECONOMICS</div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:16 }}>
        <div style={{ textAlign:"center", padding:12, background:`${HOT}10`, borderRadius:6, border:`1px solid ${HOT}30` }}>
          <div style={{ fontSize:18, fontWeight:800, color:HOT, fontFamily:"'JetBrains Mono',monospace" }}>{PRICING.cdt_premium}</div>
          <div style={{ fontSize:10, color:DIM, marginTop:4 }}>PREMIUM CDT (MARKET)</div>
        </div>
        <div style={{ textAlign:"center", padding:12, background:`${WARM}10`, borderRadius:6, border:`1px solid ${WARM}30` }}>
          <div style={{ fontSize:18, fontWeight:800, color:WARM, fontFamily:"'JetBrains Mono',monospace" }}>{PRICING.cdt_self_extract}</div>
          <div style={{ fontSize:10, color:DIM, marginTop:4 }}>SELF-EXTRACTION (AMORTIZED)</div>
        </div>
        <div style={{ textAlign:"center", padding:12, background:`${GRN}10`, borderRadius:6, border:`1px solid ${GRN}30` }}>
          <div style={{ fontSize:18, fontWeight:800, color:GRN, fontFamily:"'JetBrains Mono',monospace" }}>{PRICING.botanical_dft}</div>
          <div style={{ fontSize:10, color:DIM, marginTop:4 }}>DFT BOTANICAL</div>
        </div>
      </div>
      <div style={{ fontSize:13, color:TEXT, lineHeight:1.6 }}>
        <strong style={{ color:GOLD }}>The math:</strong> For non-flagship products (edibles, beverages, wellness, topicals), consumers cannot distinguish CDT from botanical. A brand spending $100K/yr on terpenes could reclaim <strong style={{ color:GRN }}>$95K+ in margin</strong> by converting non-vape lines to DFT botanical blends.
      </div>
    </div>
  );
}

function CoalitionCard() {
  const brands = [
    { name:"Mellow Fellow", status:"BRIEF COMPLETE", color:GRN, value:"$14-96K/yr" },
    { name:"Urb", status:"WARM INTRO READY", color:WARM, value:"$20-60K/yr" },
    { name:"Zombi", status:"WARM INTRO READY", color:WARM, value:"$15-45K/yr" },
    { name:"Pushin P's", status:"WARM INTRO READY", color:WARM, value:"$10-30K/yr" },
  ];
  return (
    <div style={{ background:SURFACE, borderRadius:8, border:`1px solid ${GOLD}40`, padding:16 }}>
      <div style={{ color:GOLD, fontWeight:700, fontSize:14, marginBottom:4, fontFamily:"'JetBrains Mono',monospace" }}>GOOD FELLOWS COALITION</div>
      <div style={{ color:DIM, fontSize:12, marginBottom:12 }}>Land Mellow Fellow → warm intro to 3 more brands</div>
      {brands.map(b => (
        <div key={b.name} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"8px 0", borderBottom:`1px solid ${BORDER}` }}>
          <span style={{ color:TEXT, fontWeight:600 }}>{b.name}</span>
          <div style={{ display:"flex", gap:12, alignItems:"center" }}>
            <span style={{ fontSize:12, color:b.color, fontFamily:"'JetBrains Mono',monospace" }}>{b.status}</span>
            <span style={{ fontSize:13, color:TEXT, fontWeight:700, fontFamily:"'JetBrains Mono',monospace" }}>{b.value}</span>
          </div>
        </div>
      ))}
      <div style={{ marginTop:12, padding:12, background:`${GOLD}10`, borderRadius:6, textAlign:"center" }}>
        <div style={{ fontSize:10, color:DIM, textTransform:"uppercase" }}>Total Coalition Pipeline</div>
        <div style={{ fontSize:24, fontWeight:800, color:GOLD, fontFamily:"'JetBrains Mono',monospace" }}>$150,000–350,000/yr</div>
      </div>
    </div>
  );
}

// ── Main App ──
export default function NexusV5() {
  const [booted, setBooted] = useState(false);
  const [bootLines, setBootLines] = useState([]);
  const [view, setView] = useState("COMMAND");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const chatRef = useRef(null);
  const inputRef = useRef(null);

  // Boot sequence
  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < SYSTEM_LINES.length) {
        setBootLines(prev => [...prev, SYSTEM_LINES[i]]);
        i++;
      } else {
        clearInterval(timer);
        setTimeout(() => {
          setBooted(true);
          setMessages([{
            role: "assistant",
            type: "system",
            content: "Nexus BDR System online. 12 agents operational. 138 contacts in pipeline. Mellow Fellow brief complete.\n\nType /help for commands, or ask naturally — \"show me the pipeline\", \"tell me about Mellow Fellow\", \"what's the CDT pricing\"."
          }]);
        }, 600);
      }
    }, 200);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (booted && inputRef.current) inputRef.current.focus();
  }, [booted]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  const handleSend = useCallback(() => {
    if (!input.trim()) return;
    const userMsg = { role:"user", content:input.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    setTimeout(() => {
      const result = processCommand(input, setMessages);
      setMessages(prev => [...prev, { role:"assistant", ...result }]);
      setTyping(false);
    }, 400 + Math.random() * 400);
  }, [input]);

  const handleKey = (e) => { if (e.key === "Enter") handleSend(); };

  // ── Boot Screen ──
  if (!booted) {
    return (
      <div style={{ background:VOID, minHeight:"100vh", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", fontFamily:"'JetBrains Mono',monospace", padding:24 }}>
        <div style={{ fontSize:28, fontWeight:800, background:`linear-gradient(135deg, ${GOLD}, #e8c55a)`, WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", marginBottom:32, letterSpacing:4 }}>NEXUS</div>
        <div style={{ maxWidth:600, width:"100%" }}>
          {bootLines.map((line, i) => (
            <div key={i} style={{ color:line.color, fontSize:13, padding:"3px 0", opacity:0, animation:"fadeIn 0.3s forwards", animationDelay:`${i*0.05}s` }}>
              <span style={{ color:DIM, marginRight:8 }}>[{String(i).padStart(2,"0")}]</span>{line.text}
            </div>
          ))}
        </div>
        <style>{`@keyframes fadeIn { to { opacity: 1 } }`}</style>
      </div>
    );
  }

  // ── Main Interface ──
  return (
    <div style={{ background:BG, minHeight:"100vh", fontFamily:"'Outfit',sans-serif", color:TEXT }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      
      {/* Ticker */}
      <div style={{ background:VOID, borderBottom:`1px solid ${BORDER}`, overflow:"hidden", height:28, display:"flex", alignItems:"center" }}>
        <div style={{ display:"flex", gap:48, whiteSpace:"nowrap", animation:"ticker 50s linear infinite", paddingLeft:"100%" }}>
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, i) => (
            <span key={i} style={{ fontSize:11, fontFamily:"'JetBrains Mono',monospace" }}>
              <span style={{ color:item.color, marginRight:4 }}>●</span>
              <span style={{ color:DIM }}>{item.text}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Header */}
      <div style={{ padding:"12px 24px", display:"flex", justifyContent:"space-between", alignItems:"center", borderBottom:`1px solid ${BORDER}` }}>
        <div style={{ display:"flex", alignItems:"center", gap:16 }}>
          <span style={{ fontSize:20, fontWeight:800, background:`linear-gradient(135deg, ${GOLD}, #e8c55a)`, WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", letterSpacing:3, fontFamily:"'JetBrains Mono',monospace" }}>NEXUS</span>
          <span style={{ color:DIM, fontSize:12 }}>BDR Intelligence System v5.0</span>
        </div>
        <div style={{ display:"flex", gap:4 }}>
          {["COMMAND","AGENTS","INTEL","PRICING"].map(v => (
            <button key={v} onClick={() => setView(v)} style={{
              background: view === v ? GOLD : "transparent",
              color: view === v ? VOID : DIM,
              border:`1px solid ${view === v ? GOLD : BORDER}`,
              padding:"6px 16px", borderRadius:4, fontSize:11, fontWeight:700,
              cursor:"pointer", fontFamily:"'JetBrains Mono',monospace", letterSpacing:1,
              transition:"all 0.2s"
            }}>{v}</button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ display:"flex", height:"calc(100vh - 72px)" }}>
        
        {/* Left: Chat */}
        <div style={{ flex: view === "COMMAND" ? 1 : 0, minWidth: view === "COMMAND" ? 0 : 0, display: view === "COMMAND" ? "flex" : "none", flexDirection:"column", borderRight:`1px solid ${BORDER}` }}>
          <div ref={chatRef} style={{ flex:1, overflow:"auto", padding:20, display:"flex", flexDirection:"column", gap:12 }}>
            {messages.map((msg, i) => (
              <div key={i}>
                {msg.role === "user" ? (
                  <div style={{ display:"flex", justifyContent:"flex-end" }}>
                    <div style={{ background:`${GOLD}20`, border:`1px solid ${GOLD}40`, borderRadius:"12px 12px 0 12px", padding:"10px 16px", maxWidth:"80%", fontSize:14, color:TEXT }}>{msg.content}</div>
                  </div>
                ) : (
                  <div style={{ maxWidth:"90%" }}>
                    {msg.type === "pipeline" && <PipelineViz data={msg.data} />}
                    {msg.type === "company" && <CompanyCard data={msg.data} />}
                    {msg.type === "pricing" && <PricingCard />}
                    {msg.type === "coalition" && <CoalitionCard />}
                    {msg.type === "top" && (
                      <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                        {msg.data.map(c => <CompanyCard key={c.name} data={c} />)}
                      </div>
                    )}
                    {msg.type === "agents" && (
                      <div style={{ background:SURFACE, borderRadius:8, border:`1px solid ${BORDER}`, padding:12 }}>
                        <div style={{ color:GOLD, fontWeight:700, fontSize:13, marginBottom:8, fontFamily:"'JetBrains Mono',monospace" }}>AGENT FLEET — {AGENTS.length} AGENTS</div>
                        {AGENTS.map(a => (
                          <div key={a.name} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"6px 0", borderBottom:`1px solid ${BORDER}20`, fontSize:12 }}>
                            <div>
                              <span style={{ color:a.status==="active"?GRN:a.status==="deployed"?COOL:a.status==="ready"?WARM:DIM, marginRight:6 }}>●</span>
                              <span style={{ color:TEXT, fontWeight:600 }}>{a.name}</span>
                              <span style={{ color:DIM, marginLeft:8 }}>{a.desc}</span>
                            </div>
                            <span style={{ color:DIM, fontFamily:"'JetBrains Mono',monospace", fontSize:10 }}>{a.lines}L</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {(msg.type === "system" || msg.type === "demo" || msg.type === "status") && (
                      <div style={{ background:SURFACE, borderRadius:8, border:`1px solid ${BORDER}`, padding:"12px 16px", fontSize:13, color:TEXT, lineHeight:1.6, whiteSpace:"pre-wrap" }}>{msg.content}</div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {typing && (
              <div style={{ background:SURFACE, borderRadius:8, padding:"10px 16px", display:"inline-block", maxWidth:80 }}>
                <span style={{ color:GOLD, fontSize:18, letterSpacing:3, animation:"pulse 1s infinite" }}>···</span>
              </div>
            )}
          </div>

          {/* Input */}
          <div style={{ padding:"12px 20px", borderTop:`1px solid ${BORDER}`, display:"flex", gap:8, background:VOID }}>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask anything or type /help..."
              style={{ flex:1, background:SURFACE, border:`1px solid ${BORDER}`, borderRadius:6, padding:"10px 16px", color:TEXT, fontSize:14, fontFamily:"'Outfit',sans-serif", outline:"none" }}
            />
            <button onClick={handleSend} style={{ background:GOLD, color:VOID, border:"none", borderRadius:6, padding:"10px 20px", fontWeight:700, cursor:"pointer", fontSize:13 }}>Send</button>
          </div>
        </div>

        {/* Agents View */}
        {view === "AGENTS" && (
          <div style={{ flex:1, overflow:"auto", padding:24 }}>
            <h2 style={{ color:GOLD, fontSize:18, fontWeight:700, marginBottom:16, fontFamily:"'JetBrains Mono',monospace" }}>AGENT FLEET — {AGENTS.length} AGENTS / {AGENTS.reduce((s,a) => s+a.lines, 0).toLocaleString()} LINES</h2>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(300px, 1fr))", gap:12 }}>
              {AGENTS.map(a => (
                <div key={a.name} style={{ background:SURFACE, borderRadius:8, border:`1px solid ${BORDER}`, padding:16 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
                    <span style={{ color:TEXT, fontWeight:700, fontSize:14 }}>{a.name}</span>
                    <span style={{ color:a.status==="active"?GRN:a.status==="deployed"?COOL:a.status==="ready"?WARM:DIM, fontSize:11, fontFamily:"'JetBrains Mono',monospace", textTransform:"uppercase" }}>{a.status}</span>
                  </div>
                  <div style={{ color:DIM, fontSize:12, marginBottom:8, lineHeight:1.4 }}>{a.desc}</div>
                  <div style={{ color:DIM, fontSize:11, fontFamily:"'JetBrains Mono',monospace" }}>{a.file} · {a.lines}L</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Intel View */}
        {view === "INTEL" && (
          <div style={{ flex:1, overflow:"auto", padding:24 }}>
            <PipelineViz data={PIPELINE_STATS} />
            <div style={{ marginTop:20 }}>
              <h3 style={{ color:GOLD, fontSize:14, fontWeight:700, marginBottom:12, fontFamily:"'JetBrains Mono',monospace" }}>TARGET ACCOUNTS</h3>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(340px, 1fr))", gap:12 }}>
                {COMPANIES.map(c => <CompanyCard key={c.name} data={c} />)}
              </div>
            </div>
          </div>
        )}

        {/* Pricing View */}
        {view === "PRICING" && (
          <div style={{ flex:1, overflow:"auto", padding:24 }}>
            <PricingCard />
            <div style={{ marginTop:16 }}><CoalitionCard /></div>
            <div style={{ marginTop:16, background:SURFACE, borderRadius:8, border:`1px solid ${BORDER}`, padding:16 }}>
              <div style={{ color:GOLD, fontWeight:700, fontSize:14, marginBottom:12, fontFamily:"'JetBrains Mono',monospace" }}>MELLOW FELLOW DEAL MODEL</div>
              {[
                { scenario:"Conservative", desc:"Edibles + wellness botanical supply", value:"$14,400/yr", color:COOL },
                { scenario:"Likely", desc:"Convert edibles + beverages + backup vape", value:"$42,000/yr", color:GRN },
                { scenario:"Upside", desc:"Full botanical partner + custom R&D + coalition", value:"$96,000/yr", color:GOLD },
              ].map(s => (
                <div key={s.scenario} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"10px 0", borderBottom:`1px solid ${BORDER}` }}>
                  <div>
                    <div style={{ color:TEXT, fontWeight:600 }}>{s.scenario}</div>
                    <div style={{ color:DIM, fontSize:12 }}>{s.desc}</div>
                  </div>
                  <div style={{ color:s.color, fontWeight:800, fontSize:18, fontFamily:"'JetBrains Mono',monospace" }}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes ticker { 0% { transform: translateX(0) } 100% { transform: translateX(-50%) } }
        @keyframes pulse { 0%,100% { opacity:0.3 } 50% { opacity:1 } }
        ::-webkit-scrollbar { width:6px }
        ::-webkit-scrollbar-track { background:${VOID} }
        ::-webkit-scrollbar-thumb { background:${BORDER}; border-radius:3px }
        ::-webkit-scrollbar-thumb:hover { background:${GOLD}40 }
      `}</style>
    </div>
  );
}
