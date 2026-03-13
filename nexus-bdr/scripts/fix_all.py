#!/usr/bin/env python3
"""
Comprehensive fix for nexus_v5.jsx — fixes ALL data shape mismatches
between the frontend and the actual API responses.

API data shapes discovered:
- stages: DICT {new: {count, companies}, scored: {count, companies}, ...} NOT array
- competitors: LIST of {name, pricing (string), weakness (string), risk, tbf_angle, dft_angle, ...}
- analytics: {pipeline, intelligence, system, learning} NOT {pipeline_health, intelligence_metrics, ...}
- competitor.threat_level -> competitor.risk
- competitor.weaknesses (array) -> competitor.weakness (string)
"""

with open("scripts/nexus_v5.jsx", "r") as f:
    code = f.read()

fixes = 0

# ============================================================
# FIX 1: Boot sequence closure bug
# ============================================================
old = 'setBootLines(prev => [...prev, BOOT_LINES[i]]);\n        i++;'
new = 'const line = BOOT_LINES[i];\n        i++;\n        setBootLines(prev => [...prev, line]);'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed boot sequence closure bug")

# ============================================================
# FIX 2: Boot line render null guard
# ============================================================
old = 'bootLines.map((line, i) => ('
new = 'bootLines.filter(Boolean).map((line, i) => ('
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Added boot line filter(Boolean)")

old = 'style={{ color: line.color,'
new = 'style={{ color: (line && line.color) || "#e8e8f0",'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Added boot line color fallback")

# ============================================================
# FIX 3: PipelineView - early return before useMemo
# ============================================================
old = '  if (!data) return <EmptyState message="Loading pipeline data..." />;\n\n  const { total_companies, total_contacts, total_emails, total_verified, temperatures, brand_split, stages, forecast, hot_list, companies } = data;\n\n  const filteredCompanies = useMemo(() => {'
new = '  const { total_companies, total_contacts, total_emails, total_verified, temperatures, brand_split, stages, forecast, hot_list, companies } = data || {};\n\n  const filteredCompanies = useMemo(() => {\n    if (!data) return [];'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed PipelineView early return before useMemo")

# ============================================================
# FIX 4: stages is a DICT not array — fix conversionRate
# ============================================================
old = 'const conversionRate = total_companies ? ((stages || []).filter(s => s.stage === "won").reduce((a, s) => a + s.count, 0) / total_companies * 100).toFixed(1) : "0";'
new = 'const stagesArray = stages ? Object.entries(stages).map(function(entry) { return { stage: entry[0], count: (entry[1] && entry[1].count) || 0, companies: (entry[1] && entry[1].companies) || [] }; }) : [];\n  const conversionRate = total_companies && stagesArray.length > 0 ? (stagesArray.filter(function(s) { return s.stage === "won"; }).reduce(function(a, s) { return a + s.count; }, 0) / total_companies * 100).toFixed(1) : "0";'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed stages dict -> array conversion")

# ============================================================
# FIX 5: Kanban view — stages is dict not array
# ============================================================
old = '          {(stages || []).filter(s => s.count > 0).map(stage => {'
new = '          {stagesArray.filter(s => s.count > 0).map(stage => {'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed kanban stages iteration")

# ============================================================
# FIX 6: Add data guard wrapper in PipelineView render
# ============================================================
old = '    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>\n      {/* Revenue Intelligence Header */}'
new = '    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>\n      {!data && <EmptyState message="Loading pipeline data..." />}\n      {data && <div>\n      {/* Revenue Intelligence Header */}'
if old in code:
    code = code.replace(old, new)
    old_end = '      <div style={{ marginTop: 12, fontSize: 11, color: C.textMuted, textAlign: "center" }}>\n        Showing {filteredCompanies.length} of {(companies || []).length} companies\n        {tempFilter !== "all" && " \\u00B7 Filter: " + tempFilter}\n        {search && " \\u00B7 Search: \\"" + search + "\\""}\n      </div>\n    </div>\n  );\n}'
    new_end = '      <div style={{ marginTop: 12, fontSize: 11, color: C.textMuted, textAlign: "center" }}>\n        Showing {filteredCompanies.length} of {(companies || []).length} companies\n        {tempFilter !== "all" && " \\u00B7 Filter: " + tempFilter}\n        {search && " \\u00B7 Search: \\"" + search + "\\""}\n      </div>\n      </div>}\n    </div>\n  );\n}'
    if old_end in code:
        code = code.replace(old_end, new_end)
    fixes += 1
    print(f"{fixes}. Added PipelineView data guard wrapper")

