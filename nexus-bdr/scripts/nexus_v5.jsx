import { useState, useEffect, useRef, useCallback, useMemo } from "react";

// ═══════════════════════════════════════════════════════════════════════════════
// NEXUS BDR INTELLIGENCE SYSTEM v7.0 — COMPLETE FRONTEND
// Terpene Belt Farms + Duty Free Terpenes | Multi-Agent Sales Intelligence
// ═══════════════════════════════════════════════════════════════════════════════

// ─── DESIGN SYSTEM ───────────────────────────────────────────────────────────
const C = {
  gold: "#d4a843", goldLight: "#e8c55a", goldDim: "#8a7230", goldGlow: "#d4a84320",
  void: "#020208", bg: "#06060d", surface: "#0d0d1a", surfaceHover: "#12122a",
  surfaceActive: "#181835", panel: "#0a0a16",
  border: "#1a1a2e", borderLight: "#252545", borderGold: "#d4a84330",
  text: "#e8e8f0", textDim: "#888899", textMuted: "#555566", textBright: "#ffffff",
  hot: "#ff2d2d", hotGlow: "#ff2d2d30", warm: "#ff8c00", warmGlow: "#ff8c0030",
  cool: "#2d7fff", coolGlow: "#2d7fff30", cold: "#555570",
  green: "#00e09a", greenDim: "#00a070", greenGlow: "#00e09a20",
  purple: "#a855f7", purpleGlow: "#a855f720", pink: "#ec4899", pinkGlow: "#ec489920",
  cyan: "#22d3ee", cyanGlow: "#22d3ee20",
  gradeA: "#00e09a", gradeB: "#22d3ee", gradeC: "#ff8c00", gradeD: "#555570",
  red: "#ef4444", orange: "#f97316", yellow: "#eab308",
};

const font = "'JetBrains Mono',monospace";
const fontBody = "'Outfit',sans-serif";
const tempColor = (t) => t === "Hot" ? C.hot : t === "Warm" ? C.warm : t === "Cool" ? C.cool : C.cold;
const stageLabel = { new: "New", scored: "Scored", enriched: "Enriched", researched: "Researched", outreach_ready: "Outreach Ready", engaged: "Engaged", meeting: "Meeting", proposal: "Proposal", won: "Won" };
const stageColor = { new: C.cold, scored: C.cool, enriched: C.cyan, researched: C.warm, outreach_ready: C.green, engaged: C.gold, meeting: C.purple, proposal: C.pink, won: C.green };
const stageIcon = { new: "\u25CB", scored: "\u25C9", enriched: "\u2B22", researched: "\u25C8", outreach_ready: "\u25B6", engaged: "\u2B50", meeting: "\u260E", proposal: "\u2709", won: "\u2714" };
const gradeColor = (g) => g === "A" ? C.gradeA : g === "B" ? C.gradeB : g === "C" ? C.gradeC : C.gradeD;
const formatCurrency = (n) => typeof n === "number" ? (n >= 1000000 ? "$" + (n / 1000000).toFixed(1) + "M" : n >= 1000 ? "$" + (n / 1000).toFixed(0) + "K" : "$" + n.toLocaleString()) : n || "\u2014";

// ─── ANIMATION STYLES ───────────────────────────────────────────────────────
const globalStyles = `
  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px) } to { opacity: 1; transform: translateY(0) } }
  @keyframes fadeInFast { from { opacity: 0 } to { opacity: 1 } }
  @keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.5 } }
  @keyframes slideIn { from { opacity: 0; transform: translateX(-12px) } to { opacity: 1; transform: translateX(0) } }
  @keyframes glow { 0%, 100% { box-shadow: 0 0 4px rgba(212,168,67,0.2) } 50% { box-shadow: 0 0 16px rgba(212,168,67,0.4) } }
  @keyframes countUp { from { opacity: 0; transform: scale(0.8) } to { opacity: 1; transform: scale(1) } }
  ::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:${C.void}}::-webkit-scrollbar-thumb{background:${C.border};border-radius:3px}::-webkit-scrollbar-thumb:hover{background:${C.gold}40}
  * { box-sizing: border-box; }
  body { margin: 0; background: ${C.bg}; }
`;

// ═══════════════════════════════════════════════════════════════════════════════
// SHARED COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════════

function Badge({ children, color = C.textDim, bg: bgColor, size = "sm", glow = false }) {
  const sizes = { xs: { padding: "1px 5px", fontSize: 8 }, sm: { padding: "2px 8px", fontSize: 10 }, md: { padding: "4px 12px", fontSize: 11 }, lg: { padding: "6px 16px", fontSize: 12 } };
  const s = sizes[size] || sizes.sm;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, ...s, borderRadius: 4, fontWeight: 700, fontFamily: font, letterSpacing: 0.5, color, background: bgColor || color + "18", border: "1px solid " + color + "30", textTransform: "uppercase", whiteSpace: "nowrap", boxShadow: glow ? "0 0 8px " + color + "30" : "none" }}>{children}</span>
  );
}

function StatBox({ label, value, color = C.text, sub, icon, trend, onClick, size = "md" }) {
  const sm = size === "sm";
  return (
    <div onClick={onClick} style={{ textAlign: "center", padding: sm ? "8px 10px" : "12px 16px", background: C.surface, borderRadius: 10, border: "1px solid " + C.border, minWidth: sm ? 60 : 90, cursor: onClick ? "pointer" : "default", transition: "all 0.2s", position: "relative", overflow: "hidden" }}
      onMouseEnter={e => { if (onClick) { e.currentTarget.style.borderColor = color + "60"; e.currentTarget.style.transform = "translateY(-2px)"; } }}
      onMouseLeave={e => { if (onClick) { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "translateY(0)"; } }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: "linear-gradient(90deg, transparent, " + color + "40, transparent)" }} />
      {icon && <div style={{ fontSize: sm ? 16 : 20, marginBottom: 4 }}>{icon}</div>}
      <div style={{ fontSize: sm ? 18 : 26, fontWeight: 800, color, fontFamily: font, animation: "countUp 0.4s ease-out" }}>{value}</div>
      <div style={{ fontSize: sm ? 9 : 10, color: C.textDim, textTransform: "uppercase", letterSpacing: 1, marginTop: 3 }}>{label}</div>
      {sub && <div style={{ fontSize: sm ? 9 : 10, color: C.textMuted, marginTop: 2 }}>{sub}</div>}
      {trend !== undefined && <div style={{ fontSize: 9, color: trend > 0 ? C.green : C.hot, marginTop: 2, fontFamily: font }}>{trend > 0 ? "\u25B2" : "\u25BC"} {Math.abs(trend)}%</div>}
    </div>
  );
}

function Card({ children, style, glow: glowColor, onClick, padding = 16 }) {
  return (
    <div onClick={onClick} style={{ background: C.surface, borderRadius: 10, border: "1px solid " + C.border, padding, transition: "all 0.25s", cursor: onClick ? "pointer" : "default", ...style }}
      onMouseEnter={e => { if (onClick) { e.currentTarget.style.borderColor = (glowColor || C.gold) + "50"; e.currentTarget.style.transform = "translateY(-1px)"; } }}
      onMouseLeave={e => { if (onClick) { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "translateY(0)"; } }}>
      {children}
    </div>
  );
}

function SectionHeader({ title, subtitle, action, icon }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {icon && <span style={{ fontSize: 18, opacity: 0.8 }}>{icon}</span>}
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: C.gold, fontFamily: font, letterSpacing: 2, margin: 0, textTransform: "uppercase" }}>{title}</h2>
          {subtitle && <div style={{ fontSize: 12, color: C.textDim, marginTop: 2 }}>{subtitle}</div>}
        </div>
      </div>
      {action}
    </div>
  );
}

function TabButton({ label, active, onClick, count, icon }) {
  return (
    <button onClick={onClick} style={{
      background: active ? "linear-gradient(135deg, " + C.gold + ", " + C.goldLight + ")" : "transparent",
      color: active ? C.void : C.textDim,
      border: "1px solid " + (active ? C.gold : C.border),
      padding: "7px 18px", borderRadius: 6,
      fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: font, letterSpacing: 1,
      transition: "all 0.2s", display: "flex", alignItems: "center", gap: 6,
      boxShadow: active ? "0 0 12px " + C.gold + "30" : "none",
    }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.borderColor = C.gold + "60"; }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.borderColor = active ? C.gold : C.border; }}>
      {icon && <span style={{ fontSize: 12 }}>{icon}</span>}
      {label}
      {count !== undefined && <span style={{ fontSize: 9, padding: "1px 5px", borderRadius: 8, background: active ? "rgba(0,0,0,0.2)" : C.gold + "20", color: active ? C.void : C.gold }}>{count}</span>}
    </button>
  );
}

function EmptyState({ message, action }) {
  return (
    <div style={{ padding: 60, textAlign: "center", color: C.textDim, fontSize: 13 }}>
      <div style={{ fontSize: 40, marginBottom: 16, opacity: 0.3 }}>{"\u2205"}</div>
      <div>{message}</div>
      {action && <div style={{ marginTop: 12 }}>{action}</div>}
    </div>
  );
}

