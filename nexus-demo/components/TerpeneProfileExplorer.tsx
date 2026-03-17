import React, { CSSProperties, useState, useMemo } from "react";

// ─── Types ───────────────────────────────────────────────────────
interface Terpene {
  id: string;
  name: string;
  aroma: string;
  effect: string;
  description: string;
  applications: string[];
}

interface Props {
  apiUrl?: string;
  accentColor?: string;
}

// ─── Mock Data (used when no API is connected) ───────────────────
const MOCK_TERPENES: Terpene[] = [
  { id: "terp-001", name: "Myrcene", aroma: "Earthy, musky, ripe fruit", effect: "Relaxation", description: "The most abundant terpene in modern cannabis cultivars. Contributes sedative and anti-inflammatory properties.", applications: ["Cannabis extracts", "Sleep-aid beverages", "Topical formulations"] },
  { id: "terp-002", name: "Limonene", aroma: "Bright citrus, lemon zest", effect: "Energy", description: "Prevalent in citrus rinds. Associated with elevated mood and stress relief.", applications: ["Citrus beverages", "Mood-enhancing edibles", "Flavor systems"] },
  { id: "terp-003", name: "Linalool", aroma: "Floral, lavender, subtle spice", effect: "Calm", description: "Found in lavender and 200+ plant species. Demonstrates anxiolytic and sedative properties.", applications: ["Aromatherapy", "Calming beverages", "Skincare"] },
  { id: "terp-004", name: "Beta-Caryophyllene", aroma: "Spicy, peppery, woody", effect: "Relief", description: "Unique in its ability to bind CB2 receptors. Potent anti-inflammatory activity.", applications: ["Supplements", "Spice beverages", "Pain-relief topicals"] },
  { id: "terp-005", name: "Pinene", aroma: "Fresh pine, herbal", effect: "Focus", description: "Most widely encountered terpene in nature. Supports memory retention and alertness.", applications: ["Focus beverages", "Respiratory supplements", "Forest flavors"] },
  { id: "terp-006", name: "Terpinolene", aroma: "Piney, floral, herbaceous", effect: "Energy", description: "Complex aromatic profile with antioxidant properties.", applications: ["Uplifting beverages", "Personal care", "Sativa blends"] },
  { id: "terp-007", name: "Humulene", aroma: "Hoppy, earthy, wood", effect: "Relief", description: "Found in hops and ginseng. Appetite-suppressant and anti-inflammatory.", applications: ["Hop beverages", "Weight management", "Craft flavors"] },
  { id: "terp-008", name: "Ocimene", aroma: "Sweet, tropical, woody", effect: "Energy", description: "Found in mint, orchids, mangoes. Antiviral and decongestant.", applications: ["Tropical beverages", "Fragrance", "Exotic flavors"] },
  { id: "terp-009", name: "Bisabolol", aroma: "Light floral, chamomile", effect: "Calm", description: "Derived from chamomile. Anti-irritant and antimicrobial.", applications: ["Skincare", "Calming teas", "Nighttime blends"] },
  { id: "terp-010", name: "Geraniol", aroma: "Rose, geranium", effect: "Focus", description: "Found in rose oil and lemongrass. Natural insect repellent, neuroprotective.", applications: ["Floral beverages", "Insect repellents", "Fragrance"] },
];

const EFFECTS = ["All", "Relaxation", "Energy", "Calm", "Relief", "Focus"];

const EFFECT_COLORS: Record<string, string> = {
  Relaxation: "#7C5CBF",
  Energy: "#E8AA42",
  Calm: "#5BA3CF",
  Relief: "#D96B5B",
  Focus: "#0B6E4F",
};