# ============================================================
# FIX 7: ResearchLab - early return before useMemo
# ============================================================
old = '  if (!data) return <EmptyState message="Loading research data..." />;\n  const { papers_total, highlights, synthesis, trends, gaps, matrix, businessInsights, regulatory } = data;'
new = '  const { papers_total, highlights, synthesis, trends, gaps, matrix, businessInsights, regulatory } = data || {};'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed ResearchLab early return before useMemo")

# ============================================================
# FIX 8: CompanyDossier - early return before useMemo
# ============================================================
old = '  const co = company;\n  if (!co) return null;'
new = '  const co = company || {};'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed CompanyDossier early return")

# ============================================================
# FIX 9: SignalIntel - early return before useMemo
# ============================================================
old = '  if (!data) return <EmptyState message="Loading signals..." />;\n\n  const signals = data.signals || [];\n  const signalWeights = data.signal_weights || {};'
new = '  const signals = (data && data.signals) || [];\n  const signalWeights = (data && data.signal_weights) || {};'
if old in code:
    code = code.replace(old, new)
    old_after = '  }, [signals, categoryFilter, search]);\n\n  const avgDecay'
    new_after = '  }, [signals, categoryFilter, search]);\n\n  if (!data) return <EmptyState message="Loading signals..." />;\n\n  const avgDecay'
    if old_after in code:
        code = code.replace(old_after, new_after)
    fixes += 1
    print(f"{fixes}. Fixed SignalIntel early return before useMemo")

# ============================================================
# FIX 10: Analytics — field names don't match API
# API returns {pipeline, intelligence, system, learning}
# Code expects {pipeline_health, intelligence_metrics, system_stats, learning_metrics}
# ============================================================
old = '  const { pipeline_health, intelligence_metrics, system_stats, learning_metrics } = data;\n  const ph = pipeline_health || {};\n  const im = intelligence_metrics || {};\n  const ss = system_stats || {};\n  const lm = learning_metrics || {};'
new = '  const ph = (data && data.pipeline) || (data && data.pipeline_health) || {};\n  const im = (data && data.intelligence) || (data && data.intelligence_metrics) || {};\n  const ss = (data && data.system) || (data && data.system_stats) || {};\n  const lm = (data && data.learning) || (data && data.learning_metrics) || {};'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print(f"{fixes}. Fixed Analytics field name mapping")

# ============================================================
# FIX 11: Competitor — threat_level -> risk, weaknesses -> weakness (string)
# ============================================================
# threat_level -> risk
code = code.replace('comp.threat_level === "HIGH"', '(comp.threat_level || comp.risk) === "HIGH"')
code = code.replace('comp.threat_level === "MEDIUM"', '(comp.threat_level || comp.risk) === "MEDIUM"')
code = code.replace('{comp.threat_level || "MEDIUM"}', '{comp.threat_level || comp.risk || "MEDIUM"}')
fixes += 1
print(f"{fixes}. Fixed competitor threat_level -> risk mapping")

