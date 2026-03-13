import { useState, useEffect, useRef, useCallback, useMemo } from "react";

// ═══════════════════════════════════════════════════════════
// DESIGN SYSTEM
// ═══════════════════════════════════════════════════════════
const C = {
  gold: "#d4a843", goldLight: "#e8c55a", goldDim: "#8a7230",
  void: "#020208", bg: "#06060d", surface: "#0d0d1a", surfaceHover: "#12122a",
  border: "#1a1a2e", borderLight: "#252545",
  text: "#e8e8f0", textDim: "#888899", textMuted: "#555566",
  hot: "#ff2d2d", warm: "#ff8c00", cool: "#2d7fff", cold: "#555570",
  green: "#00e09a", greenDim: "#00a070",
  purple: "#a855f7", pink: "#ec4899", cyan: "#22d3ee",
  gradeA: "#00e09a", gradeB: "#22d3ee", gradeC: "#ff8c00", gradeD: "#555570",
};

const font = "'JetBrains Mono',monospace";
const fontBody = "'Outfit',sans-serif";

const tempColor = (t) => t === "Hot" ? C.hot : t === "Warm" ? C.warm : t === "Cool" ? C.cool : C.cold;
const stageLabel = { new: "New", scored: "Scored", enriched: "Enriched", researched: "Researched", outreach_ready: "Outreach Ready", engaged: "Engaged", meeting: "Meeting", proposal: "Proposal", won: "Won" };
const stageColor = { new: C.cold, scored: C.cool, enriched: C.cyan, researched: C.warm, outreach_ready: C.green, engaged: C.gold, meeting: C.purple, proposal: C.pink, won: C.green };
const gradeColor = (g) => g === "A" ? C.gradeA : g === "B" ? C.gradeB : g === "C" ? C.gradeC : C.gradeD;

// ═══════════════════════════════════════════════════════════
// SHARED COMPONENTS
// ═══════════════════════════════════════════════════════════

function Badge({ children, color = C.textDim, bg: bgColor }) {
  return <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700, fontFamily: font, letterSpacing: 0.5, color: color, background: bgColor || `${color}18`, border: `1px solid ${color}30`, textTransform: "uppercase", whiteSpace: "nowrap" }}>{children}</span>;
}

function StatBox({ label, value, color = C.text, sub }) {
  return (
    <div style={{ textAlign: "center", padding: "10px 12px", background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, minWidth: 80 }}>
      <div style={{ fontSize: 22, fontWeight: 800, color, fontFamily: font }}>{value}</div>
      <div style={{ fontSize: 10, color: C.textDim, textTransform: "uppercase", letterSpacing: 1, marginTop: 2 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ title, subtitle, action }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
      <div>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: C.gold, fontFamily: font, letterSpacing: 2, margin: 0 }}>{title}</h2>
        {subtitle && <div style={{ fontSize: 12, color: C.textDim, marginTop: 2 }}>{subtitle}</div>}
      </div>
      {action}
    </div>
  );
}

function TabButton({ label, active, onClick, count }) {
  return (
    <button onClick={onClick} style={{
      background: active ? C.gold : "transparent", color: active ? C.void : C.textDim,
      border: `1px solid ${active ? C.gold : C.border}`, padding: "6px 16px", borderRadius: 4,
      fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: font, letterSpacing: 1,
      transition: "all 0.2s", display: "flex", alignItems: "center", gap: 6,
    }}>
      {label}
      {count !== undefined && <span style={{ fontSize: 10, opacity: 0.7 }}>({count})</span>}
    </button>
  );
}

function EmptyState({ message }) {
  return <div style={{ padding: 40, textAlign: "center", color: C.textDim, fontSize: 13 }}>{message}</div>;
}