// ─── Component ───────────────────────────────────────────────────
const TerpeneProfileExplorer: React.FC<Props> = ({
  accentColor = "#0B6E4F",
}) => {
  const [activeFilter, setActiveFilter] = useState("All");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (activeFilter === "All") return MOCK_TERPENES;
    return MOCK_TERPENES.filter((t) => t.effect === activeFilter);
  }, [activeFilter]);

  const container: CSSProperties = {
    width: "100%",
    padding: "64px 24px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: "#F8FAF9",
  };

  const heading: CSSProperties = {
    fontSize: 36,
    fontWeight: 700,
    color: "#0F1F17",
    textAlign: "center",
    margin: "0 0 8px",
    letterSpacing: "-0.02em",
  };

  const subtitle: CSSProperties = {
    fontSize: 16,
    color: "#4A6358",
    textAlign: "center",
    margin: "0 0 32px",
  };

  const filterBar: CSSProperties = {
    display: "flex",
    justifyContent: "center",
    gap: 8,
    flexWrap: "wrap",
    marginBottom: 40,
  };

  const filterBtn = (active: boolean): CSSProperties => ({
    padding: "8px 20px",
    fontSize: 14,
    fontWeight: 500,
    border: "none",
    borderRadius: 9999,
    cursor: "pointer",
    background: active ? accentColor : "#E2E8E5",
    color: active ? "#fff" : "#4A6358",
    transition: "all 0.2s ease",
  });

  const grid: CSSProperties = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
    gap: 20,
    maxWidth: 1080,
    margin: "0 auto",
  };

  const card = (isExpanded: boolean): CSSProperties => ({
    background: "#FFFFFF",
    borderRadius: 12,
    padding: 24,
    border: "1px solid #E2E8E5",
    cursor: "pointer",
    transition: "box-shadow 0.2s ease, transform 0.2s ease",
    boxShadow: isExpanded
      ? "0 12px 32px rgba(15, 31, 23, 0.12)"
      : "0 1px 2px rgba(15, 31, 23, 0.06)",
    transform: isExpanded ? "translateY(-2px)" : "none",
  });

  const effectBadge = (effect: string): CSSProperties => ({
    display: "inline-block",
    padding: "4px 12px",
    fontSize: 12,
    fontWeight: 600,
    borderRadius: 9999,
    background: `${EFFECT_COLORS[effect] || accentColor}18`,
    color: EFFECT_COLORS[effect] || accentColor,
    marginBottom: 12,
  });

  return (
    <div style={container}>
      <h2 style={heading}>Terpene Profile Explorer</h2>
      <p style={subtitle}>
        Browse our library of botanical terpene compounds. Filter by effect
        category.
      </p>

      <div style={filterBar}>
        {EFFECTS.map((e) => (
          <button
            key={e}
            style={filterBtn(activeFilter === e)}
            onClick={() => setActiveFilter(e)}
          >
            {e}
          </button>
        ))}
      </div>

      <div style={grid}>
        {filtered.map((t) => {
          const isExpanded = expandedId === t.id;
          return (
            <div
              key={t.id}
              style={card(isExpanded)}
              onClick={() => setExpandedId(isExpanded ? null : t.id)}
            >
              <span style={effectBadge(t.effect)}>{t.effect}</span>
              <h3
                style={{
                  fontSize: 20,
                  fontWeight: 600,
                  color: "#0F1F17",
                  margin: "0 0 4px",
                }}
              >
                {t.name}
              </h3>
              <p
                style={{
                  fontSize: 14,
                  color: "#8A9E94",
                  margin: "0 0 12px",
                  fontStyle: "italic",
                }}
              >
                {t.aroma}
              </p>
              <p
                style={{
                  fontSize: 14,
                  color: "#4A6358",
                  lineHeight: 1.6,
                  margin: 0,
                }}
              >
                {t.description}
              </p>

              {isExpanded && (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #E2E8E5" }}>
                  <p
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: "#8A9E94",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      margin: "0 0 8px",
                    }}
                  >
                    Applications
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {t.applications.map((app) => (
                      <span
                        key={app}
                        style={{
                          fontSize: 13,
                          padding: "4px 12px",
                          borderRadius: 6,
                          background: "rgba(11, 110, 79, 0.06)",
                          color: "#0B6E4F",
                        }}
                      >
                        {app}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── Framer Property Controls ────────────────────────────────────
if (typeof window !== "undefined" && (window as any).Framer) {
  const { addPropertyControls, ControlType } = require("framer");
  addPropertyControls(TerpeneProfileExplorer, {
    apiUrl: { type: ControlType.String, title: "API URL", defaultValue: "/api/terpenes" },
    accentColor: { type: ControlType.Color, title: "Accent Color", defaultValue: "#0B6E4F" },
  });
}

export default TerpeneProfileExplorer;