function ProgressBar({ segments, height = 8, showLabels = false }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div>
      <div style={{ display: "flex", height, borderRadius: height / 2, overflow: "hidden", gap: 1, background: C.border }}>
        {segments.map((s, i) => s.value > 0 && (
          <div key={i} title={(s.label || "") + ": " + s.value} style={{ width: ((s.value / total) * 100) + "%", background: "linear-gradient(90deg, " + s.color + ", " + s.color + "cc)", minWidth: s.value > 0 ? 3 : 0, transition: "width 0.6s ease-out" }} />
        ))}
      </div>
      {showLabels && (
        <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap" }}>
          {segments.filter(s => s.value > 0).map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: C.textDim }}>
              <div style={{ width: 8, height: 8, borderRadius: 2, background: s.color }} />
              {s.label}: {s.value}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MiniChart({ data, color = C.green, width = 120, height = 32 }) {
  if (!data || data.length < 2) return null;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const points = data.map((v, i) => ((i / (data.length - 1)) * width) + "," + (height - ((v - min) / range) * height)).join(" ");
  const areaPoints = points + " " + width + "," + height + " 0," + height;
  const gradId = "mcg" + color.replace("#", "");
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <defs><linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity="0.3"/><stop offset="100%" stopColor={color} stopOpacity="0"/></linearGradient></defs>
      <polygon points={areaPoints} fill={"url(#" + gradId + ")"} />
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CircularGauge({ value, max = 100, color = C.gold, size = 64, label }) {
  const pct = Math.min(value / max, 1);
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  return (
    <div style={{ position: "relative", width: size, height: size, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={C.border} strokeWidth="4" />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth="4" strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" style={{ transition: "stroke-dashoffset 1s ease-out" }} />
      </svg>
      <div style={{ position: "absolute", textAlign: "center" }}>
        <div style={{ fontSize: size * 0.25, fontWeight: 800, color, fontFamily: font }}>{value}</div>
        {label && <div style={{ fontSize: 7, color: C.textDim, textTransform: "uppercase" }}>{label}</div>}
      </div>
    </div>
  );
}

function SearchBar({ value, onChange, placeholder }) {
  return (
    <div style={{ position: "relative" }}>
      <span style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: C.textMuted, fontSize: 14, pointerEvents: "none" }}>{"\u{1F50D}"}</span>
      <input value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder || "Search..."}
        style={{ width: "100%", background: C.surface, border: "1px solid " + C.border, borderRadius: 8, padding: "10px 14px 10px 36px", color: C.text, fontSize: 13, fontFamily: fontBody, outline: "none" }}
        onFocus={e => e.target.style.borderColor = C.gold + "60"} onBlur={e => e.target.style.borderColor = C.border} />
    </div>
  );
}

function FilterChip({ label, active, onClick, color = C.gold }) {
  return (
    <button onClick={onClick} style={{ padding: "4px 12px", borderRadius: 20, fontSize: 10, fontWeight: 600, fontFamily: font, letterSpacing: 0.5, cursor: "pointer", transition: "all 0.2s", background: active ? color + "20" : "transparent", color: active ? color : C.textDim, border: "1px solid " + (active ? color + "50" : C.border) }}>{label}</button>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// PIPELINE WAR ROOM — Revenue Intelligence + Deal Velocity + Kanban
// ═══════════════════════════════════════════════════════════════════════════════

function PipelineView({ data, onSelectCompany }) {
  const [search, setSearch] = useState("");
  const [tempFilter, setTempFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");
  const [sortBy, setSortBy] = useState("score");
  const [viewMode, setViewMode] = useState("kanban");
  const [expandedStage, setExpandedStage] = useState(null);

  if (!data) return <EmptyState message="Loading pipeline data..." />;

  const { total_companies, total_contacts, total_emails, total_verified, temperatures, brand_split, stages, forecast, hot_list, companies } = data;

  const filteredCompanies = useMemo(() => {
    let list = companies || [];
    if (search) list = list.filter(c => c.name.toLowerCase().includes(search.toLowerCase()) || (c.domain || "").toLowerCase().includes(search.toLowerCase()));
    if (tempFilter !== "all") list = list.filter(c => c.temperature === tempFilter);
    if (stageFilter !== "all") list = list.filter(c => c.stage === stageFilter);
    list = [...list].sort((a, b) => sortBy === "score" ? (b.avg_score || 0) - (a.avg_score || 0) : sortBy === "contacts" ? (b.contact_count || 0) - (a.contact_count || 0) : (a.name || "").localeCompare(b.name || ""));
    return list;
  }, [companies, search, tempFilter, stageFilter, sortBy]);

  const totalPipelineValue = forecast ? (forecast.conservative || 0) + (forecast.likely || 0) + (forecast.upside || 0) : 0;
  const conversionRate = total_companies ? ((stages || []).filter(s => s.stage === "won").reduce((a, s) => a + s.count, 0) / total_companies * 100).toFixed(1) : "0";
  const avgScore = companies && companies.length > 0 ? (companies.reduce((a, c) => a + (c.avg_score || 0), 0) / companies.length).toFixed(0) : 0;
  const hotCount = (temperatures || {}).Hot || 0;
  const warmCount = (temperatures || {}).Warm || 0;

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      {/* Revenue Intelligence Header */}
      <SectionHeader title="Pipeline War Room" subtitle={"Real-time revenue intelligence across " + (total_companies || 0) + " target companies"} icon={"\u{1F3AF}"} />

      {/* Key Metrics Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 1fr)", gap: 10, marginBottom: 20 }}>
        <StatBox label="Companies" value={total_companies || 0} color={C.text} icon={"\u{1F3E2}"} />
        <StatBox label="Contacts" value={total_contacts || 0} color={C.cyan} icon={"\u{1F465}"} />
        <StatBox label="Emails" value={total_emails || 0} color={C.green} sub={(total_verified || 0) + " verified"} />
        <StatBox label="Hot" value={hotCount} color={C.hot} icon={"\u{1F525}"} onClick={() => setTempFilter(tempFilter === "Hot" ? "all" : "Hot")} />
        <StatBox label="Warm" value={warmCount} color={C.warm} onClick={() => setTempFilter(tempFilter === "Warm" ? "all" : "Warm")} />
        <StatBox label="Avg Score" value={avgScore} color={C.gold} />
        <StatBox label="TBF" value={(brand_split || {}).TBF || 0} color={C.purple} sub="Enterprise" />
        <StatBox label="DFT" value={(brand_split || {}).DFT || 0} color={C.pink} sub="Craft" />
      </div>

      {/* Revenue Forecast Panel */}
      {forecast && (
        <Card style={{ marginBottom: 20, borderColor: C.borderGold }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2 }}>REVENUE FORECAST — 12 MONTH PROJECTION</div>
              <div style={{ fontSize: 11, color: C.textDim, marginTop: 2 }}>Based on deal models from sales intel briefs</div>
            </div>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <Badge color={C.green} size="md">Pipeline Active</Badge>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
            {[
              { tier: "Conservative", value: forecast.conservative, color: C.cool, desc: "Minimum expected revenue" },
              { tier: "Likely", value: forecast.likely, color: C.green, desc: "Expected revenue" },
              { tier: "Upside", value: forecast.upside, color: C.gold, desc: "Maximum potential" },
            ].map(f => (
              <div key={f.tier} style={{ padding: 20, background: f.color + "08", borderRadius: 10, border: "1px solid " + f.color + "25", textAlign: "center", position: "relative", overflow: "hidden" }}>
                <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 3, background: "linear-gradient(90deg, transparent, " + f.color + ", transparent)" }} />
                <div style={{ fontSize: 10, color: C.textDim, textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>{f.tier}</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: f.color, fontFamily: font, letterSpacing: -1 }}>{formatCurrency(f.value)}</div>
                <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>{f.desc}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16 }}>
            <ProgressBar segments={[
              { label: "Conservative", value: forecast.conservative || 1, color: C.cool },
              { label: "Likely", value: forecast.likely || 1, color: C.green },
              { label: "Upside", value: forecast.upside || 1, color: C.gold },
            ]} height={6} showLabels={true} />
          </div>
        </Card>
      )}

      {/* Pipeline Temperature Distribution */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
        {/* Temperature Distribution */}
        <Card>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>TEMPERATURE DISTRIBUTION</div>
          <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
            {["Hot", "Warm", "Cool", "Cold"].map(t => {
              const count = (temperatures || {})[t] || 0;
              const pct = total_companies ? ((count / total_companies) * 100).toFixed(0) : 0;
              return (
                <div key={t} style={{ flex: 1, padding: 12, background: tempColor(t) + "08", borderRadius: 8, border: "1px solid " + tempColor(t) + "20", textAlign: "center", cursor: "pointer", transition: "all 0.2s", transform: tempFilter === t ? "scale(1.05)" : "scale(1)" }} onClick={() => setTempFilter(tempFilter === t ? "all" : t)}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: tempColor(t), fontFamily: font }}>{count}</div>
                  <div style={{ fontSize: 10, color: C.textDim, marginTop: 2 }}>{t}</div>
                  <div style={{ fontSize: 9, color: C.textMuted }}>{pct}%</div>
                </div>
              );
            })}
          </div>
          <ProgressBar segments={[
            { label: "Hot", value: hotCount, color: C.hot },
            { label: "Warm", value: warmCount, color: C.warm },
            { label: "Cool", value: (temperatures || {}).Cool || 0, color: C.cool },
            { label: "Cold", value: (temperatures || {}).Cold || 0, color: C.cold },
          ]} height={10} />
        </Card>

        {/* Hot Targets — Priority Actions */}
        <Card style={{ borderColor: C.hot + "30" }}>
          <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>
            {"\u{1F525}"} PRIORITY TARGETS — IMMEDIATE ACTION
          </div>
          {(hot_list || []).slice(0, 5).map((h, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 6, marginBottom: 4, cursor: "pointer", transition: "all 0.15s", background: "transparent" }}
              onClick={() => onSelectCompany(h.company || h.name)}
              onMouseEnter={e => e.currentTarget.style.background = C.surfaceHover}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
              <div style={{ width: 28, height: 28, borderRadius: 6, background: C.hot + "15", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: C.hot, fontFamily: font, flexShrink: 0 }}>{i + 1}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{h.company || h.name}</div>
                <div style={{ fontSize: 10, color: C.textDim }}>{h.next_action || h.reason || "Engage immediately"}</div>
              </div>
              <div style={{ fontSize: 16, fontWeight: 800, color: C.hot, fontFamily: font }}>{h.score || h.avg_score || "?"}</div>
            </div>
          ))}
          {(!hot_list || hot_list.length === 0) && <div style={{ padding: 16, textAlign: "center", fontSize: 12, color: C.textDim }}>No hot targets currently</div>}
        </Card>
      </div>

      {/* View Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 6 }}>
          <FilterChip label="All" active={tempFilter === "all"} onClick={() => setTempFilter("all")} />
          <FilterChip label="Hot" active={tempFilter === "Hot"} onClick={() => setTempFilter("Hot")} color={C.hot} />
          <FilterChip label="Warm" active={tempFilter === "Warm"} onClick={() => setTempFilter("Warm")} color={C.warm} />
          <FilterChip label="Cool" active={tempFilter === "Cool"} onClick={() => setTempFilter("Cool")} color={C.cool} />
          <span style={{ width: 1, height: 20, background: C.border, margin: "0 4px" }} />
          <FilterChip label="Kanban" active={viewMode === "kanban"} onClick={() => setViewMode("kanban")} />
          <FilterChip label="Grid" active={viewMode === "grid"} onClick={() => setViewMode("grid")} />
          <FilterChip label="Table" active={viewMode === "table"} onClick={() => setViewMode("table")} />
        </div>
        <div style={{ width: 260 }}>
          <SearchBar value={search} onChange={setSearch} placeholder="Search companies..." />
        </div>
      </div>

      {/* KANBAN VIEW */}
      {viewMode === "kanban" && (
        <div style={{ display: "flex", gap: 10, overflow: "auto", paddingBottom: 16, minHeight: 400 }}>
          {(stages || []).filter(s => s.count > 0).map(stage => {
            const stageCompanies = filteredCompanies.filter(c => c.stage === stage.stage);
            const isExpanded = expandedStage === stage.stage;
            return (
              <div key={stage.stage} style={{ minWidth: 260, maxWidth: 300, flex: isExpanded ? 2 : 1, background: C.panel, borderRadius: 10, border: "1px solid " + C.border, display: "flex", flexDirection: "column", transition: "flex 0.3s" }}>
                <div style={{ padding: "12px 14px", borderBottom: "1px solid " + C.border, display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }} onClick={() => setExpandedStage(isExpanded ? null : stage.stage)}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ color: stageColor[stage.stage] || C.textDim }}>{stageIcon[stage.stage] || "\u25CB"}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: C.text, fontFamily: font }}>{stageLabel[stage.stage] || stage.stage}</span>
                  </div>
                  <Badge color={stageColor[stage.stage] || C.textDim} size="xs">{stageCompanies.length}</Badge>
                </div>
                <div style={{ flex: 1, overflow: "auto", padding: 8 }}>
                  {stageCompanies.slice(0, isExpanded ? 50 : 8).map(co => (
                    <div key={co.name} style={{ padding: "10px 12px", marginBottom: 6, background: C.surface, borderRadius: 8, border: "1px solid " + C.border, cursor: "pointer", transition: "all 0.15s", borderLeft: "3px solid " + tempColor(co.temperature) }}
                      onClick={() => onSelectCompany(co.name)}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold + "50"; e.currentTarget.style.transform = "translateX(2px)"; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.transform = "translateX(0)"; }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: C.text, lineHeight: 1.3 }}>{co.name}</div>
                        <div style={{ fontSize: 14, fontWeight: 800, color: tempColor(co.temperature), fontFamily: font, flexShrink: 0, marginLeft: 8 }}>{co.avg_score}</div>
                      </div>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        <Badge color={co.brand === "TBF" ? C.purple : C.pink} size="xs">{co.brand}</Badge>
                        <Badge color={tempColor(co.temperature)} size="xs">{co.temperature}</Badge>
                        {co.contact_count > 0 && <Badge color={C.textDim} size="xs">{co.contact_count} contacts</Badge>}
                      </div>
                      {co.brief_status === "complete" && (
                        <div style={{ marginTop: 4, fontSize: 9, color: C.green, display: "flex", alignItems: "center", gap: 4 }}>
                          {"\u2714"} Brief complete
                        </div>
                      )}
                    </div>
                  ))}
                  {stageCompanies.length === 0 && <div style={{ padding: 16, textAlign: "center", fontSize: 11, color: C.textMuted }}>No companies</div>}
                  {!isExpanded && stageCompanies.length > 8 && (
                    <div style={{ textAlign: "center", padding: 6, fontSize: 10, color: C.gold, cursor: "pointer" }} onClick={() => setExpandedStage(stage.stage)}>+{stageCompanies.length - 8} more</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* GRID VIEW */}
      {viewMode === "grid" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 10 }}>
          {filteredCompanies.map((co, idx) => (
            <Card key={co.name} onClick={() => onSelectCompany(co.name)} glow={tempColor(co.temperature)} style={{ animation: "fadeIn 0.3s ease-out", animationDelay: Math.min(idx * 0.03, 0.5) + "s", animationFillMode: "both", borderLeft: "3px solid " + tempColor(co.temperature) }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{co.name}</div>
                  <div style={{ fontSize: 11, color: C.textDim, marginTop: 2 }}>{co.domain}{co.state ? " \u00B7 " + co.state : ""}</div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                  <div style={{ fontSize: 24, fontWeight: 800, color: tempColor(co.temperature), fontFamily: font, textShadow: "0 0 16px " + tempColor(co.temperature) + "40" }}>{co.avg_score}</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 4, marginBottom: 8, flexWrap: "wrap" }}>
                <Badge color={co.brand === "TBF" ? C.purple : C.pink}>{co.brand}</Badge>
                <Badge color={stageColor[co.stage]}>{stageLabel[co.stage]}</Badge>
                <Badge color={tempColor(co.temperature)}>{co.temperature}</Badge>
              </div>
              <div style={{ display: "flex", gap: 12, fontSize: 11, color: C.textDim }}>
                <span>{co.contact_count} contacts</span>
                <span>{co.emails_verified} verified</span>
                {co.brief_status === "complete" && <span style={{ color: C.green }}>{"\u2714"} Brief</span>}
              </div>
              {co.industry && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 6 }}>{co.industry}{co.employees ? " \u00B7 " + co.employees + " emp" : ""}</div>}
            </Card>
          ))}
        </div>
      )}

      {/* TABLE VIEW */}
      {viewMode === "table" && (
        <div style={{ overflowX: "auto", borderRadius: 10, border: "1px solid " + C.border }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: C.panel }}>
                {["Company", "Score", "Temp", "Brand", "Stage", "Contacts", "Emails", "Verified", "Industry", "State"].map(h => (
                  <th key={h} style={{ padding: "10px 14px", fontSize: 10, color: C.gold, fontFamily: font, textAlign: "left", borderBottom: "1px solid " + C.border, letterSpacing: 1, cursor: "pointer" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredCompanies.map(co => (
                <tr key={co.name} style={{ cursor: "pointer", transition: "background 0.15s" }}
                  onClick={() => onSelectCompany(co.name)}
                  onMouseEnter={e => e.currentTarget.style.background = C.surfaceHover}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                  <td style={{ padding: "10px 14px", fontSize: 13, fontWeight: 600, color: C.text, borderBottom: "1px solid " + C.border + "08" }}>{co.name}</td>
                  <td style={{ padding: "10px 14px", fontSize: 14, fontWeight: 800, color: tempColor(co.temperature), fontFamily: font, borderBottom: "1px solid " + C.border + "08" }}>{co.avg_score}</td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid " + C.border + "08" }}><Badge color={tempColor(co.temperature)} size="xs">{co.temperature}</Badge></td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid " + C.border + "08" }}><Badge color={co.brand === "TBF" ? C.purple : C.pink} size="xs">{co.brand}</Badge></td>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid " + C.border + "08" }}><Badge color={stageColor[co.stage]} size="xs">{stageLabel[co.stage]}</Badge></td>
                  <td style={{ padding: "10px 14px", fontSize: 12, color: C.text, fontFamily: font, borderBottom: "1px solid " + C.border + "08" }}>{co.contact_count}</td>
                  <td style={{ padding: "10px 14px", fontSize: 12, color: C.textDim, borderBottom: "1px solid " + C.border + "08" }}>{co.emails_total}</td>
                  <td style={{ padding: "10px 14px", fontSize: 12, color: C.green, borderBottom: "1px solid " + C.border + "08" }}>{co.emails_verified}</td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: C.textDim, borderBottom: "1px solid " + C.border + "08" }}>{(co.industry || "").slice(0, 25)}</td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: C.textDim, borderBottom: "1px solid " + C.border + "08" }}>{co.state || "\u2014"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ marginTop: 12, fontSize: 11, color: C.textMuted, textAlign: "center" }}>
        Showing {filteredCompanies.length} of {(companies || []).length} companies
        {tempFilter !== "all" && " \u00B7 Filter: " + tempFilter}
        {search && " \u00B7 Search: \"" + search + "\""}
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// COMPANY DOSSIER — Full Independent Profile with Deep Intelligence
// ═══════════════════════════════════════════════════════════════════════════════

function CompanyDossier({ company, onBack }) {
  const [tab, setTab] = useState("overview");
  const co = company;
  if (!co) return null;

  const brief = co.brief_data || {};
  const tabs = [
    { id: "overview", label: "Overview", icon: "\u{1F3E2}" },
    { id: "people", label: "People", count: co.contact_count, icon: "\u{1F465}" },
    { id: "intel", label: "Intel", icon: "\u{1F575}" },
    { id: "deal", label: "Deal", icon: "\u{1F4B0}" },
    { id: "signals", label: "Signals", count: (co.signals || []).length, icon: "\u{1F4E1}" },
    { id: "outreach", label: "Outreach", icon: "\u{1F4E7}" },
  ];

  const swotData = useMemo(() => {
    if (!brief) return null;
    return {
      strengths: [
        brief.brand_positioning && "Strong brand: " + brief.brand_positioning,
        co.contact_count > 10 && co.contact_count + " contacts identified",
        co.emails_verified > 5 && co.emails_verified + " verified emails",
        brief.key_products && brief.key_products.length > 3 && "Diverse product line (" + brief.key_products.length + " products)",
      ].filter(Boolean),
      weaknesses: [
        co.supplier_intel && co.supplier_intel.switching_barriers && co.supplier_intel.switching_barriers.length > 0 && "Switching barriers: " + co.supplier_intel.switching_barriers[0],
        !brief.description && "Limited intel — brief not yet generated",
        co.emails_verified === 0 && "No verified email addresses",
      ].filter(Boolean),
      opportunities: [
        co.supplier_intel && co.supplier_intel.switching_triggers && co.supplier_intel.switching_triggers.length > 0 && co.supplier_intel.switching_triggers[0],
        brief.growth_signals && brief.growth_signals.length > 0 && brief.growth_signals[0],
        co.displacement_strategy && co.displacement_strategy.primary_angle,
      ].filter(Boolean),
      threats: [
        co.supplier_intel && co.supplier_intel.most_likely_supplier && "Incumbent: " + co.supplier_intel.most_likely_supplier,
        co.objections && co.objections.length > 0 && "Known objection: " + co.objections[0].objection,
      ].filter(Boolean),
    };
  }, [co, brief]);

  return (
    <div style={{ height: "100%", overflow: "auto", padding: 24 }}>
      {/* Back button + Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20, animation: "fadeIn 0.3s ease-out" }}>
        <button onClick={onBack} style={{ background: C.surface, border: "1px solid " + C.border, borderRadius: 8, padding: "8px 16px", color: C.textDim, cursor: "pointer", fontSize: 12, fontFamily: font, transition: "all 0.2s", display: "flex", alignItems: "center", gap: 6 }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.gold; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textDim; }}>
          {"\u2190"} Back
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <h1 style={{ fontSize: 26, fontWeight: 800, color: C.text, margin: 0 }}>{co.name}</h1>
            <span style={{ fontSize: 32, fontWeight: 800, color: tempColor(co.temperature), fontFamily: font, textShadow: "0 0 20px " + tempColor(co.temperature) + "50" }}>{co.avg_score}</span>
            <Badge color={co.brand === "TBF" ? C.purple : C.pink} size="md" glow>{co.brand}</Badge>
            <Badge color={stageColor[co.stage]} size="md">{stageLabel[co.stage]}</Badge>
            <Badge color={tempColor(co.temperature)} size="md" glow>{co.temperature}</Badge>
          </div>
          <div style={{ fontSize: 12, color: C.textDim, marginTop: 4 }}>{co.domain}{co.state ? " \u00B7 " + co.state : ""}{co.industry ? " \u00B7 " + co.industry : ""}{co.employees ? " \u00B7 " + co.employees + " employees" : ""}</div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        <StatBox label="Contacts" value={co.contact_count} color={C.text} size="sm" />
        <StatBox label="Emails" value={co.emails_total} color={C.cyan} size="sm" />
        <StatBox label="Verified" value={co.emails_verified} color={C.green} size="sm" />
        <StatBox label="Top Score" value={co.top_score} color={tempColor(co.temperature)} size="sm" />
        {brief.terpene_relevance && <StatBox label="Terp Fit" value={brief.terpene_relevance} color={brief.terpene_relevance === "HIGH" ? C.green : C.warm} size="sm" />}
        {co.brief_status === "complete" && <StatBox label="Brief" value={"\u2714"} color={C.green} size="sm" />}
        {co.deal_model && co.deal_model.likely && <StatBox label="Deal Value" value={formatCurrency(co.deal_model.likely.annual_value || co.deal_model.likely.annual_revenue)} color={C.gold} size="sm" />}
      </div>

      {/* Sub-tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, borderBottom: "1px solid " + C.border, paddingBottom: 8, overflowX: "auto" }}>
        {tabs.map(t => <TabButton key={t.id} label={t.label} count={t.count} active={tab === t.id} onClick={() => setTab(t.id)} icon={t.icon} />)}
      </div>

      {/* OVERVIEW TAB */}
      {tab === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, animation: "fadeIn 0.3s ease-out" }}>
          {/* Left column */}
          <div>
            {brief.description && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>COMPANY OVERVIEW</div>
                <div style={{ fontSize: 13, color: C.text, lineHeight: 1.7 }}>{brief.description}</div>
                {brief.founded && <div style={{ fontSize: 12, color: C.textDim, marginTop: 8 }}>Founded: {brief.founded}{brief.headquarters ? " \u00B7 " + brief.headquarters : ""}</div>}
                {brief.company_type && <div style={{ fontSize: 12, color: C.textDim }}>Type: {brief.company_type}</div>}
                {brief.estimated_revenue && <div style={{ fontSize: 12, color: C.gold, marginTop: 4 }}>Est. Revenue: {brief.estimated_revenue}</div>}
              </Card>
            )}
            {brief.key_products && brief.key_products.length > 0 && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>PRODUCTS ({brief.key_products.length})</div>
                {brief.key_products.map((p, i) => (
                  <div key={i} style={{ fontSize: 12, color: C.text, padding: "6px 0", borderBottom: i < brief.key_products.length - 1 ? "1px solid " + C.border : "none", lineHeight: 1.5, display: "flex", gap: 6 }}>
                    <span style={{ color: C.gold, flexShrink: 0 }}>{"\u2022"}</span> {p}
                  </div>
                ))}
              </Card>
            )}
            {co.extraction_methods && co.extraction_methods.length > 0 && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.cyan, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>EXTRACTION & PRODUCTS</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                  {co.extraction_methods.map(m => <Badge key={m} color={C.cyan}>{m}</Badge>)}
                </div>
                {co.product_types && co.product_types.length > 0 && (
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {co.product_types.map(p => <Badge key={p} color={C.purple}>{p}</Badge>)}
                  </div>
                )}
              </Card>
            )}

            {/* SWOT Analysis */}
            {swotData && (swotData.strengths.length > 0 || swotData.opportunities.length > 0) && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>SWOT ANALYSIS</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { key: "strengths", label: "STRENGTHS", color: C.green, icon: "\u25B2" },
                    { key: "weaknesses", label: "WEAKNESSES", color: C.hot, icon: "\u25BC" },
                    { key: "opportunities", label: "OPPORTUNITIES", color: C.cyan, icon: "\u2605" },
                    { key: "threats", label: "THREATS", color: C.warm, icon: "\u26A0" },
                  ].map(q => (
                    <div key={q.key} style={{ padding: 10, background: q.color + "06", borderRadius: 6, border: "1px solid " + q.color + "15" }}>
                      <div style={{ fontSize: 9, color: q.color, fontWeight: 700, fontFamily: font, letterSpacing: 1, marginBottom: 6 }}>{q.icon} {q.label}</div>
                      {swotData[q.key].length > 0 ? swotData[q.key].map((item, i) => (
                        <div key={i} style={{ fontSize: 10, color: C.textDim, lineHeight: 1.5, padding: "2px 0" }}>{item}</div>
                      )) : <div style={{ fontSize: 10, color: C.textMuted }}>No data yet</div>}
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Right column */}
          <div>
            {brief.recent_news && brief.recent_news.length > 0 && (
              <Card style={{ marginBottom: 16, borderColor: C.hot + "20" }}>
                <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>{"\u{1F4F0}"} RECENT NEWS</div>
                {brief.recent_news.map((n, i) => (
                  <div key={i} style={{ padding: "10px 0", borderBottom: i < brief.recent_news.length - 1 ? "1px solid " + C.border : "none" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{n.headline}</div>
                    {n.date && <div style={{ fontSize: 10, color: C.textDim, marginTop: 2 }}>{n.date}</div>}
                    {n.significance && <div style={{ fontSize: 11, color: C.textDim, marginTop: 4, lineHeight: 1.5 }}>{n.significance}</div>}
                  </div>
                ))}
              </Card>
            )}
            {brief.growth_signals && brief.growth_signals.length > 0 && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.green, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>{"\u{1F4C8}"} GROWTH SIGNALS</div>
                {brief.growth_signals.map((g, i) => (
                  <div key={i} style={{ fontSize: 12, color: C.text, padding: "6px 0", display: "flex", gap: 8, lineHeight: 1.5 }}>
                    <span style={{ color: C.green, flexShrink: 0 }}>+</span> {g}
                  </div>
                ))}
              </Card>
            )}
            {brief.brand_positioning && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>BRAND POSITIONING</div>
                <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{brief.brand_positioning}</div>
              </Card>
            )}
            {brief.decision_makers && brief.decision_makers.length > 0 && (
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.purple, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>KEY DECISION MAKERS</div>
                {brief.decision_makers.map((dm, i) => (
                  <div key={i} style={{ padding: "8px 0", borderBottom: i < brief.decision_makers.length - 1 ? "1px solid " + C.border : "none" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{dm.name || dm}</div>
                    {dm.title && <div style={{ fontSize: 11, color: C.textDim }}>{dm.title}</div>}
                    {dm.role && <div style={{ fontSize: 11, color: C.purple }}>{dm.role}</div>}
                  </div>
                ))}
              </Card>
            )}
            {!brief.description && (
              <Card style={{ borderColor: C.warm + "30", textAlign: "center", padding: 24 }}>
                <div style={{ fontSize: 13, color: C.warm, fontWeight: 600, marginBottom: 8 }}>Brief Not Yet Generated</div>
                <div style={{ fontSize: 12, color: C.textDim }}>Run: python3 scripts/sales_intel_brief_v4.py --company "{co.name}"</div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* PEOPLE TAB */}
      {tab === "people" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {co.contacts && co.contacts.length > 0 ? (
            <div>
              <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                {["C-Suite", "VP", "Director", "Manager"].map(level => {
                  const count = co.contacts.filter(c => c.decision_maker_level === level).length;
                  if (count === 0) return null;
                  const lColor = level === "C-Suite" ? C.gold : level === "VP" ? C.purple : level === "Director" ? C.cyan : C.textDim;
                  return <StatBox key={level} label={level} value={count} color={lColor} size="sm" />;
                })}
                <StatBox label="Verified" value={co.contacts.filter(c => c.email_status === "Valid" || c.email_status === "Verified").length} color={C.green} size="sm" />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 10 }}>
                {co.contacts.map((contact, i) => {
                  const dmColor = contact.decision_maker_level === "C-Suite" ? C.gold : contact.decision_maker_level === "VP" ? C.purple : contact.decision_maker_level === "Director" ? C.cyan : C.textDim;
                  return (
                    <Card key={i} style={{ borderLeft: "3px solid " + dmColor, animation: "fadeIn 0.3s ease-out", animationDelay: Math.min(i * 0.03, 0.3) + "s", animationFillMode: "both" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                          <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{contact.name || "Unknown"}</div>
                          <div style={{ fontSize: 12, color: C.textDim, marginTop: 2 }}>{contact.title || "No title"}</div>
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                          <div style={{ fontSize: 20, fontWeight: 800, color: tempColor(contact.temperature), fontFamily: font }}>{contact.score}</div>
                          <CircularGauge value={contact.score || 0} color={tempColor(contact.temperature)} size={36} />
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                        {contact.decision_maker_level && <Badge color={dmColor}>{contact.decision_maker_level}</Badge>}
                        {contact.icp_tier && <Badge color={C.textDim}>{contact.icp_tier}</Badge>}
                        {contact.temperature && <Badge color={tempColor(contact.temperature)}>{contact.temperature}</Badge>}
                      </div>
                      <div style={{ marginTop: 10, fontSize: 11, color: C.textDim }}>
                        {contact.email && <div style={{ marginBottom: 3 }}>Email: <span style={{ color: contact.email_status === "Valid" || contact.email_status === "Verified" ? C.green : C.text }}>{contact.email}</span> {contact.email_status && <Badge color={contact.email_status === "Valid" || contact.email_status === "Verified" ? C.green : C.warm} size="xs">{contact.email_status}</Badge>}</div>}
                        {contact.phone && <div style={{ marginBottom: 3 }}>Phone: <span style={{ color: C.text }}>{contact.phone}</span></div>}
                        {contact.linkedin && <div>LinkedIn: <span style={{ color: C.cyan }}>{contact.linkedin.split("/in/")[1] || contact.linkedin}</span></div>}
                      </div>
                      {contact.score_reasons && contact.score_reasons.length > 0 && (
                        <div style={{ marginTop: 8, padding: "6px 8px", background: C.gold + "08", borderRadius: 4 }}>
                          <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 3 }}>SCORE BREAKDOWN</div>
                          <div style={{ fontSize: 10, color: C.textDim }}>{contact.score_reasons.join(" \u00B7 ")}</div>
                        </div>
                      )}
                    </Card>
                  );
                })}
              </div>
            </div>
          ) : <EmptyState message="No contacts discovered yet. Run Apollo Pipeline to find contacts." />}
        </div>
      )}

      {/* INTEL TAB */}
      {tab === "intel" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, animation: "fadeIn 0.3s ease-out" }}>
          {co.supplier_intel && Object.keys(co.supplier_intel).length > 0 && (
            <Card style={{ borderColor: C.hot + "20" }}>
              <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>{"\u{1F575}"} CURRENT SUPPLIER INTEL</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 10, padding: "8px 12px", background: C.hot + "08", borderRadius: 6, borderLeft: "3px solid " + C.hot }}>{co.supplier_intel.most_likely_supplier || "Unknown"}</div>
              {co.supplier_intel.confidence && <div style={{ fontSize: 11, color: C.textDim, marginBottom: 10 }}>Confidence: <Badge color={co.supplier_intel.confidence === "HIGH" ? C.green : C.warm}>{co.supplier_intel.confidence}</Badge></div>}
              {co.supplier_intel.evidence && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 6 }}>EVIDENCE</div>
                  {co.supplier_intel.evidence.slice(0, 5).map((e, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.textDim, padding: "4px 0", lineHeight: 1.5, display: "flex", gap: 6 }}>
                      <span style={{ color: C.gold, flexShrink: 0 }}>{"\u2022"}</span> {e}
                    </div>
                  ))}
                </div>
              )}
              {co.supplier_intel.switching_triggers && (
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 10, color: C.green, fontWeight: 600, marginBottom: 4 }}>SWITCHING TRIGGERS</div>
                  {co.supplier_intel.switching_triggers.map((t, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.text, padding: "3px 0", display: "flex", gap: 6 }}>
                      <span style={{ color: C.green }}>+</span> {t}
                    </div>
                  ))}
                </div>
              )}
              {co.supplier_intel.switching_barriers && (
                <div>
                  <div style={{ fontSize: 10, color: C.hot, fontWeight: 600, marginBottom: 4 }}>SWITCHING BARRIERS</div>
                  {co.supplier_intel.switching_barriers.map((b, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.textDim, padding: "3px 0", display: "flex", gap: 6 }}>
                      <span style={{ color: C.hot }}>-</span> {b}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}
          {co.displacement_strategy && Object.keys(co.displacement_strategy).length > 0 && (
            <Card>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>{"\u{1F3AF}"} DISPLACEMENT STRATEGY</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: C.gold, marginBottom: 10, padding: "8px 12px", background: C.gold + "08", borderRadius: 6 }}>{co.displacement_strategy.primary_angle}</div>
              {co.displacement_strategy.supporting_angles && (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 10, color: C.cyan, fontWeight: 600, marginBottom: 4 }}>SUPPORTING ANGLES</div>
                  {co.displacement_strategy.supporting_angles.map((a, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.textDim, padding: "3px 0", lineHeight: 1.5 }}>{"\u25B8"} {a}</div>
                  ))}
                </div>
              )}
              {co.displacement_strategy.sample_strategy && (
                <div style={{ padding: 12, background: C.gold + "08", borderRadius: 6, border: "1px solid " + C.gold + "20" }}>
                  <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 4 }}>SAMPLE STRATEGY</div>
                  <div style={{ fontSize: 11, color: C.text, lineHeight: 1.5 }}>{co.displacement_strategy.sample_strategy}</div>
                </div>
              )}
            </Card>
          )}
          {co.pricing_intel && Object.keys(co.pricing_intel).length > 0 && (
            <Card style={{ gridColumn: "1 / -1", borderColor: C.gold + "30" }}>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>{"\u{1F4B2}"} PRICING INTELLIGENCE</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                {[
                  { label: "THEIR CURRENT COST", value: co.pricing_intel.their_likely_current_cost, color: C.hot },
                  { label: "OUR PRICING", value: co.pricing_intel.our_pricing_tier, color: C.green },
                  { label: "ADVANTAGE", value: co.pricing_intel.advantage_or_gap, color: C.gold },
                ].map(p => (
                  <div key={p.label} style={{ textAlign: "center", padding: 16, background: p.color + "08", borderRadius: 8, border: "1px solid " + p.color + "20" }}>
                    <div style={{ fontSize: 20, fontWeight: 700, color: p.color, fontFamily: font }}>{p.value || "?"}</div>
                    <div style={{ fontSize: 9, color: C.textDim, marginTop: 4, letterSpacing: 1 }}>{p.label}</div>
                  </div>
                ))}
              </div>
              {co.pricing_intel.value_justification && (
                <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6, marginTop: 12, padding: 12, background: C.panel, borderRadius: 6 }}>{co.pricing_intel.value_justification}</div>
              )}
            </Card>
          )}
          {!co.supplier_intel && !co.displacement_strategy && !co.pricing_intel && (
            <div style={{ gridColumn: "1 / -1" }}>
              <EmptyState message="No intel data yet. Run a sales intel brief to generate supplier analysis, displacement strategy, and pricing intelligence." />
            </div>
          )}
        </div>
      )}

      {/* DEAL TAB */}
      {tab === "deal" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {co.deal_model && Object.keys(co.deal_model).length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <Card>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 14 }}>{"\u{1F4B0}"} DEAL MODEL</div>
                {["conservative", "likely", "upside"].map(tier => {
                  const d = co.deal_model[tier];
                  if (!d) return null;
                  const color = tier === "conservative" ? C.cool : tier === "likely" ? C.green : tier === "upside" ? C.gold : C.textDim;
                  return (
                    <div key={tier} style={{ padding: 14, marginBottom: 8, background: color + "08", borderRadius: 8, border: "1px solid " + color + "25", position: "relative", overflow: "hidden" }}>
                      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: color }} />
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color, textTransform: "uppercase", letterSpacing: 1 }}>{tier}</div>
                        <div style={{ fontSize: 22, fontWeight: 800, color, fontFamily: font }}>{formatCurrency(d.annual_value || d.annual_revenue)}</div>
                      </div>
                      {d.initial_liters && <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>Initial: {d.initial_liters}L ({d.initial_value || "?"})</div>}
                      {d.volume_per_month && <div style={{ fontSize: 11, color: C.textDim }}>Monthly: {d.volume_per_month}L</div>}
                      {d.margin && <div style={{ fontSize: 11, color: C.textDim }}>Margin: {d.margin}</div>}
                    </div>
                  );
                })}
                {co.deal_model.timeline && (
                  <div style={{ marginTop: 10, padding: 12, background: C.panel, borderRadius: 6 }}>
                    <div style={{ fontSize: 10, color: C.cyan, fontWeight: 600, marginBottom: 4 }}>TIMELINE</div>
                    <div style={{ fontSize: 11, color: C.text, lineHeight: 1.5 }}>{co.deal_model.timeline}</div>
                  </div>
                )}
              </Card>
              {co.objections && co.objections.length > 0 && (
                <Card style={{ borderColor: C.hot + "20" }}>
                  <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 14 }}>{"\u26A0"} OBJECTION HANDLING</div>
                  {co.objections.map((obj, i) => (
                    <div key={i} style={{ padding: "10px 0", borderBottom: i < co.objections.length - 1 ? "1px solid " + C.border : "none" }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: C.hot, marginBottom: 6 }}>{"\u{1F6D1}"} {obj.objection}</div>
                      <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6, padding: "6px 10px", background: C.green + "06", borderRadius: 4, borderLeft: "2px solid " + C.green + "40" }}>{obj.response}</div>
                    </div>
                  ))}
                </Card>
              )}
            </div>
          ) : <EmptyState message="No deal model available. Generate a sales intel brief to create Conservative/Likely/Upside deal projections." />}
        </div>
      )}

      {/* SIGNALS TAB */}
      {tab === "signals" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {co.signals && co.signals.length > 0 ? (
            <div>
              <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                {(() => {
                  const cats = {};
                  co.signals.forEach(s => { cats[s.category || "other"] = (cats[s.category || "other"] || 0) + 1; });
                  return Object.entries(cats).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
                    <StatBox key={cat} label={cat} value={count} color={stageColor[cat] || C.textDim} size="sm" />
                  ));
                })()}
              </div>
              {co.signals.map((sig, i) => (
                <Card key={i} style={{ marginBottom: 6, padding: 12, borderLeft: "3px solid " + (stageColor[sig.category] || C.textDim) }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <Badge color={stageColor[sig.category] || C.textDim}>{sig.category || "signal"}</Badge>
                      <span style={{ fontSize: 13, color: C.text }}>{sig.summary || sig.type}</span>
                    </div>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <span style={{ fontSize: 11, color: C.textDim }}>{sig.timestamp ? sig.timestamp.split("T")[0] : ""}</span>
                      <Badge color={sig.decayed_score > 0.5 ? C.green : sig.decayed_score > 0.2 ? C.warm : C.cold}>{(sig.decayed_score || 0).toFixed(2)}</Badge>
                    </div>
                  </div>
                  {sig.detail && <div style={{ fontSize: 11, color: C.textDim, marginTop: 6, lineHeight: 1.5 }}>{sig.detail}</div>}
                </Card>
              ))}
            </div>
          ) : <EmptyState message="No signals detected. Run trigger monitor or free intel scan." />}
        </div>
      )}

      {/* OUTREACH TAB */}
      {tab === "outreach" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {co.outreach_bundle && Object.keys(co.outreach_bundle).length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {Object.entries(co.outreach_bundle).map(([key, content]) => {
                const isText = typeof content === "string";
                return (
                  <Card key={key} style={{ gridColumn: isText && content.length > 500 ? "1 / -1" : undefined }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2 }}>{key.toUpperCase().replace(/_/g, " ")}</div>
                      {isText && <Badge color={C.textDim} size="xs">{content.length} chars</Badge>}
                    </div>
                    {isText ? (
                      <pre style={{ fontSize: 11, color: C.text, lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word", maxHeight: 300, overflow: "auto", fontFamily: fontBody, margin: 0, padding: 10, background: C.panel, borderRadius: 6 }}>{content}</pre>
                    ) : (
                      <pre style={{ fontSize: 10, color: C.textDim, lineHeight: 1.4, whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto", fontFamily: font, margin: 0, padding: 10, background: C.panel, borderRadius: 6 }}>{JSON.stringify(content, null, 2)}</pre>
                    )}
                  </Card>
                );
              })}
            </div>
          ) : co.outreach_sequence && co.outreach_sequence.length > 0 ? (
            <div>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>OUTREACH SEQUENCE ({co.outreach_sequence.length} touches)</div>
              {co.outreach_sequence.map((touch, i) => (
                <Card key={i} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                    <Badge color={C.gold}>Touch {touch.touch || i + 1}</Badge>
                    <Badge color={C.cyan}>Day {touch.day || 0}</Badge>
                    <Badge color={C.purple}>{touch.channel || "Email"}</Badge>
                    {touch.target && <span style={{ fontSize: 12, color: C.textDim }}>To: {touch.target}</span>}
                  </div>
                  {touch.subject && <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 6 }}>Subject: {touch.subject}</div>}
                  {touch.body && <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6, whiteSpace: "pre-wrap", padding: 10, background: C.panel, borderRadius: 6 }}>{touch.body}</div>}
                </Card>
              ))}
            </div>
          ) : <EmptyState message="No outreach artifacts generated. Run kill shot bundle to generate email, LinkedIn DM, call script, and HeyGen video." />}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// TERPENE INTELLIGENCE LAB — PhD-Grade Research + Commercial Translation
