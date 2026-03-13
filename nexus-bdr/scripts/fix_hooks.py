#!/usr/bin/env python3
"""Fix React hooks ordering violations in nexus_v5.jsx"""

with open("scripts/nexus_v5.jsx", "r") as f:
    code = f.read()

fixes = 0

# Fix 1: PipelineView - early return before useMemo
old = '  if (!data) return <EmptyState message="Loading pipeline data..." />;\n\n  const { total_companies, total_contacts, total_emails, total_verified, temperatures, brand_split, stages, forecast, hot_list, companies } = data;\n\n  const filteredCompanies = useMemo(() => {'
new = '  const { total_companies, total_contacts, total_emails, total_verified, temperatures, brand_split, stages, forecast, hot_list, companies } = data || {};\n\n  const filteredCompanies = useMemo(() => {\n    if (!data) return [];'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print("1. Fixed PipelineView hooks order")

# Fix 2: ResearchLab - early return before useMemo
old = '  if (!data) return <EmptyState message="Loading research data..." />;\n  const { papers_total, highlights, synthesis, trends, gaps, matrix, businessInsights, regulatory } = data;'
new = '  const { papers_total, highlights, synthesis, trends, gaps, matrix, businessInsights, regulatory } = data || {};'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print("2. Fixed ResearchLab hooks order")

# Fix 3: CompanyDossier - early return before useMemo
old = '  const co = company;\n  if (!co) return null;'
new = '  const co = company || {};'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print("3. Fixed CompanyDossier hooks order")

# Fix 4: SignalIntel - early return before useMemo
old = '  if (!data) return <EmptyState message="Loading signals..." />;\n\n  const signals = data.signals || [];\n  const signalWeights = data.signal_weights || {};'
new = '  const signals = (data && data.signals) || [];\n  const signalWeights = (data && data.signal_weights) || {};'
if old in code:
    code = code.replace(old, new)
    # Add the early return AFTER the useMemo calls
    old_after = '  }, [signals, categoryFilter, search]);\n\n  const avgDecay'
    new_after = '  }, [signals, categoryFilter, search]);\n\n  if (!data) return <EmptyState message="Loading signals..." />;\n\n  const avgDecay'
    if old_after in code:
        code = code.replace(old_after, new_after)
    fixes += 1
    print("4. Fixed SignalIntel hooks order")

# Fix 5: Add data guard wrapper in PipelineView render
old = '    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>\n      {/* Revenue Intelligence Header */}'
new = '    <div style={{ padding: 24, overflow: "auto", height: "100%" }}>\n      {!data && <EmptyState message="Loading pipeline data..." />}\n      {data && <div>\n      {/* Revenue Intelligence Header */}'
if old in code:
    code = code.replace(old, new)
    old_end = '      <div style={{ marginTop: 12, fontSize: 11, color: C.textMuted, textAlign: "center" }}>\n        Showing {filteredCompanies.length} of {(companies || []).length} companies\n        {tempFilter !== "all" && " \\u00B7 Filter: " + tempFilter}\n        {search && " \\u00B7 Search: \\"" + search + "\\""}\n      </div>\n    </div>\n  );\n}'
    new_end = '      <div style={{ marginTop: 12, fontSize: 11, color: C.textMuted, textAlign: "center" }}>\n        Showing {filteredCompanies.length} of {(companies || []).length} companies\n        {tempFilter !== "all" && " \\u00B7 Filter: " + tempFilter}\n        {search && " \\u00B7 Search: \\"" + search + "\\""}\n      </div>\n      </div>}\n    </div>\n  );\n}'
    if old_end in code:
        code = code.replace(old_end, new_end)
    fixes += 1
    print("5. Added data guard wrapper in PipelineView render")

# Fix 6: Boot sequence closure bug
old = 'setBootLines(prev => [...prev, BOOT_LINES[i]]);\n        i++;'
new = 'const line = BOOT_LINES[i];\n        i++;\n        setBootLines(prev => [...prev, line]);'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print("6. Fixed boot sequence closure bug")

# Fix 7: Boot line render null guard
old = 'bootLines.map((line, i) => ('
new = 'bootLines.filter(Boolean).map((line, i) => ('
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print("7. Added boot line null guard")

old = 'style={{ color: line.color,'
new = 'style={{ color: (line && line.color) || "#e8e8f0",'
if old in code:
    code = code.replace(old, new)
    fixes += 1
    print("8. Added boot line color fallback")

with open("scripts/nexus_v5.jsx", "w") as f:
    f.write(code)

print(f"\nApplied {fixes} fixes. Restart: python3 scripts/reef_server.py")
