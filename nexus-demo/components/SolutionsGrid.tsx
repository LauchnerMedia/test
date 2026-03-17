import React, { CSSProperties, useState } from "react";

// ─── Types ───────────────────────────────────────────────────────
interface Solution {
  id: string;
  title: string;
  description: string;
  industries: string[];
}

interface Props {
  sectionTitle?: string;
  sectionSubtitle?: string;
  accentColor?: string;
}

// ─── Icons (inline SVG paths) ────────────────────────────────────
const ICONS: Record<string, string> = {
  "Beverage Formulation":
    "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93z",
  "Cannabis Terpene Innovation":
    "M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66L7 18h2l1 3h2v-5l4-4 3 1 1-3c-3-1-4-2-3-9z",
  "Flavor Systems":
    "M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z",
  "Ingredient R&D":
    "M19.8 18.4L14 10.67V6.5l1.35-1.69c.26-.33.03-.81-.39-.81H9.04c-.42 0-.65.48-.39.81L10 6.5v4.17L4.2 18.4c-.49.66-.02 1.6.8 1.6h14.2c.82 0 1.29-.94.8-1.6z",
};

// ─── Mock Data ───────────────────────────────────────────────────
const SOLUTIONS: Solution[] = [
  {
    id: "sol-001",
    title: "Beverage Formulation",
    description:
      "Water-soluble terpene blends engineered for functional beverages. Nano-emulsion tech ensures stable dispersion and rapid bioavailability.",
    industries: ["Functional beverages", "Craft brewing", "RTD cocktails", "Wellness drinks"],
  },
  {
    id: "sol-002",
    title: "Cannabis Terpene Innovation",
    description:
      "Strain-specific and effect-targeted terpene profiles for vape, edibles, and concentrates. 300+ botanical formulations available.",
    industries: ["Cannabis processors", "Vape manufacturers", "Edible brands", "White-label"],
  },
  {
    id: "sol-003",
    title: "Flavor Systems",
    description:
      "Natural terpene-derived flavor compounds. Replace synthetic flavoring with clean-label, plant-derived alternatives.",
    industries: ["Food manufacturing", "Confectionery", "Snack production", "Flavor houses"],
  },
  {
    id: "sol-004",
    title: "Ingredient R&D",
    description:
      "Custom terpene isolation, characterization, and formulation services from proof-of-concept through scale-up.",
    industries: ["Pharmaceutical", "Nutraceutical", "Cosmetics", "Agricultural biotech"],
  },
];

// ─── Component ───────────────────────────────────────────────────
const SolutionsGrid: React.FC<Props> = ({
  sectionTitle = "Solutions",
  sectionSubtitle = "Terpene science applied across industries",
  accentColor = "#0B6E4F",
}) => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const container: CSSProperties = {
    width: "100%",
    padding: "72px 24px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: "#FFFFFF",
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
    margin: "0 0 48px",
  };

  const grid: CSSProperties = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: 24,
    maxWidth: 1080,
    margin: "0 auto",
  };

  const card = (isHovered: boolean): CSSProperties => ({
    background: "#F8FAF9",
    borderRadius: 16,
    padding: 32,
    border: `1px solid ${isHovered ? accentColor : "#E2E8E5"}`,
    transition: "all 0.25s ease",
    boxShadow: isHovered
      ? "0 12px 32px rgba(15, 31, 23, 0.1)"
      : "0 1px 2px rgba(15, 31, 23, 0.04)",
    transform: isHovered ? "translateY(-4px)" : "none",
    cursor: "default",
  });

  const iconContainer = (isHovered: boolean): CSSProperties => ({
    width: 48,
    height: 48,
    borderRadius: 12,
    background: isHovered ? accentColor : "rgba(11, 110, 79, 0.08)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
    transition: "background 0.25s ease",
  });

  return (
    <div style={container}>
      <h2 style={heading}>{sectionTitle}</h2>
      <p style={subtitle}>{sectionSubtitle}</p>

      <div style={grid}>
        {SOLUTIONS.map((sol) => {
          const isHovered = hoveredId === sol.id;
          return (
            <div
              key={sol.id}
              style={card(isHovered)}
              onMouseEnter={() => setHoveredId(sol.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <div style={iconContainer(isHovered)}>
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill={isHovered ? "#fff" : accentColor}
                >
                  <path d={ICONS[sol.title] || ICONS["Ingredient R&D"]} />
                </svg>
              </div>

              <h3
                style={{
                  fontSize: 20,
                  fontWeight: 600,
                  color: "#0F1F17",
                  margin: "0 0 8px",
                }}
              >
                {sol.title}
              </h3>

              <p
                style={{
                  fontSize: 14,
                  color: "#4A6358",
                  lineHeight: 1.65,
                  margin: "0 0 20px",
                }}
              >
                {sol.description}
              </p>

              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {sol.industries.map((ind) => (
                  <span
                    key={ind}
                    style={{
                      fontSize: 12,
                      padding: "3px 10px",
                      borderRadius: 6,
                      background: "rgba(11, 110, 79, 0.06)",
                      color: "#0B6E4F",
                      fontWeight: 500,
                    }}
                  >
                    {ind}
                  </span>
                ))}
              </div>
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
  addPropertyControls(SolutionsGrid, {
    sectionTitle: { type: ControlType.String, title: "Title", defaultValue: "Solutions" },
    sectionSubtitle: { type: ControlType.String, title: "Subtitle", defaultValue: "Terpene science applied across industries" },
    accentColor: { type: ControlType.Color, title: "Accent Color", defaultValue: "#0B6E4F" },
  });
}

export default SolutionsGrid;