// ═══════════════════════════════════════════════════════════════════════════════

function ResearchLab({ data }) {
  const [tab, setTab] = useState("matrix");
  const [selectedTerpene, setSelectedTerpene] = useState(null);
  const [selectedEffect, setSelectedEffect] = useState(null);
  const [evidenceFilter, setEvidenceFilter] = useState("all");

  if (!data) return <EmptyState message="Loading research data..." />;
  const { papers_total, highlights, synthesis, trends, gaps, matrix, businessInsights, regulatory } = data;

  const tabs = [
    { id: "matrix", label: "Effect Matrix", icon: "\u{1F9EC}" },
    { id: "evidence", label: "Evidence", icon: "\u{1F4DA}", count: (highlights || []).length },
    { id: "commercial", label: "Commercial", icon: "\u{1F4B5}", count: (businessInsights || []).length },
    { id: "mechanisms", label: "Mechanisms", icon: "\u{1F52C}" },
    { id: "gaps", label: "R&D Gaps", icon: "\u{1F50D}" },
    { id: "regulatory", label: "Regulatory", icon: "\u{2696}" , count: (regulatory || []).length },
  ];

  // Compute mechanism network from highlights
  const mechNetwork = useMemo(() => {
    if (!highlights) return [];
    const mechMap = {};
    highlights.forEach(p => {
      (p.mechanisms || []).forEach(m => {
        if (!mechMap[m]) mechMap[m] = { mechanism: m, terpenes: new Set(), papers: 0, effects: new Set(), grades: [] };
        mechMap[m].papers++;
        mechMap[m].grades.push(p.evidenceGrade);
        (p.terpenes || []).forEach(t => mechMap[m].terpenes.add(t));
        (p.effects || []).forEach(e => mechMap[m].effects.add(e));
      });
    });
    return Object.values(mechMap).sort((a, b) => b.papers - a.papers);
  }, [highlights]);

  // Compute terpene summary stats
  const terpeneStats = useMemo(() => {
    if (!highlights) return {};
    const stats = {};
    highlights.forEach(p => {
      (p.terpenes || []).forEach(t => {
        if (!stats[t]) stats[t] = { name: t, papers: 0, gradeA: 0, gradeB: 0, effects: new Set(), mechanisms: new Set() };
        stats[t].papers++;
        if (p.evidenceGrade === "A") stats[t].gradeA++;
        if (p.evidenceGrade === "B") stats[t].gradeB++;
        (p.effects || []).forEach(e => stats[t].effects.add(e));
        (p.mechanisms || []).forEach(m => stats[t].mechanisms.add(m));
      });
    });
    return stats;
  }, [highlights]);

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="Terpene Intelligence Lab" subtitle={(papers_total || 0) + " papers indexed \u00B7 PhD-grade evidence \u00B7 Commercial translation"} icon={"\u{1F9EA}"} />

      {/* Quick Stats */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        <StatBox label="Papers" value={papers_total || 0} color={C.gold} icon={"\u{1F4DA}"} />
        <StatBox label="Grade A" value={highlights ? highlights.filter(h => h.evidenceGrade === "A").length : 0} color={C.gradeA} sub="Meta/Systematic" />
        <StatBox label="Grade B" value={highlights ? highlights.filter(h => h.evidenceGrade === "B").length : 0} color={C.gradeB} sub="RCT/Cohort" />
        <StatBox label="Terpenes" value={Object.keys(terpeneStats).length} color={C.purple} />
        <StatBox label="Mechanisms" value={mechNetwork.length} color={C.cyan} />
        <StatBox label="Insights" value={(businessInsights || []).length} color={C.warm} sub="Commercial" />
        <StatBox label="Regulatory" value={(regulatory || []).length} color={C.hot} sub="Alerts" />
      </div>

      <div style={{ display: "flex", gap: 4, marginBottom: 20, overflowX: "auto" }}>
        {tabs.map(t => <TabButton key={t.id} label={t.label} active={tab === t.id} onClick={() => setTab(t.id)} count={t.count} icon={t.icon} />)}
      </div>

      {/* TERPENE-EFFECT MATRIX */}
      {tab === "matrix" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {matrix ? (
            <div>
              {/* Terpene Quick Cards */}
              <div style={{ display: "flex", gap: 8, marginBottom: 16, overflowX: "auto", paddingBottom: 8 }}>
                {Object.keys(terpeneStats).sort((a, b) => terpeneStats[b].papers - terpeneStats[a].papers).slice(0, 12).map(t => {
                  const s = terpeneStats[t];
                  const isSelected = selectedTerpene === t;
                  return (
                    <div key={t} onClick={() => setSelectedTerpene(isSelected ? null : t)} style={{ minWidth: 120, padding: "10px 14px", background: isSelected ? C.green + "15" : C.surface, borderRadius: 8, border: "1px solid " + (isSelected ? C.green + "50" : C.border), cursor: "pointer", transition: "all 0.2s", flexShrink: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{t.replace(/_/g, " ")}</div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: C.green, fontFamily: font, marginTop: 4 }}>{s.papers}</div>
                      <div style={{ fontSize: 9, color: C.textDim }}>papers</div>
                      <div style={{ display: "flex", gap: 3, marginTop: 4 }}>
                        {s.gradeA > 0 && <Badge color={C.gradeA} size="xs">{s.gradeA}A</Badge>}
                        {s.gradeB > 0 && <Badge color={C.gradeB} size="xs">{s.gradeB}B</Badge>}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Main Matrix */}
              <Card style={{ overflow: "auto" }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>TERPENE x EFFECT EVIDENCE MATRIX</div>
                <div style={{ fontSize: 10, color: C.textDim, marginBottom: 12 }}>Cell values = paper count. Color intensity = evidence strength. Click cells to explore.</div>
                {(() => {
                  const terpenes = Object.keys(matrix).sort((a, b) => {
                    const aTotal = Object.values(matrix[a] || {}).reduce((s, v) => s + v, 0);
                    const bTotal = Object.values(matrix[b] || {}).reduce((s, v) => s + v, 0);
                    return bTotal - aTotal;
                  });
                  if (terpenes.length === 0) return <EmptyState message="No matrix data available." />;
                  const allEffects = new Set();
                  terpenes.forEach(t => Object.keys(matrix[t] || {}).forEach(e => allEffects.add(e)));
                  const effects = Array.from(allEffects).sort();
                  const maxVal = Math.max(1, ...terpenes.flatMap(t => effects.map(e => (matrix[t] || {})[e] || 0)));
                  return (
                    <div style={{ overflowX: "auto" }}>
                      <table style={{ borderCollapse: "collapse", width: "100%", minWidth: effects.length * 80 }}>
                        <thead>
                          <tr>
                            <th style={{ padding: "8px 10px", fontSize: 10, color: C.gold, fontFamily: font, textAlign: "left", borderBottom: "2px solid " + C.border, position: "sticky", left: 0, background: C.surface, zIndex: 1, minWidth: 100 }}>TERPENE</th>
                            {effects.map(e => (
                              <th key={e} style={{ padding: "8px 6px", fontSize: 9, color: selectedEffect === e ? C.cyan : C.textDim, fontFamily: font, textAlign: "center", borderBottom: "2px solid " + C.border, textTransform: "uppercase", letterSpacing: 0.5, cursor: "pointer", background: selectedEffect === e ? C.cyan + "08" : "transparent" }}
                                onClick={() => setSelectedEffect(selectedEffect === e ? null : e)}>
                                {e.replace(/_/g, " ").slice(0, 15)}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {terpenes.filter(t => !selectedTerpene || t === selectedTerpene).map(terp => (
                            <tr key={terp} style={{ background: selectedTerpene === terp ? C.green + "06" : "transparent" }}>
                              <td style={{ padding: "8px 10px", fontSize: 11, color: C.text, fontWeight: 600, borderBottom: "1px solid " + C.border, position: "sticky", left: 0, background: C.surface, zIndex: 1, textTransform: "capitalize", cursor: "pointer" }}
                                onClick={() => setSelectedTerpene(selectedTerpene === terp ? null : terp)}>
                                {terp.replace(/_/g, " ")}
                              </td>
                              {effects.map(eff => {
                                const val = (matrix[terp] || {})[eff] || 0;
                                const intensity = val / maxVal;
                                const bg = val > 0 ? "rgba(0, 224, 154, " + (0.06 + intensity * 0.4) + ")" : "transparent";
                                return (
                                  <td key={eff} style={{ padding: "8px 6px", textAlign: "center", fontSize: 12, fontWeight: val > 0 ? 700 : 400, color: val > 0 ? C.green : C.textMuted, fontFamily: font, borderBottom: "1px solid " + C.border, background: bg, transition: "all 0.2s", cursor: val > 0 ? "pointer" : "default" }}>
                                    {val || ""}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  );
                })()}
              </Card>
            </div>
          ) : <EmptyState message="Run terpene research to build the evidence matrix." />}
        </div>
      )}

      {/* EVIDENCE DASHBOARD */}
      {tab === "evidence" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {highlights && highlights.length > 0 ? (
            <div>
              {/* Grade Distribution */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
                {["A", "B", "C", "D"].map(grade => {
                  const count = highlights.filter(h => h.evidenceGrade === grade).length;
                  const pct = ((count / highlights.length) * 100).toFixed(0);
                  const isActive = evidenceFilter === grade;
                  return (
                    <div key={grade} onClick={() => setEvidenceFilter(isActive ? "all" : grade)} style={{ background: isActive ? gradeColor(grade) + "15" : C.surface, borderRadius: 10, border: "1px solid " + gradeColor(grade) + (isActive ? "50" : "20"), padding: 14, textAlign: "center", cursor: "pointer", transition: "all 0.2s" }}>
                      <div style={{ fontSize: 28, fontWeight: 800, color: gradeColor(grade), fontFamily: font }}>{count}</div>
                      <div style={{ fontSize: 10, color: C.textDim, marginTop: 2 }}>GRADE {grade}</div>
                      <div style={{ fontSize: 9, color: C.textMuted }}>{grade === "A" ? "Meta/Systematic" : grade === "B" ? "RCT/Cohort" : grade === "C" ? "Animal In Vivo" : "In Vitro"}</div>
                      <div style={{ fontSize: 9, color: C.textMuted, marginTop: 2 }}>{pct}% of total</div>
                    </div>
                  );
                })}
              </div>

              {/* Filters */}
              <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
                <FilterChip label="All" active={evidenceFilter === "all"} onClick={() => setEvidenceFilter("all")} />
                {["A", "B", "C", "D"].map(g => (
                  <FilterChip key={g} label={"Grade " + g} active={evidenceFilter === g} onClick={() => setEvidenceFilter(evidenceFilter === g ? "all" : g)} color={gradeColor(g)} />
                ))}
              </div>

              {/* Paper List */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
                {highlights
                  .filter(p => evidenceFilter === "all" || p.evidenceGrade === evidenceFilter)
                  .slice(0, 30)
                  .map((paper, i) => (
                  <Card key={i} style={{ padding: 14, borderLeft: "3px solid " + gradeColor(paper.evidenceGrade), animation: "fadeIn 0.3s ease-out", animationDelay: Math.min(i * 0.02, 0.3) + "s", animationFillMode: "both" }}>
                    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                      <div style={{ width: 40, height: 40, borderRadius: 8, background: gradeColor(paper.evidenceGrade) + "15", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, fontWeight: 800, color: gradeColor(paper.evidenceGrade), fontFamily: font, flexShrink: 0 }}>{paper.evidenceGrade}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.4, marginBottom: 4 }}>{paper.title}</div>
                        <div style={{ fontSize: 11, color: C.textDim }}>{paper.journal} ({paper.year}) \u00B7 {paper.studyType} \u00B7 {paper.modelOrganism}</div>
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
                          {(paper.terpenes || []).map(t => <Badge key={t} color={C.green}>{t}</Badge>)}
                          {(paper.effects || []).map(e => <Badge key={e} color={C.cyan}>{e.replace(/_/g, " ")}</Badge>)}
                          {paper.outcomeDirection && <Badge color={paper.outcomeDirection === "positive" ? C.green : paper.outcomeDirection === "negative" ? C.hot : C.textDim}>{paper.outcomeDirection}</Badge>}
                        </div>
                        {paper.mechanisms && paper.mechanisms.length > 0 && (
                          <div style={{ fontSize: 10, color: C.purple, marginTop: 6 }}>{"\u{1F52C}"} Mechanisms: {paper.mechanisms.join(", ")}</div>
                        )}
                        {paper.dose && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>Dose: {paper.dose}</div>}
                      </div>
                      <div style={{ textAlign: "right", flexShrink: 0 }}>
                        <div style={{ fontSize: 16, fontWeight: 700, color: C.gold, fontFamily: font }}>{paper.score}</div>
                        <div style={{ fontSize: 9, color: C.textDim }}>score</div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
              {highlights.filter(p => evidenceFilter === "all" || p.evidenceGrade === evidenceFilter).length > 30 && (
                <div style={{ textAlign: "center", padding: 16, fontSize: 12, color: C.textDim }}>
                  Showing 30 of {highlights.filter(p => evidenceFilter === "all" || p.evidenceGrade === evidenceFilter).length} papers
                </div>
              )}
            </div>
          ) : <EmptyState message="No papers indexed yet. Run terpene research to harvest papers." />}
        </div>
      )}

      {/* COMMERCIAL TRANSLATOR */}
      {tab === "commercial" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {businessInsights && businessInsights.length > 0 ? (
            <div>
              <Card style={{ marginBottom: 16, borderColor: C.gold + "30", padding: 14 }}>
                <div style={{ fontSize: 12, color: C.gold, fontWeight: 600 }}>{"\u{1F6E1}"} These insights translate peer-reviewed research into compliance-safe selling points. No medical claims \u2014 only consumer preference and formulation-level framing.</div>
              </Card>

              {/* Insight Type Summary */}
              <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
                {[
                  { type: "weekly_bet", label: "Weekly Bets", color: C.gold },
                  { type: "trend_alert", label: "Trend Alerts", color: C.cyan },
                  { type: "rd_opportunity", label: "R&D Opportunities", color: C.purple },
                ].map(t => (
                  <StatBox key={t.type} label={t.label} value={businessInsights.filter(i => i.type === t.type).length} color={t.color} size="sm" />
                ))}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 14 }}>
                {businessInsights.map((ins, i) => {
                  const typeColor = ins.type === "weekly_bet" ? C.gold : ins.type === "trend_alert" ? C.cyan : C.purple;
                  const typeLabel = ins.type === "weekly_bet" ? "WEEKLY BET" : ins.type === "trend_alert" ? "TREND ALERT" : "R&D OPPORTUNITY";
                  return (
                    <Card key={i} style={{ borderLeft: "4px solid " + typeColor, animation: "fadeIn 0.3s ease-out", animationDelay: Math.min(i * 0.05, 0.3) + "s", animationFillMode: "both" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <Badge color={typeColor} size="md">{typeLabel}</Badge>
                          <span style={{ fontSize: 16, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{ins.terpene}</span>
                          <Badge color={C.textDim}>{ins.category}</Badge>
                        </div>
                        <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
                          <span style={{ fontSize: 9, color: C.textDim, marginRight: 4 }}>Confidence:</span>
                          {Array.from({ length: 6 }, (_, j) => (
                            <div key={j} style={{ width: 8, height: 8, borderRadius: 2, background: j < (ins.confidence || 0) ? typeColor : C.border }} />
                          ))}
                        </div>
                      </div>
                      <div style={{ fontSize: 14, color: C.text, lineHeight: 1.7, marginBottom: 12, padding: "10px 14px", background: C.green + "06", borderRadius: 8, borderLeft: "3px solid " + C.green + "40", fontStyle: "italic" }}>
                        "{ins.safe_framing}"
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                        <div>
                          <div style={{ fontSize: 10, color: C.cyan, fontWeight: 700, fontFamily: font, letterSpacing: 1, marginBottom: 6 }}>PRODUCT ANGLE</div>
                          <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{ins.product_angle}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: 10, color: C.warm, fontWeight: 700, fontFamily: font, letterSpacing: 1, marginBottom: 6 }}>SALES ANGLE</div>
                          <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{ins.sales_angle}</div>
                        </div>
                      </div>
                      <div style={{ marginTop: 10, padding: "8px 12px", background: C.gold + "08", borderRadius: 6, border: "1px solid " + C.gold + "15" }}>
                        <div style={{ fontSize: 10, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 1 }}>WHY WE CAN SAY IT</div>
                        <div style={{ fontSize: 11, color: C.textDim, marginTop: 3, lineHeight: 1.5 }}>{ins.why_we_can_say_it}</div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          ) : <EmptyState message="No business insights available. Run terpene research with --synthesize." />}
        </div>
      )}

      {/* MECHANISMS */}
      {tab === "mechanisms" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {mechNetwork.length > 0 ? (
            <div>
              <div style={{ fontSize: 12, color: C.textDim, marginBottom: 16 }}>
                {mechNetwork.length} unique mechanisms identified across {papers_total} papers. Showing interconnections between terpenes, mechanisms, and effects.
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))", gap: 12 }}>
                {mechNetwork.slice(0, 24).map((m, i) => {
                  const bestGrade = m.grades.includes("A") ? "A" : m.grades.includes("B") ? "B" : m.grades.includes("C") ? "C" : "D";
                  return (
                    <Card key={m.mechanism} style={{ borderLeft: "3px solid " + C.purple, animation: "fadeIn 0.3s ease-out", animationDelay: Math.min(i * 0.03, 0.3) + "s", animationFillMode: "both" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: C.purple, textTransform: "capitalize" }}>{m.mechanism.replace(/_/g, " ")}</div>
                        <div style={{ display: "flex", gap: 4 }}>
                          <Badge color={gradeColor(bestGrade)} size="xs">Best: {bestGrade}</Badge>
                          <Badge color={C.textDim} size="xs">{m.papers} papers</Badge>
                        </div>
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 4, fontFamily: font }}>TERPENES</div>
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                          {Array.from(m.terpenes).map(t => <Badge key={t} color={C.green}>{t}</Badge>)}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: 10, color: C.cyan, fontWeight: 600, marginBottom: 4, fontFamily: font }}>EFFECTS</div>
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                          {Array.from(m.effects).slice(0, 6).map(e => <Badge key={e} color={C.cyan}>{e.replace(/_/g, " ")}</Badge>)}
                          {Array.from(m.effects).length > 6 && <Badge color={C.textDim}>+{Array.from(m.effects).length - 6}</Badge>}
                        </div>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          ) : <EmptyState message="No mechanism data extracted yet." />}
        </div>
      )}

      {/* R&D GAPS */}
      {tab === "gaps" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {gaps ? (
            <div>
              {gaps.underweighted_by_tbf && gaps.underweighted_by_tbf.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 11, color: C.purple, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>{"\u{1F4A1}"} UNDERWEIGHTED TERPENES (Research {">"} Product Focus)</div>
                  <div style={{ fontSize: 11, color: C.textDim, marginBottom: 12 }}>These terpenes have strong research backing but are under-represented in TBF's product lineup. Consider expanding.</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10 }}>
                    {gaps.underweighted_by_tbf.slice(0, 10).map((g, i) => (
                      <Card key={i} style={{ borderColor: C.purple + "30" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                          <div style={{ fontSize: 15, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{(g.terpene || "").replace(/_/g, " ")}</div>
                          <Badge color={C.purple} size="md">Gap: {(g.gap_score || 0).toFixed(4)}</Badge>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                          <span style={{ fontSize: 11, color: C.textDim }}>Evidence: {g.evidence_share || 0} papers</span>
                          <span style={{ fontSize: 11, color: C.textDim }}>Product: {g.tbf_focus_units || 0} lines</span>
                        </div>
                        <ProgressBar segments={[
                          { label: "Evidence", value: g.evidence_share || 1, color: C.purple },
                          { label: "Product", value: g.tbf_focus_units || 0.1, color: C.gold },
                        ]} height={6} showLabels />
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              {gaps.overweighted_by_tbf && gaps.overweighted_by_tbf.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>{"\u26A0"} OVERWEIGHTED TERPENES (Product Focus {">"} Research)</div>
                  <div style={{ fontSize: 11, color: C.textDim, marginBottom: 12 }}>These terpenes have more product focus than research backing. Monitor for evidence gaps.</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10 }}>
                    {gaps.overweighted_by_tbf.slice(0, 8).map((g, i) => (
                      <Card key={i} style={{ borderColor: C.gold + "30" }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{(g.terpene || "").replace(/_/g, " ")}</div>
                        <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>Product focus exceeds evidence base</div>
                        {g.gap_score && <Badge color={C.gold} size="xs">Gap: {g.gap_score.toFixed(4)}</Badge>}
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : <EmptyState message="Run gap analysis to identify R&D opportunities." />}
        </div>
      )}

      {/* REGULATORY */}
      {tab === "regulatory" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {regulatory && regulatory.length > 0 ? (
            <div>
              <Card style={{ marginBottom: 16, borderColor: C.hot + "20", padding: 14 }}>
                <div style={{ fontSize: 12, color: C.hot, fontWeight: 600 }}>{"\u26A0"} Regulatory intelligence from {regulatory.length} sources. Review for compliance before using in outreach.</div>
              </Card>
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
                {regulatory.map((r, i) => (
                  <Card key={i} style={{ padding: 14, borderLeft: "3px solid " + C.hot }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>{r.title || r.topic || "Regulatory Hit"}</div>
                    <div style={{ fontSize: 11, color: C.textDim, lineHeight: 1.6 }}>{r.summary || r.detail || JSON.stringify(r)}</div>
                    {r.terpenes && <div style={{ display: "flex", gap: 4, marginTop: 8 }}>{r.terpenes.map(t => <Badge key={t} color={C.hot}>{t}</Badge>)}</div>}
                    {r.jurisdiction && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>Jurisdiction: {r.jurisdiction}</div>}
                    {r.date && <div style={{ fontSize: 10, color: C.textMuted }}>Date: {r.date}</div>}
                  </Card>
                ))}
              </div>
            </div>
          ) : <EmptyState message="No regulatory signals found." />}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// COMPETITOR INTELLIGENCE — Deep Competitive Analysis
// ═══════════════════════════════════════════════════════════════════════════════

function CompetitorIntel({ data }) {
  const [selectedCompetitor, setSelectedCompetitor] = useState(null);
  const [tab, setTab] = useState("overview");

  if (!data) return <EmptyState message="Loading competitor data..." />;
  const { competitors, market_position, vulnerability_scan } = data;

  if (!competitors || competitors.length === 0) return <EmptyState message="No competitor data available." />;

  const selected = selectedCompetitor ? competitors.find(c => c.name === selectedCompetitor) : null;

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="Competitor Intelligence" subtitle={(competitors || []).length + " competitors tracked \u00B7 Pricing, weaknesses, displacement angles"} icon={"\u{1F575}"} />

      {/* Competitor Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12, marginBottom: 20 }}>
        {competitors.map((comp, i) => {
          const isSelected = selectedCompetitor === comp.name;
          const threatColor = comp.threat_level === "HIGH" ? C.hot : comp.threat_level === "MEDIUM" ? C.warm : C.green;
          return (
            <Card key={comp.name} onClick={() => setSelectedCompetitor(isSelected ? null : comp.name)}
              style={{ borderColor: isSelected ? threatColor + "50" : C.border, borderLeft: "4px solid " + threatColor, animation: "fadeIn 0.3s ease-out", animationDelay: i * 0.05 + "s", animationFillMode: "both" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: C.text }}>{comp.name}</div>
                  <div style={{ fontSize: 11, color: C.textDim, marginTop: 2 }}>{comp.category || comp.market_segment || "Terpene Supplier"}</div>
                </div>
                <Badge color={threatColor} size="md" glow>{comp.threat_level || "MEDIUM"}</Badge>
              </div>

              {comp.pricing && (
                <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                  {comp.pricing.low && <div style={{ fontSize: 10, color: C.textDim }}>{comp.pricing.low} - {comp.pricing.high}/L</div>}
                  {comp.pricing.avg && <div style={{ fontSize: 10, color: C.gold }}>Avg: {comp.pricing.avg}/L</div>}
                </div>
              )}

              {comp.weaknesses && comp.weaknesses.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 9, color: C.hot, fontWeight: 600, marginBottom: 3, fontFamily: font }}>WEAKNESSES</div>
                  {comp.weaknesses.slice(0, 2).map((w, j) => (
                    <div key={j} style={{ fontSize: 10, color: C.textDim, lineHeight: 1.4, display: "flex", gap: 4 }}>
                      <span style={{ color: C.hot }}>{"\u2022"}</span> {typeof w === "string" ? w : w.weakness || w.description || JSON.stringify(w)}
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                {comp.extraction_types && comp.extraction_types.map(e => <Badge key={e} color={C.cyan} size="xs">{e}</Badge>)}
                {comp.certifications && comp.certifications.map(c => <Badge key={c} color={C.green} size="xs">{c}</Badge>)}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Selected Competitor Deep Dive */}
      {selected && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          <Card style={{ marginBottom: 16, borderColor: C.gold + "30" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 20, fontWeight: 700, color: C.text }}>{selected.name} \u2014 Deep Dive</div>
                <div style={{ fontSize: 12, color: C.textDim }}>{selected.website || selected.url || ""}</div>
              </div>
              <button onClick={() => setSelectedCompetitor(null)} style={{ background: C.surface, border: "1px solid " + C.border, borderRadius: 6, padding: "6px 14px", color: C.textDim, cursor: "pointer", fontSize: 11, fontFamily: font }}>Close</button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {/* Pricing Deep Dive */}
              {selected.pricing && (
                <div style={{ padding: 14, background: C.panel, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>PRICING MODEL</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: C.green, fontFamily: font }}>{selected.pricing.low || "?"}</div>
                      <div style={{ fontSize: 9, color: C.textDim }}>LOW</div>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: C.gold, fontFamily: font }}>{selected.pricing.avg || "?"}</div>
                      <div style={{ fontSize: 9, color: C.textDim }}>AVG</div>
                    </div>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 16, fontWeight: 700, color: C.hot, fontFamily: font }}>{selected.pricing.high || "?"}</div>
                      <div style={{ fontSize: 9, color: C.textDim }}>HIGH</div>
                    </div>
                  </div>
                  {selected.pricing.model && <div style={{ fontSize: 11, color: C.textDim, marginTop: 8 }}>Model: {selected.pricing.model}</div>}
                  {selected.pricing.moq && <div style={{ fontSize: 11, color: C.textDim }}>MOQ: {selected.pricing.moq}</div>}
                </div>
              )}

              {/* TBF Angle */}
              {selected.tbf_angle && (
                <div style={{ padding: 14, background: C.purple + "08", borderRadius: 8, border: "1px solid " + C.purple + "15" }}>
                  <div style={{ fontSize: 11, color: C.purple, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>TBF DISPLACEMENT ANGLE</div>
                  <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{selected.tbf_angle}</div>
                </div>
              )}

              {/* DFT Angle */}
              {selected.dft_angle && (
                <div style={{ padding: 14, background: C.pink + "08", borderRadius: 8, border: "1px solid " + C.pink + "15" }}>
                  <div style={{ fontSize: 11, color: C.pink, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>DFT DISPLACEMENT ANGLE</div>
                  <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{selected.dft_angle}</div>
                </div>
              )}

              {/* Full Weaknesses */}
              {selected.weaknesses && selected.weaknesses.length > 0 && (
                <div style={{ padding: 14, background: C.hot + "06", borderRadius: 8, border: "1px solid " + C.hot + "15" }}>
                  <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>WEAKNESSES ({selected.weaknesses.length})</div>
                  {selected.weaknesses.map((w, j) => (
                    <div key={j} style={{ fontSize: 11, color: C.text, padding: "4px 0", lineHeight: 1.5, display: "flex", gap: 6 }}>
                      <span style={{ color: C.hot }}>{"\u2022"}</span> {typeof w === "string" ? w : w.weakness || JSON.stringify(w)}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Vulnerability Scan */}
            {selected.vuln_data && (
              <div style={{ marginTop: 16, padding: 14, background: C.panel, borderRadius: 8 }}>
                <div style={{ fontSize: 11, color: C.warn, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>{"\u{1F6E1}"} VULNERABILITY SCAN</div>
                <pre style={{ fontSize: 11, color: C.textDim, lineHeight: 1.5, whiteSpace: "pre-wrap", fontFamily: font, margin: 0 }}>{JSON.stringify(selected.vuln_data, null, 2)}</pre>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Market Position Overview */}
      {market_position && (
        <Card style={{ marginTop: 16 }}>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>MARKET LANDSCAPE</div>
          <pre style={{ fontSize: 11, color: C.textDim, lineHeight: 1.5, whiteSpace: "pre-wrap", fontFamily: fontBody, margin: 0 }}>
            {typeof market_position === "string" ? market_position : JSON.stringify(market_position, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SIGNAL INTELLIGENCE — Real-time Signal Feed with Filtering
// ═══════════════════════════════════════════════════════════════════════════════

function SignalIntel({ data, onSelectCompany }) {
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [search, setSearch] = useState("");

  if (!data) return <EmptyState message="Loading signals..." />;

  const signals = data.signals || [];
  const signalWeights = data.signal_weights || {};

  const categories = useMemo(() => {
    const cats = {};
    signals.forEach(s => { cats[s.category || "other"] = (cats[s.category || "other"] || 0) + 1; });
    return Object.entries(cats).sort((a, b) => b[1] - a[1]);
  }, [signals]);

  const filtered = useMemo(() => {
    let list = signals;
    if (categoryFilter !== "all") list = list.filter(s => s.category === categoryFilter);
    if (search) list = list.filter(s => JSON.stringify(s).toLowerCase().includes(search.toLowerCase()));
    return list.sort((a, b) => (b.decayed_score || 0) - (a.decayed_score || 0));
  }, [signals, categoryFilter, search]);

  const avgDecay = signals.length > 0 ? (signals.reduce((a, s) => a + (s.decayed_score || 0), 0) / signals.length).toFixed(3) : 0;

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="Signal Intelligence" subtitle={signals.length + " signals detected \u00B7 Exponential decay scoring \u00B7 Real-time monitoring"} icon={"\u{1F4E1}"} />

      {/* Stats */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        <StatBox label="Total Signals" value={signals.length} color={C.gold} icon={"\u{1F4E1}"} />
        <StatBox label="Categories" value={categories.length} color={C.cyan} />
        <StatBox label="Avg Decay" value={avgDecay} color={C.green} />
        <StatBox label="High Score" value={signals.length > 0 ? Math.max(...signals.map(s => s.decayed_score || 0)).toFixed(2) : 0} color={C.hot} />
      </div>

      {/* Signal Weight Reference */}
      {Object.keys(signalWeights).length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>SIGNAL WEIGHTS & DECAY</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {Object.entries(signalWeights).sort((a, b) => b[1] - a[1]).map(([type, weight]) => (
              <div key={type} style={{ padding: "4px 10px", background: C.surface, borderRadius: 4, border: "1px solid " + C.border, display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 10, color: C.textDim, textTransform: "capitalize" }}>{type.replace(/_/g, " ")}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: weight > 0.7 ? C.hot : weight > 0.4 ? C.warm : C.cool, fontFamily: font }}>{weight.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Filters */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <FilterChip label="All" active={categoryFilter === "all"} onClick={() => setCategoryFilter("all")} />
          {categories.map(([cat, count]) => (
            <FilterChip key={cat} label={cat + " (" + count + ")"} active={categoryFilter === cat} onClick={() => setCategoryFilter(categoryFilter === cat ? "all" : cat)} />
          ))}
        </div>
        <div style={{ width: 220 }}>
          <SearchBar value={search} onChange={setSearch} placeholder="Search signals..." />
        </div>
      </div>

      {/* Signal Feed */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 6 }}>
        {filtered.slice(0, 50).map((sig, i) => {
          const scoreColor = sig.decayed_score > 0.5 ? C.green : sig.decayed_score > 0.2 ? C.warm : C.cold;
          return (
            <Card key={i} style={{ padding: 12, borderLeft: "3px solid " + scoreColor, animation: "fadeIn 0.2s ease-out", animationDelay: Math.min(i * 0.02, 0.3) + "s", animationFillMode: "both" }}
              onClick={sig.company ? () => onSelectCompany(sig.company) : undefined}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}>
                  <Badge color={stageColor[sig.category] || C.textDim}>{sig.category || "signal"}</Badge>
                  <span style={{ fontSize: 13, color: C.text, flex: 1 }}>{sig.summary || sig.type}</span>
                  {sig.company && <Badge color={C.gold} size="xs">{sig.company}</Badge>}
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0, marginLeft: 12 }}>
                  {sig.timestamp && <span style={{ fontSize: 10, color: C.textDim }}>{sig.timestamp.split("T")[0]}</span>}
                  <div style={{ minWidth: 48, textAlign: "right" }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: scoreColor, fontFamily: font }}>{(sig.decayed_score || 0).toFixed(2)}</span>
                  </div>
                </div>
              </div>
              {sig.detail && <div style={{ fontSize: 11, color: C.textDim, marginTop: 4, lineHeight: 1.4, paddingLeft: 4 }}>{sig.detail}</div>}
            </Card>
          );
        })}
      </div>
      {filtered.length > 50 && (
        <div style={{ textAlign: "center", padding: 16, fontSize: 12, color: C.textDim }}>Showing 50 of {filtered.length} signals</div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// ANALYTICS DASHBOARD — System Performance + Intelligence Metrics
// ═══════════════════════════════════════════════════════════════════════════════

function AnalyticsDashboard({ data }) {
  const [tab, setTab] = useState("pipeline");

  if (!data) return <EmptyState message="Loading analytics..." />;

  const { pipeline_health, intelligence_metrics, system_stats, learning_metrics } = data;
  const ph = pipeline_health || {};
  const im = intelligence_metrics || {};
  const ss = system_stats || {};
  const lm = learning_metrics || {};

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="Analytics & Performance" subtitle="System metrics, pipeline health, intelligence performance" icon={"\u{1F4CA}"} />

      <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
        <TabButton label="Pipeline Health" active={tab === "pipeline"} onClick={() => setTab("pipeline")} icon={"\u{1F3AF}"} />
        <TabButton label="Intelligence" active={tab === "intelligence"} onClick={() => setTab("intelligence")} icon={"\u{1F9E0}"} />
        <TabButton label="System" active={tab === "system"} onClick={() => setTab("system")} icon={"\u{2699}"} />
      </div>

      {/* PIPELINE HEALTH */}
      {tab === "pipeline" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 10, marginBottom: 20 }}>
            <StatBox label="Total Leads" value={ph.total_leads || 0} color={C.text} icon={"\u{1F465}"} />
            <StatBox label="Companies" value={ph.total_companies || 0} color={C.gold} />
            <StatBox label="Scored" value={ph.scored || 0} color={C.cool} />
            <StatBox label="Hot" value={ph.hot || 0} color={C.hot} icon={"\u{1F525}"} />
            <StatBox label="Warm" value={ph.warm || 0} color={C.warm} />
            <StatBox label="Conversion" value={(ph.conversion_rate || 0) + "%"} color={C.green} />
          </div>

          {/* Stage Funnel */}
          <Card style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 14 }}>PIPELINE FUNNEL</div>
            {(ph.stage_breakdown || []).map((stage, i) => {
              const maxCount = Math.max(...(ph.stage_breakdown || []).map(s => s.count || 0), 1);
              const pct = ((stage.count || 0) / maxCount) * 100;
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
                  <div style={{ width: 120, fontSize: 11, color: C.textDim, textAlign: "right", fontFamily: font }}>{stageLabel[stage.stage] || stage.stage}</div>
                  <div style={{ flex: 1, height: 24, background: C.panel, borderRadius: 4, overflow: "hidden", position: "relative" }}>
                    <div style={{ width: pct + "%", height: "100%", background: "linear-gradient(90deg, " + (stageColor[stage.stage] || C.textDim) + ", " + (stageColor[stage.stage] || C.textDim) + "88)", borderRadius: 4, transition: "width 0.8s ease-out", display: "flex", alignItems: "center", paddingLeft: 8 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: C.text, fontFamily: font }}>{stage.count || 0}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </Card>

          {/* Temperature Trend */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>TEMPERATURE DISTRIBUTION</div>
              {ph.temperature_breakdown && (
                <div>
                  {Object.entries(ph.temperature_breakdown).map(([temp, count]) => (
                    <div key={temp} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid " + C.border }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 12, height: 12, borderRadius: 3, background: tempColor(temp) }} />
                        <span style={{ fontSize: 12, color: C.text }}>{temp}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 14, fontWeight: 700, color: tempColor(temp), fontFamily: font }}>{count}</span>
                        <span style={{ fontSize: 10, color: C.textDim }}>{ph.total_companies ? ((count / ph.total_companies) * 100).toFixed(0) + "%" : ""}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>BRAND DISTRIBUTION</div>
              {ph.brand_breakdown && Object.entries(ph.brand_breakdown).map(([brand, count]) => (
                <div key={brand} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid " + C.border }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Badge color={brand === "TBF" ? C.purple : C.pink} size="md">{brand}</Badge>
                    <span style={{ fontSize: 12, color: C.textDim }}>{brand === "TBF" ? "Enterprise" : "Craft"}</span>
                  </div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: brand === "TBF" ? C.purple : C.pink, fontFamily: font }}>{count}</div>
                </div>
              ))}
            </Card>
          </div>
        </div>
      )}

      {/* INTELLIGENCE METRICS */}
      {tab === "intelligence" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10, marginBottom: 20 }}>
            <StatBox label="Briefs" value={im.briefs_generated || 0} color={C.green} icon={"\u{1F4DD}"} />
            <StatBox label="Papers" value={im.papers_indexed || 0} color={C.purple} icon={"\u{1F4DA}"} />
            <StatBox label="Signals" value={im.signals_tracked || 0} color={C.cyan} icon={"\u{1F4E1}"} />
            <StatBox label="Outreach" value={im.outreach_bundles || 0} color={C.gold} icon={"\u{1F4E7}"} />
            <StatBox label="Competitors" value={im.competitors_tracked || 0} color={C.hot} icon={"\u{1F575}"} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>INTELLIGENCE COVERAGE</div>
              <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.8 }}>
                <div>Companies with briefs: <span style={{ color: C.green, fontWeight: 700 }}>{im.companies_with_briefs || 0}</span> / {im.total_companies || 0}</div>
                <div>Companies with outreach: <span style={{ color: C.gold, fontWeight: 700 }}>{im.companies_with_outreach || 0}</span> / {im.total_companies || 0}</div>
                <div>Companies with signals: <span style={{ color: C.cyan, fontWeight: 700 }}>{im.companies_with_signals || 0}</span> / {im.total_companies || 0}</div>
                <div>Email verification rate: <span style={{ color: C.green, fontWeight: 700 }}>{im.email_verification_rate || 0}%</span></div>
              </div>
            </Card>

            <Card>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>RESEARCH METRICS</div>
              <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.8 }}>
                <div>Total papers: <span style={{ color: C.purple, fontWeight: 700 }}>{im.papers_indexed || 0}</span></div>
                <div>Grade A papers: <span style={{ color: C.gradeA, fontWeight: 700 }}>{im.grade_a_papers || 0}</span></div>
                <div>Unique terpenes: <span style={{ color: C.green, fontWeight: 700 }}>{im.unique_terpenes || 0}</span></div>
                <div>Mechanisms identified: <span style={{ color: C.cyan, fontWeight: 700 }}>{im.mechanisms_found || 0}</span></div>
                <div>Business insights: <span style={{ color: C.gold, fontWeight: 700 }}>{im.business_insights || 0}</span></div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* SYSTEM STATS */}
      {tab === "system" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 20 }}>
            <StatBox label="Agents" value={ss.agent_count || 0} color={C.green} icon={"\u{1F916}"} />
            <StatBox label="Data Files" value={ss.data_files || 0} color={C.cyan} />
            <StatBox label="Total Size" value={ss.total_size || "0"} color={C.text} />
            <StatBox label="Uptime" value={ss.uptime || "N/A"} color={C.gold} />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <Card>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>SYSTEM CONFIGURATION</div>
              <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.8 }}>
                <div>Schema Version: <span style={{ color: C.gold, fontWeight: 700 }}>{ss.schema_version || "7.0"}</span></div>
                <div>API Server: <span style={{ color: C.green, fontWeight: 700 }}>Reef Server v3</span></div>
                <div>Frontend: <span style={{ color: C.green, fontWeight: 700 }}>Nexus v7.0</span></div>
                <div>Data Dir: <span style={{ color: C.textDim }}>{ss.data_dir || "scripts/outputs/"}</span></div>
              </div>
            </Card>

            {lm && Object.keys(lm).length > 0 && (
              <Card>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>LEARNING METRICS</div>
                <pre style={{ fontSize: 11, color: C.textDim, lineHeight: 1.5, whiteSpace: "pre-wrap", fontFamily: font, margin: 0 }}>
                  {JSON.stringify(lm, null, 2)}
                </pre>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// CAMPAIGN BUILDER — Upload Campaign → Generate Landing Page + Email in Figma
// ═══════════════════════════════════════════════════════════════════════════════

function CampaignBuilder() {
  const [campaignName, setCampaignName] = useState("");
  const [campaignType, setCampaignType] = useState("product_launch");
  const [targetAudience, setTargetAudience] = useState("enterprise");
  const [terpenes, setTerpenes] = useState("");
  const [keyMessage, setKeyMessage] = useState("");
  const [tone, setTone] = useState("professional");
  const [uploadedFile, setUploadedFile] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("create");
  const fileInputRef = useRef(null);

  const campaignTypes = [
    { id: "product_launch", label: "Product Launch", desc: "New terpene blend or product introduction", icon: "\u{1F680}" },
    { id: "seasonal", label: "Seasonal Campaign", desc: "Holiday, 420, harvest season promotions", icon: "\u{1F33F}" },
    { id: "educational", label: "Educational Series", desc: "Terpene science and effect education", icon: "\u{1F4DA}" },
    { id: "trade_show", label: "Trade Show/Event", desc: "MJBizCon, ASD, trade event collateral", icon: "\u{1F3AA}" },
    { id: "competitive", label: "Competitive Displacement", desc: "Win-back or competitor displacement", icon: "\u{1F3AF}" },
    { id: "partnership", label: "Partnership/Co-brand", desc: "Joint venture or white-label campaign", icon: "\u{1F91D}" },
  ];

  const audiences = [
    { id: "enterprise", label: "Enterprise (TBF)", color: C.purple },
    { id: "craft", label: "Craft (DFT)", color: C.pink },
    { id: "both", label: "Both Brands", color: C.gold },
  ];

  const tones = [
    { id: "professional", label: "Professional" },
    { id: "bold", label: "Bold & Edgy" },
    { id: "scientific", label: "Scientific" },
    { id: "casual", label: "Casual & Friendly" },
  ];

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
      const reader = new FileReader();
      reader.onload = (ev) => {
        try {
          const content = ev.target.result;
          if (file.name.endsWith(".json")) {
            const parsed = JSON.parse(content);
            if (parsed.name) setCampaignName(parsed.name);
            if (parsed.type) setCampaignType(parsed.type);
            if (parsed.audience) setTargetAudience(parsed.audience);
            if (parsed.terpenes) setTerpenes(Array.isArray(parsed.terpenes) ? parsed.terpenes.join(", ") : parsed.terpenes);
            if (parsed.message) setKeyMessage(parsed.message);
            if (parsed.tone) setTone(parsed.tone);
          }
        } catch (err) {
          // Non-JSON file, just use the name
          if (!campaignName) setCampaignName(file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "));
        }
      };
      reader.readAsText(file);
    }
  };

  const handleGenerate = async () => {
    if (!campaignName.trim()) { setError("Campaign name is required"); return; }
    setGenerating(true);
    setError(null);
    setResult(null);

    const payload = {
      name: campaignName,
      type: campaignType,
      audience: targetAudience,
      terpenes: terpenes.split(",").map(t => t.trim()).filter(Boolean),
      message: keyMessage,
      tone: tone,
      brand: targetAudience === "enterprise" ? "TBF" : targetAudience === "craft" ? "DFT" : "BOTH",
    };

    try {
      const resp = await fetch("/api/reef/campaign/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (data.error) { setError(data.error); }
      else { setResult(data); setTab("preview"); }
    } catch (err) {
      setError("Failed to generate campaign. Server may not support this endpoint yet.");
      // Show a mock result for demo purposes
      setResult({
        campaign: payload,
        landing_page: {
          title: campaignName,
          headline: "Experience the Future of Terpenes",
          subheadline: "Precision-crafted botanical terpene blends for the most demanding formulations",
          hero_cta: "Request Sample Kit",
          sections: [
            { title: "Why " + (targetAudience === "enterprise" ? "Terpene Belt Farms" : "Duty Free Terpenes"), content: "Industry-leading purity, consistency, and compliance. Every batch third-party tested." },
            { title: "Featured Terpenes", content: terpenes || "Myrcene, Limonene, Beta-Caryophyllene, Linalool" },
            { title: "The Science", content: "Backed by 400+ peer-reviewed papers. Evidence-graded formulation guidance." },
          ],
          color_scheme: targetAudience === "enterprise" ? { primary: "#2D5016", accent: "#D4A843", bg: "#FAFAF5" } : { primary: "#1a1a2e", accent: "#ec4899", bg: "#0f0f23" },
        },
        email_sequence: [
          { subject: "Introducing: " + campaignName, preview: "The terpene formulation your customers have been asking for", body_outline: "Hook: Industry trend + pain point\nValue: What makes this different\nProof: Research backing + customer results\nCTA: Schedule a call or request samples" },
          { subject: "The science behind " + campaignName, preview: "432 papers. One clear conclusion.", body_outline: "Lead with research credibility\nHighlight key terpene effects\nCompliance-safe framing\nCTA: Download the research brief" },
          { subject: "Last chance: " + campaignName + " early access", preview: "Priority pricing expires Friday", body_outline: "Urgency + exclusivity\nRecap value proposition\nSocial proof\nFinal CTA: Order now" },
        ],
        figma_status: "Design specifications generated. Connect Figma API to auto-create designs.",
      });
      setTab("preview");
    }
    setGenerating(false);
  };

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="Campaign Builder" subtitle="Upload campaign brief \u2192 Generate landing page + email designs" icon={"\u{1F3A8}"} />

      <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
        <TabButton label="Create" active={tab === "create"} onClick={() => setTab("create")} icon={"\u{270F}"} />
        <TabButton label="Preview" active={tab === "preview"} onClick={() => setTab("preview")} icon={"\u{1F441}"} />
        <TabButton label="Figma Export" active={tab === "figma"} onClick={() => setTab("figma")} icon={"\u{1F3A8}"} />
      </div>

      {/* CREATE TAB */}
      {tab === "create" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {/* File Upload */}
          <Card style={{ marginBottom: 16, borderColor: C.gold + "30", borderStyle: "dashed" }}>
            <div style={{ textAlign: "center", padding: 20 }}>
              <input ref={fileInputRef} type="file" accept=".json,.txt,.md" onChange={handleFileUpload} style={{ display: "none" }} />
              <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.5 }}>{"\u{1F4C1}"}</div>
              <div style={{ fontSize: 14, color: C.text, fontWeight: 600, marginBottom: 4 }}>Upload Campaign Brief</div>
              <div style={{ fontSize: 11, color: C.textDim, marginBottom: 12 }}>Drop a JSON or text file with campaign details, or fill in below</div>
              <button onClick={() => fileInputRef.current && fileInputRef.current.click()} style={{ background: C.gold, color: C.void, border: "none", borderRadius: 6, padding: "8px 20px", fontWeight: 700, cursor: "pointer", fontSize: 12, fontFamily: font }}>Choose File</button>
              {uploadedFile && <div style={{ marginTop: 8, fontSize: 11, color: C.green }}>{"\u2714"} {uploadedFile.name}</div>}
            </div>
          </Card>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* Left: Campaign Details */}
            <div>
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>CAMPAIGN DETAILS</div>

                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: 10, color: C.textDim, fontFamily: font, letterSpacing: 1, display: "block", marginBottom: 4 }}>CAMPAIGN NAME</label>
                  <input value={campaignName} onChange={e => setCampaignName(e.target.value)} placeholder="e.g., Spring Terpene Collection 2026"
                    style={{ width: "100%", background: C.panel, border: "1px solid " + C.border, borderRadius: 6, padding: "10px 14px", color: C.text, fontSize: 13, fontFamily: fontBody, outline: "none" }}
                    onFocus={e => e.target.style.borderColor = C.gold + "60"} onBlur={e => e.target.style.borderColor = C.border} />
                </div>

                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: 10, color: C.textDim, fontFamily: font, letterSpacing: 1, display: "block", marginBottom: 4 }}>KEY MESSAGE</label>
                  <textarea value={keyMessage} onChange={e => setKeyMessage(e.target.value)} placeholder="What's the core message? e.g., 'The purest botanical terpenes, backed by science'"
                    rows={3} style={{ width: "100%", background: C.panel, border: "1px solid " + C.border, borderRadius: 6, padding: "10px 14px", color: C.text, fontSize: 13, fontFamily: fontBody, outline: "none", resize: "vertical" }}
                    onFocus={e => e.target.style.borderColor = C.gold + "60"} onBlur={e => e.target.style.borderColor = C.border} />
                </div>

                <div style={{ marginBottom: 12 }}>
                  <label style={{ fontSize: 10, color: C.textDim, fontFamily: font, letterSpacing: 1, display: "block", marginBottom: 4 }}>FEATURED TERPENES</label>
                  <input value={terpenes} onChange={e => setTerpenes(e.target.value)} placeholder="e.g., Myrcene, Limonene, Beta-Caryophyllene"
                    style={{ width: "100%", background: C.panel, border: "1px solid " + C.border, borderRadius: 6, padding: "10px 14px", color: C.text, fontSize: 13, fontFamily: fontBody, outline: "none" }}
                    onFocus={e => e.target.style.borderColor = C.gold + "60"} onBlur={e => e.target.style.borderColor = C.border} />
                </div>
              </Card>
            </div>

            {/* Right: Type + Audience + Tone */}
            <div>
              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>CAMPAIGN TYPE</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                  {campaignTypes.map(ct => (
                    <div key={ct.id} onClick={() => setCampaignType(ct.id)} style={{ padding: 10, borderRadius: 6, border: "1px solid " + (campaignType === ct.id ? C.gold + "50" : C.border), background: campaignType === ct.id ? C.gold + "10" : "transparent", cursor: "pointer", transition: "all 0.2s" }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: campaignType === ct.id ? C.gold : C.text }}>{ct.icon} {ct.label}</div>
                      <div style={{ fontSize: 9, color: C.textDim, marginTop: 2 }}>{ct.desc}</div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>TARGET AUDIENCE</div>
                <div style={{ display: "flex", gap: 8 }}>
                  {audiences.map(a => (
                    <div key={a.id} onClick={() => setTargetAudience(a.id)} style={{ flex: 1, padding: 12, borderRadius: 6, border: "1px solid " + (targetAudience === a.id ? a.color + "50" : C.border), background: targetAudience === a.id ? a.color + "10" : "transparent", cursor: "pointer", textAlign: "center", transition: "all 0.2s" }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: targetAudience === a.id ? a.color : C.text }}>{a.label}</div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>TONE</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {tones.map(t => (
                    <FilterChip key={t.id} label={t.label} active={tone === t.id} onClick={() => setTone(t.id)} />
                  ))}
                </div>
              </Card>
            </div>
          </div>

          {error && <div style={{ marginTop: 12, padding: 12, background: C.hot + "15", borderRadius: 6, border: "1px solid " + C.hot + "30", color: C.hot, fontSize: 12 }}>{error}</div>}

          <div style={{ marginTop: 20, textAlign: "center" }}>
            <button onClick={handleGenerate} disabled={generating} style={{ background: generating ? C.textDim : "linear-gradient(135deg, " + C.gold + ", " + C.goldLight + ")", color: C.void, border: "none", borderRadius: 8, padding: "14px 40px", fontWeight: 800, cursor: generating ? "default" : "pointer", fontSize: 14, fontFamily: font, letterSpacing: 2, boxShadow: "0 0 20px " + C.gold + "30" }}>
              {generating ? "GENERATING..." : "\u{1F680} GENERATE CAMPAIGN"}
            </button>
          </div>
        </div>
      )}

      {/* PREVIEW TAB */}
      {tab === "preview" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          {result ? (
            <div>
              {/* Landing Page Preview */}
              {result.landing_page && (
                <Card style={{ marginBottom: 20, overflow: "hidden" }}>
                  <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 16 }}>{"\u{1F310}"} LANDING PAGE PREVIEW</div>

                  {/* Mock landing page */}
                  <div style={{ borderRadius: 8, overflow: "hidden", border: "1px solid " + C.border }}>
                    <div style={{ background: result.landing_page.color_scheme ? result.landing_page.color_scheme.primary : C.gold, padding: "40px 30px", textAlign: "center" }}>
                      <div style={{ fontSize: 28, fontWeight: 800, color: "#fff", marginBottom: 8, fontFamily: fontBody }}>{result.landing_page.headline}</div>
                      <div style={{ fontSize: 14, color: "rgba(255,255,255,0.8)", marginBottom: 20, maxWidth: 500, margin: "0 auto 20px" }}>{result.landing_page.subheadline}</div>
                      <div style={{ display: "inline-block", padding: "12px 28px", background: result.landing_page.color_scheme ? result.landing_page.color_scheme.accent : "#fff", color: result.landing_page.color_scheme ? result.landing_page.color_scheme.primary : C.void, borderRadius: 6, fontWeight: 700, fontSize: 13 }}>{result.landing_page.hero_cta}</div>
                    </div>
                    {result.landing_page.sections && result.landing_page.sections.map((sec, i) => (
                      <div key={i} style={{ padding: "20px 30px", borderBottom: "1px solid " + C.border, background: i % 2 === 0 ? C.surface : C.panel }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: C.gold, marginBottom: 6 }}>{sec.title}</div>
                        <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.6 }}>{sec.content}</div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Email Sequence Preview */}
              {result.email_sequence && (
                <Card style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 16 }}>{"\u{1F4E7}"} EMAIL SEQUENCE ({result.email_sequence.length} emails)</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
                    {result.email_sequence.map((email, i) => (
                      <Card key={i} style={{ borderLeft: "3px solid " + [C.gold, C.cyan, C.hot][i % 3] }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                          <Badge color={[C.gold, C.cyan, C.hot][i % 3]} size="md">Email {i + 1}</Badge>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>{email.subject}</div>
                        <div style={{ fontSize: 11, color: C.textDim, marginBottom: 8, fontStyle: "italic" }}>{email.preview}</div>
                        <div style={{ fontSize: 11, color: C.text, lineHeight: 1.6, padding: 10, background: C.panel, borderRadius: 6, whiteSpace: "pre-wrap" }}>{email.body_outline}</div>
                      </Card>
                    ))}
                  </div>
                </Card>
              )}

              {/* Figma Status */}
              {result.figma_status && (
                <Card style={{ borderColor: C.purple + "30" }}>
                  <div style={{ fontSize: 11, color: C.purple, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>{"\u{1F3A8}"} FIGMA INTEGRATION</div>
                  <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.6 }}>{result.figma_status}</div>
                </Card>
              )}
            </div>
          ) : (
            <EmptyState message="Create a campaign first to see the preview." />
          )}
        </div>
      )}

      {/* FIGMA EXPORT TAB */}
      {tab === "figma" && (
        <div style={{ animation: "fadeIn 0.3s ease-out" }}>
          <Card style={{ marginBottom: 16, borderColor: C.purple + "30" }}>
            <div style={{ fontSize: 11, color: C.purple, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>{"\u{1F3A8}"} FIGMA DESIGN EXPORT</div>
            <div style={{ fontSize: 13, color: C.text, lineHeight: 1.7, marginBottom: 16 }}>
              Export your campaign as Figma-ready design specifications. The system generates:
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              {[
                { title: "Landing Page", desc: "Full responsive layout with hero, sections, CTA blocks", icon: "\u{1F310}", color: C.gold },
                { title: "Email Templates", desc: "HTML-ready email designs matching brand guidelines", icon: "\u{1F4E7}", color: C.cyan },
                { title: "Social Assets", desc: "Instagram, LinkedIn, Twitter post templates", icon: "\u{1F4F1}", color: C.pink },
              ].map(item => (
                <Card key={item.title} style={{ borderColor: item.color + "20", textAlign: "center" }}>
                  <div style={{ fontSize: 28, marginBottom: 8 }}>{item.icon}</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: item.color }}>{item.title}</div>
                  <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>{item.desc}</div>
                </Card>
              ))}
            </div>
          </Card>

          <Card>
            <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>FIGMA API CONFIGURATION</div>
            <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.6, marginBottom: 12 }}>
              To enable direct Figma export, configure your Figma API token:
            </div>
            <div style={{ padding: 14, background: C.panel, borderRadius: 8, fontFamily: font, fontSize: 11, color: C.textDim }}>
              <div>1. Go to Figma Settings {">"} Personal Access Tokens</div>
              <div>2. Generate a new token with file:write scope</div>
              <div>3. Set FIGMA_API_TOKEN in your .env file</div>
              <div>4. The system will auto-create designs in your Figma workspace</div>
            </div>
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <Badge color={C.warm} size="md">Not Connected</Badge>
              <span style={{ fontSize: 11, color: C.textDim }}>Configure API token to enable</span>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// AGENTS VIEW — Agent Fleet Management + Status
// ═══════════════════════════════════════════════════════════════════════════════

function AgentsView({ agents }) {
  const [selectedAgent, setSelectedAgent] = useState(null);

  const statusColor = (s) => s === "active" ? C.green : s === "deployed" ? C.cool : s === "ready" ? C.warm : C.textDim;
  const statusIcon = (s) => s === "active" ? "\u{1F7E2}" : s === "deployed" ? "\u{1F535}" : s === "ready" ? "\u{1F7E1}" : "\u{26AA}";
  const list = agents || [];

  const agentCategories = useMemo(() => {
    const cats = { "Data Collection": [], "Analysis": [], "Outreach": [], "Research": [], "Other": [] };
    list.forEach(a => {
      const name = (a.name || "").toLowerCase();
      if (name.includes("apollo") || name.includes("scrape") || name.includes("import") || name.includes("enrich")) cats["Data Collection"].push(a);
      else if (name.includes("score") || name.includes("intel") || name.includes("brief") || name.includes("war")) cats["Analysis"].push(a);
      else if (name.includes("outreach") || name.includes("kill") || name.includes("email") || name.includes("campaign")) cats["Outreach"].push(a);
      else if (name.includes("terpene") || name.includes("research") || name.includes("pubmed")) cats["Research"].push(a);
      else cats["Other"].push(a);
    });
    return Object.entries(cats).filter(([_, v]) => v.length > 0);
  }, [list]);

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="Agent Fleet" subtitle={list.length + " specialized agents \u00B7 Multi-agent orchestration"} icon={"\u{1F916}"} />

      {/* Fleet Summary */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <StatBox label="Total" value={list.length} color={C.text} icon={"\u{1F916}"} />
        <StatBox label="Active" value={list.filter(a => a.status === "active").length} color={C.green} />
        <StatBox label="Deployed" value={list.filter(a => a.status === "deployed").length} color={C.cool} />
        <StatBox label="Ready" value={list.filter(a => a.status === "ready").length} color={C.warm} />
        <StatBox label="Standby" value={list.filter(a => !a.status || a.status === "standby").length} color={C.textDim} />
      </div>

      {/* Agents by Category */}
      {agentCategories.map(([category, catAgents]) => (
        <div key={category} style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10, display: "flex", alignItems: "center", gap: 8 }}>
            {category.toUpperCase()}
            <Badge color={C.textDim} size="xs">{catAgents.length}</Badge>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 10 }}>
            {catAgents.map((a, i) => {
              const isSelected = selectedAgent === (a.agent_id || a.name);
              return (
                <Card key={a.agent_id || a.name || i} onClick={() => setSelectedAgent(isSelected ? null : (a.agent_id || a.name))}
                  style={{ borderLeft: "3px solid " + statusColor(a.status || "standby"), borderColor: isSelected ? C.gold + "50" : C.border, animation: "fadeIn 0.3s ease-out", animationDelay: i * 0.03 + "s", animationFillMode: "both" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span>{statusIcon(a.status || "standby")}</span>
                      <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{a.name}</span>
                    </div>
                    <Badge color={statusColor(a.status || "standby")} glow={a.status === "active"}>{a.status || "standby"}</Badge>
                  </div>
                  <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.5, marginBottom: 8 }}>{a.description}</div>

                  {isSelected && (
                    <div style={{ marginTop: 8, padding: 10, background: C.panel, borderRadius: 6, animation: "fadeIn 0.2s ease-out" }}>
                      <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 4, fontFamily: font }}>DETAILS</div>
                      {a.script && <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 2, fontFamily: font }}>Script: {a.script}</div>}
                      {a.commands && <div style={{ fontSize: 10, color: C.textMuted, fontFamily: font }}>Commands: {a.commands.join(", ")}</div>}
                      {a.last_run && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>Last run: {a.last_run}</div>}
                      {a.output_dir && <div style={{ fontSize: 10, color: C.textMuted }}>Output: {a.output_dir}</div>}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      ))}

      {list.length === 0 && <EmptyState message="No agents registered. Start the agent fleet to begin." />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// COMMAND CENTER — Enhanced Chat Interface
// ═══════════════════════════════════════════════════════════════════════════════

function CommandCenter({ onSelectCompany }) {
  const [messages, setMessages] = useState([{ role: "assistant", content: "Nexus BDR System online. All agents operational.\n\nI can help with:\n\u2022 Company research & intel\n\u2022 Pipeline status & strategy\n\u2022 Competitor analysis\n\u2022 Terpene science questions\n\u2022 Outreach strategy & content\n\u2022 Campaign planning\n\nTry: \"What's the displacement strategy for Mellow Fellow?\"" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => { if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight; }, [messages]);

  const quickActions = [
    { label: "Hot targets", cmd: "Show me the hottest targets right now" },
    { label: "Pipeline summary", cmd: "Give me a pipeline summary" },
    { label: "Mellow Fellow", cmd: "Tell me everything about Mellow Fellow" },
    { label: "Competitor map", cmd: "Map out our competitive landscape" },
    { label: "Terpene trends", cmd: "What are the top terpene research trends?" },
  ];

  const send = useCallback(async (msg) => {
    const text = msg || input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const resp = await fetch("/api/reef/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: messages.slice(-8) }),
      });
      const data = await resp.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.response || "No response.", agents: data.agents_activated, companies: data.companies_mentioned }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Connection error. Make sure reef_server.py is running on port 3142." }]);
    }
    setLoading(false);
  }, [input, loading, messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Chat Messages */}
      <div ref={chatRef} style={{ flex: 1, overflow: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start", animation: "fadeIn 0.2s ease-out" }}>
            <div style={{
              maxWidth: "80%", padding: "12px 18px", borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
              background: msg.role === "user" ? C.gold + "20" : C.surface,
              border: "1px solid " + (msg.role === "user" ? C.gold + "40" : C.border),
              fontSize: 13, color: C.text, lineHeight: 1.7, whiteSpace: "pre-wrap",
            }}>
              {msg.content}
              {msg.agents && msg.agents.length > 0 && (
                <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                  {msg.agents.map((a, j) => <Badge key={j} color={C.green} size="xs">{a.script || a}</Badge>)}
                </div>
              )}
              {msg.companies && msg.companies.length > 0 && (
                <div style={{ display: "flex", gap: 4, marginTop: 6, flexWrap: "wrap" }}>
                  {msg.companies.map((c, j) => (
                    <button key={j} onClick={() => onSelectCompany(c)} style={{ background: C.gold + "15", border: "1px solid " + C.gold + "30", borderRadius: 4, padding: "2px 8px", color: C.gold, fontSize: 10, fontWeight: 600, cursor: "pointer", fontFamily: font }}>{c}</button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div style={{ color: C.gold, fontSize: 13, padding: 8, animation: "pulse 1.5s infinite" }}>{"\u{1F4AD}"} Thinking...</div>}
      </div>

      {/* Quick Actions */}
      <div style={{ padding: "8px 20px 0", display: "flex", gap: 6, flexWrap: "wrap" }}>
        {quickActions.map((qa, i) => (
          <button key={i} onClick={() => send(qa.cmd)} style={{ padding: "4px 12px", borderRadius: 16, fontSize: 10, fontWeight: 600, background: "transparent", color: C.textDim, border: "1px solid " + C.border, cursor: "pointer", fontFamily: font, transition: "all 0.2s" }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.gold; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textDim; }}>
            {qa.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={{ padding: "12px 20px", borderTop: "1px solid " + C.border, display: "flex", gap: 8, background: C.void }}>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Ask anything \u2014 research, pipeline, strategy, competitor intel..."
          style={{ flex: 1, background: C.surface, border: "1px solid " + C.border, borderRadius: 8, padding: "12px 18px", color: C.text, fontSize: 14, fontFamily: fontBody, outline: "none" }}
          onFocus={e => e.target.style.borderColor = C.gold + "60"} onBlur={e => e.target.style.borderColor = C.border} />
        <button onClick={() => send()} style={{ background: "linear-gradient(135deg, " + C.gold + ", " + C.goldLight + ")", color: C.void, border: "none", borderRadius: 8, padding: "12px 24px", fontWeight: 700, cursor: "pointer", fontSize: 13, fontFamily: font, letterSpacing: 1 }}>{"\u{1F680}"} Send</button>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// MAIN APP — Boot Sequence + Navigation + Data Loading
// ═══════════════════════════════════════════════════════════════════════════════

const BOOT_LINES = [
  { text: "NEXUS BDR SYSTEM v7.0 --- INITIALIZING", color: "#d4a843" },
  { text: "Connecting to Reef API Server...", color: "#e8e8f0" },
  { text: "Loading agent fleet [12 agents]...", color: "#e8e8f0" },
  { text: "Building company dossiers [39 companies]...", color: "#e8e8f0" },
  { text: "Indexing terpene research [432 papers]...", color: "#22d3ee" },
  { text: "Loading competitor intelligence [7 tracked]...", color: "#e8e8f0" },
  { text: "Processing signal feed [35 signals]...", color: "#e8e8f0" },
  { text: "Calculating revenue forecast...", color: "#00e09a" },
  { text: "Running vulnerability scans...", color: "#ff8c00" },
  { text: "Campaign builder ready...", color: "#e8e8f0" },
  { text: "ALL SYSTEMS OPERATIONAL", color: "#00e09a" },
  { text: "================================", color: "#d4a843" },
];

export default function NexusV5() {
  const [booted, setBooted] = useState(false);
  const [bootLines, setBootLines] = useState([]);
  const [view, setView] = useState("PIPELINE");
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [researchData, setResearchData] = useState(null);
  const [agentData, setAgentData] = useState(null);
  const [competitorData, setCompetitorData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [signalData, setSignalData] = useState(null);
  const [companyCache, setCompanyCache] = useState({});
  const [systemStatus, setSystemStatus] = useState({ api: false, agents: 0, companies: 0 });

  // Boot sequence
  useEffect(() => {
    let idx = 0;
    const total = BOOT_LINES.length;
    const timer = setInterval(() => {
      if (idx < total) {
        const line = BOOT_LINES[idx];
        idx++;
        if (line) setBootLines(function(prev) { return prev.concat([line]); });
      } else {
        clearInterval(timer);
        setTimeout(function() { setBooted(true); }, 500);
      }
    }, 120);
    return function() { clearInterval(timer); };
  }, []);

  // Load all data on boot
  useEffect(() => {
    if (!booted) return;

    const loadData = async () => {
      try {
        const [pipeResp, researchResp, agentResp, compResp, analyticsResp, signalResp] = await Promise.allSettled([
          fetch("/api/reef/pipeline").then(r => r.json()),
          fetch("/api/reef/research").then(r => r.json()),
          fetch("/api/agents").then(r => r.json()),
          fetch("/api/reef/competitors").then(r => r.json()),
          fetch("/api/reef/analytics").then(r => r.json()),
          fetch("/api/reef/signals").then(r => r.json()),
        ]);

        if (pipeResp.status === "fulfilled") setPipelineData(pipeResp.value);
        if (researchResp.status === "fulfilled") setResearchData(researchResp.value);
        if (agentResp.status === "fulfilled") setAgentData(agentResp.value.agents || []);
        if (compResp.status === "fulfilled") setCompetitorData(compResp.value);
        if (analyticsResp.status === "fulfilled") setAnalyticsData(analyticsResp.value);
        if (signalResp.status === "fulfilled") setSignalData(signalResp.value);

        setSystemStatus({
          api: true,
          agents: agentResp.status === "fulfilled" ? (agentResp.value.agents || []).length : 0,
          companies: pipeResp.status === "fulfilled" ? (pipeResp.value.total_companies || 0) : 0,
        });
      } catch (err) {
        console.error("Failed to load data:", err);
      }
    };

    loadData();
  }, [booted]);

  const handleSelectCompany = useCallback((name) => {
    if (companyCache[name]) {
      setSelectedCompany(companyCache[name]);
      return;
    }
    fetch("/api/reef/company/" + encodeURIComponent(name)).then(r => r.json()).then(d => {
      if (d.company) {
        setCompanyCache(prev => ({ ...prev, [name]: d.company }));
        setSelectedCompany(d.company);
      }
    }).catch(() => {});
  }, [companyCache]);

  // Boot screen
  if (!booted) {
    return (
      <div style={{ background: C.void, minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", fontFamily: font, padding: 24 }}>
        <style>{globalStyles}</style>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
        <div style={{ marginBottom: 40 }}>
          <div style={{ fontSize: 48, fontWeight: 800, background: "linear-gradient(135deg, " + C.gold + ", " + C.goldLight + ", " + C.gold + ")", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", letterSpacing: 12, textAlign: "center" }}>NEXUS</div>
          <div style={{ fontSize: 12, color: C.textDim, letterSpacing: 6, textAlign: "center", marginTop: 4 }}>BDR INTELLIGENCE SYSTEM</div>
        </div>
        <div style={{ maxWidth: 550, width: "100%" }}>
          {bootLines.map(function(line, i) {
            if (!line) return null;
            return (
              <div key={i} style={{ color: line.color || "#e8e8f0", fontSize: 13, padding: "3px 0", opacity: 0, animation: "fadeIn 0.3s forwards", animationDelay: (i * 0.05) + "s", display: "flex", gap: 8 }}>
                <span style={{ color: "#888899", width: 28, textAlign: "right", flexShrink: 0 }}>{"[" + String(i).padStart(2, "0") + "]"}</span>
                <span>{line.text || ""}</span>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 30, width: 200, height: 3, background: "#1a1a2e", borderRadius: 2, overflow: "hidden" }}>
          <div style={{ height: "100%", background: "linear-gradient(90deg, #d4a843, #e8c55a)", width: Math.min((bootLines.length / 12) * 100, 100) + "%", transition: "width 0.3s", borderRadius: 2 }} />
        </div>
      </div>
    );
  }

  const views = [
    { id: "PIPELINE", label: "PIPELINE", icon: "\u{1F3AF}" },
    { id: "RESEARCH", label: "RESEARCH", icon: "\u{1F9EA}" },
    { id: "COMPETITORS", label: "COMPETITORS", icon: "\u{1F575}" },
    { id: "SIGNALS", label: "SIGNALS", icon: "\u{1F4E1}" },
    { id: "ANALYTICS", label: "ANALYTICS", icon: "\u{1F4CA}" },
    { id: "CAMPAIGNS", label: "CAMPAIGNS", icon: "\u{1F3A8}" },
    { id: "COMMAND", label: "COMMAND", icon: "\u{1F4AC}" },
    { id: "AGENTS", label: "AGENTS", icon: "\u{1F916}" },
  ];

  // Company dossier view
  if (selectedCompany) {
    return (
      <div style={{ background: C.bg, minHeight: "100vh", fontFamily: fontBody, color: C.text }}>
        <style>{globalStyles}</style>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
        <CompanyDossier company={selectedCompany} onBack={() => setSelectedCompany(null)} />
      </div>
    );
  }

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: fontBody, color: C.text }}>
      <style>{globalStyles}</style>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{ padding: "8px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid " + C.border, background: C.void, position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 22, fontWeight: 800, background: "linear-gradient(135deg, " + C.gold + ", " + C.goldLight + ")", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", letterSpacing: 4, fontFamily: font }}>NEXUS</span>
          <span style={{ color: C.textDim, fontSize: 10, fontFamily: font, letterSpacing: 1 }}>BDR INTELLIGENCE v7.0</span>
          <div style={{ width: 1, height: 16, background: C.border }} />
          <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div style={{ width: 6, height: 6, borderRadius: 3, background: systemStatus.api ? C.green : C.hot, boxShadow: "0 0 6px " + (systemStatus.api ? C.green : C.hot) }} />
            <span style={{ fontSize: 9, color: C.textDim, fontFamily: font }}>{systemStatus.api ? "ONLINE" : "OFFLINE"}</span>
          </div>
          {systemStatus.api && (
            <span style={{ fontSize: 9, color: C.textMuted, fontFamily: font }}>{systemStatus.companies} companies \u00B7 {systemStatus.agents} agents</span>
          )}
        </div>
        <div style={{ display: "flex", gap: 3, overflowX: "auto" }}>
          {views.map(v => <TabButton key={v.id} label={v.label} active={view === v.id} onClick={() => setView(v.id)} icon={v.icon} />)}
        </div>
      </div>

      {/* Content */}
      <div style={{ height: "calc(100vh - 48px)" }}>
        {view === "PIPELINE" && <PipelineView data={pipelineData} onSelectCompany={handleSelectCompany} />}
        {view === "RESEARCH" && <ResearchLab data={researchData} />}
        {view === "COMPETITORS" && <CompetitorIntel data={competitorData} />}
        {view === "SIGNALS" && <SignalIntel data={signalData} onSelectCompany={handleSelectCompany} />}
        {view === "ANALYTICS" && <AnalyticsDashboard data={analyticsData} />}
        {view === "CAMPAIGNS" && <CampaignBuilder />}
        {view === "COMMAND" && <CommandCenter onSelectCompany={handleSelectCompany} />}
        {view === "AGENTS" && <AgentsView agents={agentData} />}
      </div>
    </div>
  );
}