function ProgressBar({ segments, height = 8 }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div style={{ display: "flex", height, borderRadius: height / 2, overflow: "hidden", gap: 1, background: C.border }}>
      {segments.map((s, i) => s.value > 0 && (
        <div key={i} title={`${s.label}: ${s.value}`} style={{ width: `${(s.value / total) * 100}%`, background: s.color, minWidth: s.value > 0 ? 3 : 0, transition: "width 0.6s" }} />
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// PIPELINE WAR ROOM
// ═══════════════════════════════════════════════════════════

function PipelineView({ data, onSelectCompany }) {
  if (!data) return <EmptyState message="Loading pipeline data..." />;

  const { total_companies, total_contacts, total_emails, total_verified, temperatures, brand_split, stages, forecast, hot_list, companies } = data;
  const stageOrder = ["new", "scored", "enriched", "researched", "outreach_ready", "engaged", "meeting", "proposal", "won"];

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="PIPELINE WAR ROOM" subtitle={`${total_companies} companies / ${total_contacts} contacts / Live data`} />

      {/* Top stats row */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        <StatBox label="Companies" value={total_companies} color={C.gold} />
        <StatBox label="Contacts" value={total_contacts} color={C.text} />
        <StatBox label="Emails" value={total_emails} color={C.cyan} />
        <StatBox label="Verified" value={total_verified} color={C.green} />
        <StatBox label="Hot" value={temperatures.Hot || 0} color={C.hot} />
        <StatBox label="Warm" value={temperatures.Warm || 0} color={C.warm} />
        <StatBox label="Cool" value={temperatures.Cool || 0} color={C.cool} />
        <StatBox label="TBF" value={brand_split.TBF || 0} color={C.purple} />
        <StatBox label="DFT" value={brand_split.DFT || 0} color={C.pink} />
      </div>

      {/* Revenue Forecast */}
      {(forecast.conservative > 0 || forecast.likely > 0 || forecast.upside > 0) && (
        <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.gold}40`, padding: 16, marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>REVENUE FORECAST</div>
          <div style={{ display: "flex", gap: 16 }}>
            {[
              { label: "Conservative", value: forecast.conservative, color: C.cool },
              { label: "Likely", value: forecast.likely, color: C.green },
              { label: "Upside", value: forecast.upside, color: C.gold },
            ].map(f => (
              <div key={f.label} style={{ flex: 1, textAlign: "center", padding: 12, background: `${f.color}08`, borderRadius: 6, border: `1px solid ${f.color}25` }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: f.color, fontFamily: font }}>${(f.value / 1000).toFixed(0)}K</div>
                <div style={{ fontSize: 10, color: C.textDim, textTransform: "uppercase", marginTop: 4 }}>{f.label}/yr</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pipeline Stages - Kanban */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>PIPELINE STAGES</div>
        <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
          {stageOrder.map(s => {
            const count = stages[s] ? stages[s].count : 0;
            return (
              <div key={s} style={{ flex: 1, textAlign: "center", padding: "8px 4px", background: count > 0 ? `${stageColor[s]}12` : C.surface, borderRadius: 6, border: `1px solid ${count > 0 ? stageColor[s] + "40" : C.border}` }}>
                <div style={{ fontSize: 18, fontWeight: 800, color: count > 0 ? stageColor[s] : C.textMuted, fontFamily: font }}>{count}</div>
                <div style={{ fontSize: 8, color: C.textDim, textTransform: "uppercase", letterSpacing: 0.5, marginTop: 2 }}>{stageLabel[s]}</div>
              </div>
            );
          })}
        </div>
        <ProgressBar segments={stageOrder.map(s => ({ label: stageLabel[s], value: stages[s] ? stages[s].count : 0, color: stageColor[s] }))} height={6} />
      </div>

      {/* Hot List - Next Actions */}
      {hot_list && hot_list.length > 0 && (
        <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.hot}30`, padding: 16, marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>PRIORITY ACTIONS</div>
          {hot_list.map((item, i) => (
            <div key={i} onClick={() => onSelectCompany(item.company)} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 12px", marginBottom: 4, borderRadius: 6, cursor: "pointer", background: i === 0 ? `${C.hot}08` : "transparent", border: `1px solid ${i === 0 ? C.hot + "20" : "transparent"}`, transition: "all 0.15s" }}
              onMouseEnter={e => { e.currentTarget.style.background = `${C.gold}10`; }} onMouseLeave={e => { e.currentTarget.style.background = i === 0 ? `${C.hot}08` : "transparent"; }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 28, height: 28, borderRadius: 6, background: `${tempColor(item.score >= 80 ? "Hot" : "Warm")}20`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: tempColor(item.score >= 80 ? "Hot" : "Warm"), fontFamily: font }}>{i + 1}</div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{item.company}</div>
                  <div style={{ fontSize: 11, color: C.textDim }}>{item.top_contact} — {item.top_title}</div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Badge color={tempColor(item.score >= 80 ? "Hot" : "Warm")}>{item.score}</Badge>
                <Badge color={stageColor[item.stage]}>{stageLabel[item.stage]}</Badge>
                <div style={{ fontSize: 11, color: C.green, fontWeight: 600, maxWidth: 160, textAlign: "right" }}>{item.next_action}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Full Company Grid */}
      <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>ALL ACCOUNTS ({companies.length})</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 10 }}>
        {companies.map(co => (
          <div key={co.name} onClick={() => onSelectCompany(co.name)} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, cursor: "pointer", transition: "all 0.15s", borderLeft: `3px solid ${tempColor(co.temperature)}` }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.background = C.surfaceHover; }} onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.background = C.surface; e.currentTarget.style.borderLeft = `3px solid ${tempColor(co.temperature)}`; }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{co.name}</div>
                <div style={{ fontSize: 11, color: C.textDim }}>{co.domain} {co.state && `· ${co.state}`}</div>
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: tempColor(co.temperature), fontFamily: font, textShadow: co.avg_score >= 90 ? `0 0 12px ${tempColor(co.temperature)}40` : "none" }}>{co.avg_score}</div>
            </div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              <Badge color={co.brand === "TBF" ? C.purple : C.pink}>{co.brand}</Badge>
              <Badge color={stageColor[co.stage]}>{stageLabel[co.stage]}</Badge>
              <Badge color={C.textDim}>{co.contact_count} contacts</Badge>
              {co.emails_verified > 0 && <Badge color={C.green}>{co.emails_verified} verified</Badge>}
              {co.brief_status === "complete" && <Badge color={C.green}>Brief Done</Badge>}
            </div>
            {co.top_contact && (
              <div style={{ marginTop: 8, fontSize: 11, color: C.textDim }}>
                Top: <span style={{ color: C.text }}>{co.top_contact.name}</span> — {co.top_contact.title}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// COMPANY DOSSIER - FULL INDEPENDENT PROFILE
// ═══════════════════════════════════════════════════════════

function CompanyDossier({ company, onBack }) {
  const [tab, setTab] = useState("overview");
  const co = company;
  if (!co) return null;

  const brief = co.brief_data || {};
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "people", label: "People", count: co.contact_count },
    { id: "intel", label: "Intel" },
    { id: "deal", label: "Deal" },
    { id: "signals", label: "Signals", count: (co.signals || []).length },
    { id: "outreach", label: "Outreach" },
  ];

  return (
    <div style={{ height: "100%", overflow: "auto", padding: 24 }}>
      {/* Back button + Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <button onClick={onBack} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: "6px 12px", color: C.textDim, cursor: "pointer", fontSize: 12, fontFamily: font }}>Back</button>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: C.text, margin: 0 }}>{co.name}</h1>
            <span style={{ fontSize: 28, fontWeight: 800, color: tempColor(co.temperature), fontFamily: font, textShadow: `0 0 16px ${tempColor(co.temperature)}40` }}>{co.avg_score}</span>
            <Badge color={co.brand === "TBF" ? C.purple : C.pink}>{co.brand}</Badge>
            <Badge color={stageColor[co.stage]}>{stageLabel[co.stage]}</Badge>
            <Badge color={tempColor(co.temperature)}>{co.temperature}</Badge>
          </div>
          <div style={{ fontSize: 12, color: C.textDim, marginTop: 4 }}>{co.domain} {co.state && ` · ${co.state}`} {co.industry && ` · ${co.industry}`} {co.employees && ` · ${co.employees} employees`}</div>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
        <StatBox label="Contacts" value={co.contact_count} color={C.text} />
        <StatBox label="Emails" value={co.emails_total} color={C.cyan} />
        <StatBox label="Verified" value={co.emails_verified} color={C.green} />
        <StatBox label="Top Score" value={co.top_score} color={tempColor(co.temperature)} />
        {brief.terpene_relevance && <StatBox label="Terp Fit" value={brief.terpene_relevance} color={brief.terpene_relevance === "HIGH" ? C.green : C.warm} />}
        {co.brief_status === "complete" && <StatBox label="Brief" value="Done" color={C.green} />}
      </div>

      {/* Sub-tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, borderBottom: `1px solid ${C.border}`, paddingBottom: 8 }}>
        {tabs.map(t => <TabButton key={t.id} label={t.label} count={t.count} active={tab === t.id} onClick={() => setTab(t.id)} />)}
      </div>

      {/* OVERVIEW TAB */}
      {tab === "overview" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Left column */}
          <div>
            {brief.description && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>COMPANY OVERVIEW</div>
                <div style={{ fontSize: 13, color: C.text, lineHeight: 1.7 }}>{brief.description}</div>
                {brief.founded && <div style={{ fontSize: 12, color: C.textDim, marginTop: 8 }}>Founded: {brief.founded} {brief.headquarters && `· ${brief.headquarters}`}</div>}
                {brief.company_type && <div style={{ fontSize: 12, color: C.textDim }}>Type: {brief.company_type}</div>}
              </div>
            )}
            {brief.key_products && brief.key_products.length > 0 && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>PRODUCTS</div>
                {brief.key_products.map((p, i) => (
                  <div key={i} style={{ fontSize: 12, color: C.text, padding: "4px 0", borderBottom: i < brief.key_products.length - 1 ? `1px solid ${C.border}` : "none", lineHeight: 1.5 }}>{p}</div>
                ))}
              </div>
            )}
            {co.extraction_methods.length > 0 && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>EXTRACTION & PRODUCTS</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
                  {co.extraction_methods.map(m => <Badge key={m} color={C.cyan}>{m}</Badge>)}
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {co.product_types.map(p => <Badge key={p} color={C.purple}>{p}</Badge>)}
                </div>
              </div>
            )}
          </div>
          {/* Right column */}
          <div>
            {brief.recent_news && brief.recent_news.length > 0 && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>RECENT NEWS</div>
                {brief.recent_news.map((n, i) => (
                  <div key={i} style={{ padding: "8px 0", borderBottom: i < brief.recent_news.length - 1 ? `1px solid ${C.border}` : "none" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{n.headline}</div>
                    {n.date && <div style={{ fontSize: 10, color: C.textDim, marginTop: 2 }}>{n.date}</div>}
                    {n.significance && <div style={{ fontSize: 11, color: C.textDim, marginTop: 4, lineHeight: 1.5 }}>{n.significance}</div>}
                  </div>
                ))}
              </div>
            )}
            {brief.growth_signals && brief.growth_signals.length > 0 && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.green, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>GROWTH SIGNALS</div>
                {brief.growth_signals.map((g, i) => (
                  <div key={i} style={{ fontSize: 12, color: C.text, padding: "4px 0", display: "flex", gap: 8, lineHeight: 1.5 }}>
                    <span style={{ color: C.green, flexShrink: 0 }}>+</span> {g}
                  </div>
                ))}
              </div>
            )}
            {brief.brand_positioning && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>BRAND POSITIONING</div>
                <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{brief.brand_positioning}</div>
              </div>
            )}
            {!brief.description && (
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.warm}30`, padding: 20, textAlign: "center" }}>
                <div style={{ fontSize: 13, color: C.warm, fontWeight: 600, marginBottom: 8 }}>Brief Not Yet Generated</div>
                <div style={{ fontSize: 12, color: C.textDim }}>Run: python3 scripts/sales_intel_brief_v4.py --company "{co.name}"</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* PEOPLE TAB */}
      {tab === "people" && (
        <div>
          {co.contacts.length === 0 ? <EmptyState message="No contacts discovered yet. Run Apollo Pipeline to find contacts." /> : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 10 }}>
              {co.contacts.map((contact, i) => {
                const dmColor = contact.decision_maker_level === "C-Suite" ? C.gold : contact.decision_maker_level === "VP" ? C.purple : contact.decision_maker_level === "Director" ? C.cyan : C.textDim;
                return (
                  <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14, borderLeft: `3px solid ${dmColor}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: C.text }}>{contact.name || "Unknown"}</div>
                        <div style={{ fontSize: 12, color: C.textDim, marginTop: 2 }}>{contact.title || "No title"}</div>
                      </div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: tempColor(contact.temperature), fontFamily: font }}>{contact.score}</div>
                    </div>
                    <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                      {contact.decision_maker_level && <Badge color={dmColor}>{contact.decision_maker_level}</Badge>}
                      {contact.icp_tier && <Badge color={C.textDim}>{contact.icp_tier}</Badge>}
                      {contact.temperature && <Badge color={tempColor(contact.temperature)}>{contact.temperature}</Badge>}
                    </div>
                    <div style={{ marginTop: 10, fontSize: 11, color: C.textDim }}>
                      {contact.email && <div style={{ marginBottom: 3 }}>Email: <span style={{ color: contact.email_status === "Valid" || contact.email_status === "Verified" ? C.green : C.text }}>{contact.email}</span> {contact.email_status && <Badge color={contact.email_status === "Valid" || contact.email_status === "Verified" ? C.green : C.warm}>{contact.email_status}</Badge>}</div>}
                      {contact.phone && <div style={{ marginBottom: 3 }}>Phone: <span style={{ color: C.text }}>{contact.phone}</span></div>}
                      {contact.linkedin && <div>LinkedIn: <span style={{ color: C.cyan }}>{contact.linkedin.split("/in/")[1] || contact.linkedin}</span></div>}
                    </div>
                    {contact.score_reasons && contact.score_reasons.length > 0 && (
                      <div style={{ marginTop: 8, padding: "6px 8px", background: `${C.gold}08`, borderRadius: 4 }}>
                        <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 3 }}>SCORE BREAKDOWN</div>
                        <div style={{ fontSize: 10, color: C.textDim }}>{contact.score_reasons.join(" · ")}</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* INTEL TAB */}
      {tab === "intel" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {co.supplier_intel && Object.keys(co.supplier_intel).length > 0 && (
            <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16 }}>
              <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>CURRENT SUPPLIER</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 8 }}>{co.supplier_intel.most_likely_supplier || "Unknown"}</div>
              {co.supplier_intel.evidence && (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 4 }}>Evidence</div>
                  {co.supplier_intel.evidence.slice(0, 4).map((e, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.textDim, padding: "3px 0", lineHeight: 1.5 }}>{e}</div>
                  ))}
                </div>
              )}
              {co.supplier_intel.switching_triggers && (
                <div>
                  <div style={{ fontSize: 10, color: C.green, fontWeight: 600, marginBottom: 4 }}>SWITCHING TRIGGERS</div>
                  {co.supplier_intel.switching_triggers.map((t, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.text, padding: "3px 0", display: "flex", gap: 6 }}>
                      <span style={{ color: C.green }}>+</span> {t}
                    </div>
                  ))}
                </div>
              )}
              {co.supplier_intel.switching_barriers && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 10, color: C.hot, fontWeight: 600, marginBottom: 4 }}>SWITCHING BARRIERS</div>
                  {co.supplier_intel.switching_barriers.map((b, i) => (
                    <div key={i} style={{ fontSize: 11, color: C.textDim, padding: "3px 0", display: "flex", gap: 6 }}>
                      <span style={{ color: C.hot }}>-</span> {b}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {co.displacement_strategy && Object.keys(co.displacement_strategy).length > 0 && (
            <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16 }}>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>DISPLACEMENT STRATEGY</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 8 }}>{co.displacement_strategy.primary_angle}</div>
              {co.displacement_strategy.supporting_angles && co.displacement_strategy.supporting_angles.map((a, i) => (
                <div key={i} style={{ fontSize: 11, color: C.textDim, padding: "3px 0", lineHeight: 1.5 }}>{a}</div>
              ))}
              {co.displacement_strategy.sample_strategy && (
                <div style={{ marginTop: 10, padding: 10, background: `${C.gold}08`, borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 4 }}>SAMPLE STRATEGY</div>
                  <div style={{ fontSize: 11, color: C.text, lineHeight: 1.5 }}>{co.displacement_strategy.sample_strategy}</div>
                </div>
              )}
            </div>
          )}
          {co.pricing_intel && Object.keys(co.pricing_intel).length > 0 && (
            <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.gold}30`, padding: 16, gridColumn: "1 / -1" }}>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>PRICING INTELLIGENCE</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 12 }}>
                <div style={{ textAlign: "center", padding: 10, background: `${C.hot}08`, borderRadius: 6 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: C.hot, fontFamily: font }}>{co.pricing_intel.their_likely_current_cost || "?"}</div>
                  <div style={{ fontSize: 9, color: C.textDim, marginTop: 4 }}>THEIR CURRENT COST</div>
                </div>
                <div style={{ textAlign: "center", padding: 10, background: `${C.green}08`, borderRadius: 6 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: C.green, fontFamily: font }}>{co.pricing_intel.our_pricing_tier || "?"}</div>
                  <div style={{ fontSize: 9, color: C.textDim, marginTop: 4 }}>OUR PRICING</div>
                </div>
                <div style={{ textAlign: "center", padding: 10, background: `${C.gold}08`, borderRadius: 6 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: C.gold, fontFamily: font }}>{co.pricing_intel.advantage_or_gap || "?"}</div>
                  <div style={{ fontSize: 9, color: C.textDim, marginTop: 4 }}>ADVANTAGE</div>
                </div>
              </div>
              {co.pricing_intel.value_justification && (
                <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{co.pricing_intel.value_justification}</div>
              )}
            </div>
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
        <div>
          {co.deal_model && Object.keys(co.deal_model).length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.gold}30`, padding: 16 }}>
                <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>DEAL MODEL</div>
                {["conservative", "likely", "upside"].map(tier => {
                  const d = co.deal_model[tier];
                  if (!d) return null;
                  const color = tier === "conservative" ? C.cool : tier === "likely" ? C.green : C.gold;
                  return (
                    <div key={tier} style={{ padding: 12, marginBottom: 8, background: `${color}08`, borderRadius: 6, border: `1px solid ${color}25` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color, textTransform: "uppercase" }}>{tier}</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color, fontFamily: font }}>{d.annual_value || d.annual_revenue || "?"}</div>
                      </div>
                      {d.initial_liters && <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>Initial: {d.initial_liters}L ({d.initial_value || "?"})</div>}
                    </div>
                  );
                })}
              </div>
              {co.objections && co.objections.length > 0 && (
                <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16 }}>
                  <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>OBJECTION HANDLING</div>
                  {co.objections.map((obj, i) => (
                    <div key={i} style={{ padding: "8px 0", borderBottom: i < co.objections.length - 1 ? `1px solid ${C.border}` : "none" }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: C.hot, marginBottom: 4 }}>{obj.objection}</div>
                      <div style={{ fontSize: 12, color: C.text, lineHeight: 1.5 }}>{obj.response}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : <EmptyState message="No deal model available. Generate a sales intel brief to create Conservative/Likely/Upside deal projections." />}
        </div>
      )}

      {/* SIGNALS TAB */}
      {tab === "signals" && (
        <div>
          {co.signals && co.signals.length > 0 ? co.signals.map((sig, i) => (
            <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, marginBottom: 6, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <Badge color={stageColor[sig.category] || C.textDim}>{sig.category}</Badge>
                <span style={{ fontSize: 13, color: C.text }}>{sig.summary || sig.type}</span>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ fontSize: 11, color: C.textDim }}>{sig.timestamp ? sig.timestamp.split("T")[0] : ""}</span>
                <Badge color={sig.decayed_score > 0.5 ? C.green : sig.decayed_score > 0.2 ? C.warm : C.cold}>{(sig.decayed_score || 0).toFixed(2)}</Badge>
              </div>
            </div>
          )) : <EmptyState message="No signals detected for this company. Run trigger monitor or free intel scan to harvest signals." />}
        </div>
      )}

      {/* OUTREACH TAB */}
      {tab === "outreach" && (
        <div>
          {co.outreach_bundle && Object.keys(co.outreach_bundle).length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {Object.entries(co.outreach_bundle).map(([key, content]) => {
                const isText = typeof content === "string";
                return (
                  <div key={key} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, gridColumn: isText && content.length > 500 ? "1 / -1" : undefined }}>
                    <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 8 }}>{key.toUpperCase().replace(/_/g, " ")}</div>
                    {isText ? (
                      <pre style={{ fontSize: 11, color: C.text, lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word", maxHeight: 300, overflow: "auto", fontFamily: fontBody }}>{content}</pre>
                    ) : (
                      <pre style={{ fontSize: 10, color: C.textDim, lineHeight: 1.4, whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto", fontFamily: font }}>{JSON.stringify(content, null, 2)}</pre>
                    )}
                  </div>
                );
              })}
            </div>
          ) : co.outreach_sequence && co.outreach_sequence.length > 0 ? (
            <div>
              {co.outreach_sequence.map((touch, i) => (
                <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, marginBottom: 10 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                    <Badge color={C.gold}>Touch {touch.touch || i + 1}</Badge>
                    <Badge color={C.cyan}>Day {touch.day || 0}</Badge>
                    <Badge color={C.purple}>{touch.channel || "Email"}</Badge>
                    {touch.target && <span style={{ fontSize: 12, color: C.textDim }}>To: {touch.target}</span>}
                  </div>
                  {touch.subject && <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 6 }}>Subject: {touch.subject}</div>}
                  {touch.body && <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{touch.body}</div>}
                </div>
              ))}
            </div>
          ) : <EmptyState message="No outreach artifacts generated. Run kill shot bundle to generate email, LinkedIn DM, call script, and HeyGen video." />}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// TERPENE INTELLIGENCE LAB - PhD GRADE