# weaknesses (array) -> weakness (string) — make it work with both
old_w = '              {comp.weaknesses && comp.weaknesses.length > 0 && (\n                <div style={{ marginBottom: 8 }}>\n                  <div style={{ fontSize: 9, color: C.hot, fontWeight: 600, marginBottom: 3, fontFamily: font }}>WEAKNESSES</div>\n                  {comp.weaknesses.slice(0, 2).map((w, j) => (\n                    <div key={j} style={{ fontSize: 10, color: C.textDim, lineHeight: 1.4, display: "flex", gap: 4 }}>\n                      <span style={{ color: C.hot }}>{\"\\u2022\"}</span> {typeof w === "string" ? w : w.weakness || w.description || JSON.stringify(w)}\n                    </div>\n                  ))}\n                </div>\n              )}'
new_w = '              {(comp.weaknesses || comp.weakness) && (\n                <div style={{ marginBottom: 8 }}>\n                  <div style={{ fontSize: 9, color: C.hot, fontWeight: 600, marginBottom: 3, fontFamily: font }}>WEAKNESSES</div>\n                  {Array.isArray(comp.weaknesses) ? comp.weaknesses.slice(0, 2).map(function(w, j) { return (\n                    <div key={j} style={{ fontSize: 10, color: C.textDim, lineHeight: 1.4, display: "flex", gap: 4 }}>\n                      <span style={{ color: C.hot }}>{\"\\u2022\"}</span> {typeof w === "string" ? w : w.weakness || w.description || JSON.stringify(w)}\n                    </div>\n                  ); }) : <div style={{ fontSize: 10, color: C.textDim, lineHeight: 1.4, display: "flex", gap: 4 }}><span style={{ color: C.hot }}>{\"\\u2022\"}</span> {comp.weakness}</div>}\n                </div>\n              )}'
if old_w in code:
    code = code.replace(old_w, new_w)
    fixes += 1
    print(f"{fixes}. Fixed competitor weaknesses array vs string")

# Fix competitor pricing — API returns string like "$25-50/L" not object
old_p = '''              {comp.pricing && (
                <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                  {comp.pricing.low && <div style={{ fontSize: 10, color: C.textDim }}>{comp.pricing.low} - {comp.pricing.high}/L</div>}
                  {comp.pricing.avg && <div style={{ fontSize: 10, color: C.gold }}>Avg: {comp.pricing.avg}/L</div>}
                </div>
              )}'''
new_p = '''              {comp.pricing && (
                <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                  <div style={{ fontSize: 10, color: C.gold }}>{typeof comp.pricing === "string" ? comp.pricing : (comp.pricing.low || "") + " - " + (comp.pricing.high || "")}</div>
                </div>
              )}'''
if old_p in code:
    code = code.replace(old_p, new_p)
    fixes += 1
    print(f"{fixes}. Fixed competitor pricing string vs object")

# Fix deep dive pricing section
old_dp = '''                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
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
                  {selected.pricing.moq && <div style={{ fontSize: 11, color: C.textDim }}>MOQ: {selected.pricing.moq}</div>}'''
new_dp = '''                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 18, fontWeight: 700, color: C.gold, fontFamily: font }}>{typeof selected.pricing === "string" ? selected.pricing : JSON.stringify(selected.pricing)}</div>
                    <div style={{ fontSize: 9, color: C.textDim }}>PRICING RANGE</div>
                  </div>'''
if old_dp in code:
    code = code.replace(old_dp, new_dp)
    fixes += 1
    print(f"{fixes}. Fixed competitor deep dive pricing")

# Fix deep dive weaknesses
old_dw = '              {selected.weaknesses && selected.weaknesses.length > 0 && (\n                <div style={{ padding: 14, background: C.hot + "06", borderRadius: 8, border: "1px solid " + C.hot + "15" }}>\n                  <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>WEAKNESSES ({selected.weaknesses.length})</div>\n                  {selected.weaknesses.map((w, j) => (\n                    <div key={j} style={{ fontSize: 11, color: C.text, padding: "4px 0", lineHeight: 1.5, display: "flex", gap: 6 }}>\n                      <span style={{ color: C.hot }}>{\"\\u2022\"}</span> {typeof w === "string" ? w : w.weakness || JSON.stringify(w)}\n                    </div>\n                  ))}\n                </div>\n              )}'
new_dw = '              {(selected.weaknesses || selected.weakness) && (\n                <div style={{ padding: 14, background: C.hot + "06", borderRadius: 8, border: "1px solid " + C.hot + "15" }}>\n                  <div style={{ fontSize: 11, color: C.hot, fontWeight: 700, fontFamily: font, letterSpacing: 2, marginBottom: 10 }}>WEAKNESSES</div>\n                  {Array.isArray(selected.weaknesses) ? selected.weaknesses.map(function(w, j) { return (\n                    <div key={j} style={{ fontSize: 11, color: C.text, padding: "4px 0", lineHeight: 1.5, display: "flex", gap: 6 }}>\n                      <span style={{ color: C.hot }}>{\"\\u2022\"}</span> {typeof w === "string" ? w : w.weakness || JSON.stringify(w)}\n                    </div>\n                  ); }) : <div style={{ fontSize: 11, color: C.text, padding: "4px 0", lineHeight: 1.5, display: "flex", gap: 6 }}><span style={{ color: C.hot }}>{\"\\u2022\"}</span> {selected.weakness}</div>}\n                </div>\n              )}'
if old_dw in code:
    code = code.replace(old_dw, new_dw)
    fixes += 1
    print(f"{fixes}. Fixed competitor deep dive weaknesses")

# ============================================================
# FIX 12: Analytics stage_breakdown — stages is dict not array
# ============================================================
old_sb = '            {(ph.stage_breakdown || []).map((stage, i) => {\n              const maxCount = Math.max(...(ph.stage_breakdown || []).map(s => s.count || 0), 1);'
new_sb = '            {(function() { var sb = ph.stage_breakdown || ph.stages; if (!sb) return null; var arr = Array.isArray(sb) ? sb : Object.entries(sb).map(function(e) { return { stage: e[0], count: (e[1] && e[1].count) || (typeof e[1] === "number" ? e[1] : 0) }; }); var maxCount = Math.max.apply(null, arr.map(function(s) { return s.count || 0; }).concat([1])); return arr; })().map((stage, i) => {\n              const maxCount = Math.max.apply(null, (function() { var sb = ph.stage_breakdown || ph.stages; if (!sb) return [1]; var arr = Array.isArray(sb) ? sb : Object.entries(sb).map(function(e) { return { stage: e[0], count: (e[1] && e[1].count) || (typeof e[1] === "number" ? e[1] : 0) }; }); return arr.map(function(s) { return s.count || 0; }).concat([1]); })());'
if old_sb in code:
    code = code.replace(old_sb, new_sb)
    fixes += 1
    print(f"{fixes}. Fixed analytics stage_breakdown")

# Simpler fix: just replace the whole stage funnel section
# Actually let me do a simpler approach for analytics stages
old_temp = '              {ph.temperature_breakdown && ('
new_temp = '              {(ph.temperature_breakdown || ph.temperatures) && ('
if old_temp in code:
    code = code.replace(old_temp, new_temp)

old_temp2 = '                {Object.entries(ph.temperature_breakdown).map(([temp, count]) => ('
new_temp2 = '                {Object.entries(ph.temperature_breakdown || ph.temperatures || {}).map(([temp, count]) => ('
if old_temp2 in code:
    code = code.replace(old_temp2, new_temp2)

old_brand = '              {ph.brand_breakdown && Object.entries(ph.brand_breakdown).map(([brand, count]) => ('
new_brand = '              {(ph.brand_breakdown || ph.brands) && Object.entries(ph.brand_breakdown || ph.brands || {}).map(([brand, count]) => ('
if old_brand in code:
    code = code.replace(old_brand, new_brand)
    fixes += 1
    print(f"{fixes}. Fixed analytics temperature/brand field names")

# ============================================================
# WRITE RESULT
# ============================================================
with open("scripts/nexus_v5.jsx", "w") as f:
    f.write(code)

print(f"\n{'='*50}")
print(f"Applied {fixes} fixes total")
print(f"Restart: python3 scripts/reef_server.py")
print(f"{'='*50}")