// ═══════════════════════════════════════════════════════════

function ResearchLab({ data }) {
  const [tab, setTab] = useState("matrix");

  if (!data) return <EmptyState message="Loading research data..." />;
  const { papers_total, highlights, synthesis, trends, gaps, matrix, businessInsights, regulatory } = data;

  const tabs = [
    { id: "matrix", label: "Effect Matrix" },
    { id: "evidence", label: "Evidence" },
    { id: "commercial", label: "Commercial" },
    { id: "mechanisms", label: "Mechanisms" },
    { id: "gaps", label: "R&D Gaps" },
    { id: "regulatory", label: "Regulatory" },
  ];

  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="TERPENE INTELLIGENCE LAB" subtitle={`${papers_total || 0} papers indexed · PhD-grade evidence analysis`} />

      <div style={{ display: "flex", gap: 4, marginBottom: 20 }}>
        {tabs.map(t => <TabButton key={t.id} label={t.label} active={tab === t.id} onClick={() => setTab(t.id)} />)}
      </div>

      {/* TERPENE-EFFECT MATRIX */}
      {tab === "matrix" && (
        <div>
          {matrix ? (
            <div style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, overflow: "auto" }}>
              <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 12 }}>TERPENE x EFFECT EVIDENCE MATRIX</div>
              <div style={{ fontSize: 10, color: C.textDim, marginBottom: 12 }}>Cell values show paper count. Color intensity indicates evidence strength.</div>
              {(() => {
                const terpenes = Object.keys(matrix);
                if (terpenes.length === 0) return <EmptyState message="No matrix data available yet." />;
                const allEffects = new Set();
                terpenes.forEach(t => Object.keys(matrix[t] || {}).forEach(e => allEffects.add(e)));
                const effects = Array.from(allEffects).sort();
                const maxVal = Math.max(1, ...terpenes.flatMap(t => effects.map(e => (matrix[t] || {})[e] || 0)));
                return (
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ borderCollapse: "collapse", width: "100%", minWidth: effects.length * 80 }}>
                      <thead>
                        <tr>
                          <th style={{ padding: "6px 10px", fontSize: 10, color: C.gold, fontFamily: font, textAlign: "left", borderBottom: `1px solid ${C.border}`, position: "sticky", left: 0, background: C.surface, zIndex: 1 }}>TERPENE</th>
                          {effects.map(e => (
                            <th key={e} style={{ padding: "6px 8px", fontSize: 9, color: C.textDim, fontFamily: font, textAlign: "center", borderBottom: `1px solid ${C.border}`, textTransform: "uppercase", letterSpacing: 0.5 }}>{e.replace(/_/g, " ")}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {terpenes.map(terp => (
                          <tr key={terp}>
                            <td style={{ padding: "6px 10px", fontSize: 11, color: C.text, fontWeight: 600, borderBottom: `1px solid ${C.border}`, position: "sticky", left: 0, background: C.surface, zIndex: 1, textTransform: "capitalize" }}>{terp.replace(/_/g, " ")}</td>
                            {effects.map(eff => {
                              const val = (matrix[terp] || {})[eff] || 0;
                              const intensity = val / maxVal;
                              const bg = val > 0 ? `rgba(0, 224, 154, ${0.08 + intensity * 0.35})` : "transparent";
                              return (
                                <td key={eff} style={{ padding: "6px 8px", textAlign: "center", fontSize: 12, fontWeight: val > 0 ? 700 : 400, color: val > 0 ? C.green : C.textMuted, fontFamily: font, borderBottom: `1px solid ${C.border}`, background: bg }}>{val || ""}</td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })()}
            </div>
          ) : <EmptyState message="Run terpene research to build the evidence matrix: python3 scripts/terpene_research_v2.py --full --days 90" />}
        </div>
      )}

      {/* EVIDENCE DASHBOARD */}
      {tab === "evidence" && (
        <div>
          {highlights && highlights.length > 0 ? (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 16 }}>
                {["A", "B", "C", "D"].map(grade => {
                  const count = highlights.filter(h => h.evidenceGrade === grade).length;
                  return (
                    <div key={grade} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${gradeColor(grade)}30`, padding: 12, textAlign: "center" }}>
                      <div style={{ fontSize: 24, fontWeight: 800, color: gradeColor(grade), fontFamily: font }}>{count}</div>
                      <div style={{ fontSize: 10, color: C.textDim, marginTop: 2 }}>GRADE {grade}</div>
                      <div style={{ fontSize: 9, color: C.textMuted }}>{grade === "A" ? "Meta/Systematic" : grade === "B" ? "RCT/Cohort" : grade === "C" ? "Animal In Vivo" : "In Vitro"}</div>
                    </div>
                  );
                })}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 6 }}>
                {highlights.slice(0, 20).map((paper, i) => (
                  <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 12, display: "flex", gap: 12, alignItems: "flex-start" }}>
                    <div style={{ width: 36, height: 36, borderRadius: 6, background: `${gradeColor(paper.evidenceGrade)}15`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800, color: gradeColor(paper.evidenceGrade), fontFamily: font, flexShrink: 0 }}>{paper.evidenceGrade}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: C.text, lineHeight: 1.4, marginBottom: 4 }}>{paper.title}</div>
                      <div style={{ fontSize: 11, color: C.textDim }}>{paper.journal} ({paper.year}) · {paper.studyType} · {paper.modelOrganism}</div>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
                        {(paper.terpenes || []).map(t => <Badge key={t} color={C.green}>{t}</Badge>)}
                        {(paper.effects || []).map(e => <Badge key={e} color={C.cyan}>{e.replace(/_/g, " ")}</Badge>)}
                        {paper.outcomeDirection && <Badge color={paper.outcomeDirection === "positive" ? C.green : paper.outcomeDirection === "negative" ? C.hot : C.textDim}>{paper.outcomeDirection}</Badge>}
                      </div>
                      {paper.mechanisms && paper.mechanisms.length > 0 && (
                        <div style={{ fontSize: 10, color: C.purple, marginTop: 4 }}>Mechanisms: {paper.mechanisms.join(", ")}</div>
                      )}
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: C.gold, fontFamily: font }}>{paper.score}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : <EmptyState message="No papers indexed yet. Run: python3 scripts/terpene_research_v2.py --harvest --days 90" />}
        </div>
      )}

      {/* COMMERCIAL TRANSLATOR */}
      {tab === "commercial" && (
        <div>
          {businessInsights && businessInsights.length > 0 ? (
            <div>
              <div style={{ background: `${C.gold}08`, borderRadius: 8, border: `1px solid ${C.gold}30`, padding: 14, marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: C.gold, fontWeight: 600 }}>These insights translate peer-reviewed research into compliance-safe selling points. No medical claims — only consumer preference and formulation-level framing.</div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 12 }}>
                {businessInsights.map((ins, i) => {
                  const typeColor = ins.type === "weekly_bet" ? C.gold : ins.type === "trend_alert" ? C.cyan : C.purple;
                  const typeLabel = ins.type === "weekly_bet" ? "WEEKLY BET" : ins.type === "trend_alert" ? "TREND ALERT" : "R&D OPPORTUNITY";
                  return (
                    <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, borderLeft: `3px solid ${typeColor}` }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <Badge color={typeColor}>{typeLabel}</Badge>
                          <span style={{ fontSize: 15, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{ins.terpene}</span>
                          <Badge color={C.textDim}>{ins.category}</Badge>
                        </div>
                        <div style={{ display: "flex", gap: 2 }}>
                          {Array.from({ length: 6 }, (_, j) => (
                            <div key={j} style={{ width: 8, height: 8, borderRadius: 2, background: j < (ins.confidence || 0) ? typeColor : C.border }} />
                          ))}
                        </div>
                      </div>
                      <div style={{ fontSize: 13, color: C.text, lineHeight: 1.6, marginBottom: 10, padding: "8px 12px", background: `${C.green}06`, borderRadius: 6, borderLeft: `2px solid ${C.green}40` }}>
                        "{ins.safe_framing}"
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <div>
                          <div style={{ fontSize: 10, color: C.cyan, fontWeight: 600, marginBottom: 4 }}>PRODUCT ANGLE</div>
                          <div style={{ fontSize: 12, color: C.text, lineHeight: 1.5 }}>{ins.product_angle}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: 10, color: C.warm, fontWeight: 600, marginBottom: 4 }}>SALES ANGLE</div>
                          <div style={{ fontSize: 12, color: C.text, lineHeight: 1.5 }}>{ins.sales_angle}</div>
                        </div>
                      </div>
                      <div style={{ marginTop: 8, padding: "6px 10px", background: `${C.gold}08`, borderRadius: 4 }}>
                        <div style={{ fontSize: 10, color: C.gold, fontWeight: 600 }}>WHY WE CAN SAY IT</div>
                        <div style={{ fontSize: 11, color: C.textDim, marginTop: 2 }}>{ins.why_we_can_say_it}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : <EmptyState message="No business insights available. Run: python3 scripts/terpene_research_v2.py --synthesize" />}
        </div>
      )}

      {/* MECHANISMS */}
      {tab === "mechanisms" && (
        <div>
          {highlights && highlights.length > 0 ? (() => {
            const mechMap = {};
            highlights.forEach(p => {
              (p.mechanisms || []).forEach(m => {
                if (!mechMap[m]) mechMap[m] = { mechanism: m, terpenes: new Set(), papers: 0, effects: new Set() };
                mechMap[m].papers++;
                (p.terpenes || []).forEach(t => mechMap[m].terpenes.add(t));
                (p.effects || []).forEach(e => mechMap[m].effects.add(e));
              });
            });
            const mechs = Object.values(mechMap).sort((a, b) => b.papers - a.papers).slice(0, 20);
            return mechs.length > 0 ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {mechs.map(m => (
                  <div key={m.mechanism} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 14 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: C.purple, textTransform: "capitalize" }}>{m.mechanism.replace(/_/g, " ")}</div>
                      <Badge color={C.textDim}>{m.papers} papers</Badge>
                    </div>
                    <div style={{ marginBottom: 6 }}>
                      <div style={{ fontSize: 10, color: C.gold, fontWeight: 600, marginBottom: 3 }}>TERPENES</div>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {Array.from(m.terpenes).map(t => <Badge key={t} color={C.green}>{t}</Badge>)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, color: C.cyan, fontWeight: 600, marginBottom: 3 }}>EFFECTS</div>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {Array.from(m.effects).map(e => <Badge key={e} color={C.cyan}>{e.replace(/_/g, " ")}</Badge>)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : <EmptyState message="No mechanism data extracted yet." />;
          })() : <EmptyState message="No papers indexed yet." />}
        </div>
      )}

      {/* R&D GAPS */}
      {tab === "gaps" && (
        <div>
          {gaps ? (
            <div>
              {gaps.underweighted_by_tbf && gaps.underweighted_by_tbf.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: C.purple, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>UNDERWEIGHTED TERPENES (Research > Product Focus)</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10 }}>
                    {gaps.underweighted_by_tbf.slice(0, 10).map((g, i) => (
                      <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.purple}30`, padding: 14 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{(g.terpene || "").replace(/_/g, " ")}</div>
                          <Badge color={C.purple}>Gap: {(g.gap_score || 0).toFixed(4)}</Badge>
                        </div>
                        <div style={{ fontSize: 11, color: C.textDim }}>Evidence share: {g.evidence_share || 0} papers</div>
                        <div style={{ fontSize: 11, color: C.textDim }}>Product focus: {g.tbf_focus_units || 0} lines</div>
                        <div style={{ marginTop: 6 }}>
                          <ProgressBar segments={[
                            { label: "Evidence", value: g.evidence_share || 1, color: C.purple },
                            { label: "Product", value: g.tbf_focus_units || 0.1, color: C.gold },
                          ]} height={4} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {gaps.overweighted_by_tbf && gaps.overweighted_by_tbf.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, color: C.gold, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>OVERWEIGHTED TERPENES (Product Focus > Research)</div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 10 }}>
                    {gaps.overweighted_by_tbf.slice(0, 6).map((g, i) => (
                      <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.gold}30`, padding: 14 }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: C.text, textTransform: "capitalize" }}>{(g.terpene || "").replace(/_/g, " ")}</div>
                        <div style={{ fontSize: 11, color: C.textDim, marginTop: 4 }}>Product focus exceeds evidence base</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : <EmptyState message="Run gap analysis: python3 scripts/terpene_research_v2.py --gaps" />}
        </div>
      )}

      {/* REGULATORY */}
      {tab === "regulatory" && (
        <div>
          {regulatory && regulatory.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8 }}>
              {regulatory.map((r, i) => (
                <div key={i} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.hot}20`, padding: 14, borderLeft: `3px solid ${C.hot}` }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>{r.title || r.topic || "Regulatory Hit"}</div>
                  <div style={{ fontSize: 11, color: C.textDim, lineHeight: 1.5 }}>{r.summary || r.detail || JSON.stringify(r)}</div>
                  {r.terpenes && <div style={{ display: "flex", gap: 4, marginTop: 6 }}>{r.terpenes.map(t => <Badge key={t} color={C.hot}>{t}</Badge>)}</div>}
                </div>
              ))}
            </div>
          ) : <EmptyState message="No regulatory signals found. Run: python3 scripts/terpene_research_v2.py --regulatory" />}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// AGENTS VIEW
// ═══════════════════════════════════════════════════════════

function AgentsView({ agents }) {
  const statusColor = (s) => s === "active" ? C.green : s === "deployed" ? C.cool : s === "ready" ? C.warm : C.textDim;
  const list = agents || [];
  return (
    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>
      <SectionHeader title="AGENT FLEET" subtitle={`${list.length} specialized agents`} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 10 }}>
        {list.map(a => (
          <div key={a.agent_id || a.name} style={{ background: C.surface, borderRadius: 8, border: `1px solid ${C.border}`, padding: 16, borderLeft: `3px solid ${statusColor(a.status || "standby")}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{a.name}</span>
              <Badge color={statusColor(a.status || "standby")}>{a.status || "standby"}</Badge>
            </div>
            <div style={{ fontSize: 12, color: C.textDim, lineHeight: 1.5, marginBottom: 6 }}>{a.description}</div>
            <div style={{ fontSize: 10, color: C.textMuted, fontFamily: font }}>{a.script}</div>
            {a.commands && <div style={{ fontSize: 10, color: C.textMuted, marginTop: 4 }}>{a.commands.join(" ")}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// COMMAND CENTER - CHAT
// ═══════════════════════════════════════════════════════════

function CommandCenter({ onSelectCompany }) {
  const [messages, setMessages] = useState([{ role: "assistant", content: "Nexus BDR System online. All agents operational.\n\nAsk me anything — company research, pipeline status, competitor analysis, terpene science, or outreach strategy." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => { if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight; }, [messages]);

  const send = useCallback(async () => {
    if (!input.trim() || loading) return;
    const msg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const resp = await fetch("/api/reef/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: messages.slice(-6) }),
      });
      const data = await resp.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.response || "No response.", agents: data.agents_activated }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Connection error. Make sure the server is running." }]);
    }
    setLoading(false);
  }, [input, loading, messages]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div ref={chatRef} style={{ flex: 1, overflow: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 10 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{
              maxWidth: "85%", padding: "10px 16px", borderRadius: msg.role === "user" ? "12px 12px 0 12px" : "12px 12px 12px 0",
              background: msg.role === "user" ? `${C.gold}20` : C.surface,
              border: `1px solid ${msg.role === "user" ? C.gold + "40" : C.border}`,
              fontSize: 13, color: C.text, lineHeight: 1.6, whiteSpace: "pre-wrap",
            }}>
              {msg.content}
              {msg.agents && msg.agents.length > 0 && (
                <div style={{ display: "flex", gap: 4, marginTop: 8, flexWrap: "wrap" }}>
                  {msg.agents.map((a, j) => <Badge key={j} color={C.green}>{a.script || a}</Badge>)}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div style={{ color: C.gold, fontSize: 14, padding: 8 }}>Thinking...</div>}
      </div>
      <div style={{ padding: "12px 20px", borderTop: `1px solid ${C.border}`, display: "flex", gap: 8, background: C.void }}>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
          placeholder="Ask anything — research, pipeline, strategy..."
          style={{ flex: 1, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6, padding: "10px 16px", color: C.text, fontSize: 14, fontFamily: fontBody, outline: "none" }} />
        <button onClick={send} style={{ background: C.gold, color: C.void, border: "none", borderRadius: 6, padding: "10px 20px", fontWeight: 700, cursor: "pointer", fontSize: 13 }}>Send</button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// MAIN APP
// ═══════════════════════════════════════════════════════════

export default function NexusV5() {
  const [booted, setBooted] = useState(false);
  const [bootLines, setBootLines] = useState([]);
  const [view, setView] = useState("PIPELINE");
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [researchData, setResearchData] = useState(null);
  const [agentData, setAgentData] = useState(null);
  const [companyCache, setCompanyCache] = useState({});

  const BOOT_LINES = [
    { text: "NEXUS BDR SYSTEM v6.0 — INITIALIZING", color: C.gold },
    { text: "Loading agent fleet...", color: C.text },
    { text: "Connecting to pipeline data...", color: C.text },
    { text: "Building company dossiers...", color: C.text },
    { text: "Indexing terpene research...", color: C.text },
    { text: "Calculating revenue forecast...", color: C.green },
    { text: "SYSTEM ONLINE — All agents operational", color: C.green },
  ];

  // Boot sequence
  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < BOOT_LINES.length) {
        setBootLines(prev => [...prev, BOOT_LINES[i]]);
        i++;
      } else {
        clearInterval(timer);
        setTimeout(() => setBooted(true), 400);
      }
    }, 150);
    return () => clearInterval(timer);
  }, []);

  // Load data on boot
  useEffect(() => {
    if (!booted) return;
    fetch("/api/reef/pipeline").then(r => r.json()).then(setPipelineData).catch(() => {});
    fetch("/api/reef/research").then(r => r.json()).then(setResearchData).catch(() => {});
    fetch("/api/agents").then(r => r.json()).then(d => setAgentData(d.agents || [])).catch(() => {});
  }, [booted]);

  const handleSelectCompany = useCallback((name) => {
    if (companyCache[name]) {
      setSelectedCompany(companyCache[name]);
      return;
    }
    fetch(`/api/reef/company/${encodeURIComponent(name)}`).then(r => r.json()).then(d => {
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
        <div style={{ fontSize: 32, fontWeight: 800, background: `linear-gradient(135deg, ${C.gold}, ${C.goldLight})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: 32, letterSpacing: 6 }}>NEXUS</div>
        <div style={{ maxWidth: 500, width: "100%" }}>
          {bootLines.map((line, i) => (
            <div key={i} style={{ color: line.color, fontSize: 13, padding: "4px 0", opacity: 0, animation: "fadeIn 0.3s forwards", animationDelay: `${i * 0.05}s` }}>
              <span style={{ color: C.textDim, marginRight: 8 }}>[{String(i).padStart(2, "0")}]</span>{line.text}
            </div>
          ))}
        </div>
        <style>{`@keyframes fadeIn { to { opacity: 1 } }`}</style>
      </div>
    );
  }

  const views = [
    { id: "PIPELINE", label: "PIPELINE" },
    { id: "RESEARCH", label: "RESEARCH" },
    { id: "COMMAND", label: "COMMAND" },
    { id: "AGENTS", label: "AGENTS" },
  ];

  // Company dossier view
  if (selectedCompany) {
    return (
      <div style={{ background: C.bg, minHeight: "100vh", fontFamily: fontBody, color: C.text }}>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
        <CompanyDossier company={selectedCompany} onBack={() => setSelectedCompany(null)} />
        <style>{`::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:${C.void}}::-webkit-scrollbar-thumb{background:${C.border};border-radius:3px}::-webkit-scrollbar-thumb:hover{background:${C.gold}40}`}</style>
      </div>
    );
  }

  return (
    <div style={{ background: C.bg, minHeight: "100vh", fontFamily: fontBody, color: C.text }}>
      <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      {/* Header */}
      <div style={{ padding: "10px 24px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: `1px solid ${C.border}`, background: C.void }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 20, fontWeight: 800, background: `linear-gradient(135deg, ${C.gold}, ${C.goldLight})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", letterSpacing: 4, fontFamily: font }}>NEXUS</span>
          <span style={{ color: C.textDim, fontSize: 11, fontFamily: font }}>BDR Intelligence v6.0</span>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {views.map(v => <TabButton key={v.id} label={v.label} active={view === v.id} onClick={() => setView(v.id)} />)}
        </div>
      </div>

      {/* Content */}
      <div style={{ height: "calc(100vh - 48px)" }}>
        {view === "PIPELINE" && <PipelineView data={pipelineData} onSelectCompany={handleSelectCompany} />}
        {view === "RESEARCH" && <ResearchLab data={researchData} />}
        {view === "COMMAND" && <CommandCenter onSelectCompany={handleSelectCompany} />}
        {view === "AGENTS" && <AgentsView agents={agentData} />}
      </div>

      <style>{`
        ::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:${C.void}}::-webkit-scrollbar-thumb{background:${C.border};border-radius:3px}::-webkit-scrollbar-thumb:hover{background:${C.gold}40}
      `}</style>
    </div>
  );
}
