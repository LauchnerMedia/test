import React, { CSSProperties, useState } from "react";

interface Market {
  id: string;
  title: string;
  description: string;
  applications: string[];
  color: string;
  icon: React.ReactNode;
}

const MARKETS: Market[] = [
  {
    id: "beverage",
    title: "Functional Beverages",
    description: "Natural terpene-derived flavor and functional compounds for next-generation beverages. From sparkling waters to adaptogenic drinks.",
    applications: ["Flavor systems", "Functional actives", "Clean-label ingredients", "Nano-emulsions"],
    color: "#3B82F6",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 2h8l-1 14H9L8 2z" />
        <path d="M6 18h12" />
        <path d="M9 22h6" />
        <path d="M6 18l-1-2h14l-1 2" />
      </svg>
    ),
  },
  {
    id: "flavor",
    title: "Flavor & Fragrance",
    description: "Plant-derived alternatives to petroleum-based synthetic flavor and fragrance compounds. Clean-label, sustainable, and scalable.",
    applications: ["Aroma engineering", "Fragrance blending", "Natural flavor replacement", "Scent profiles"],
    color: "#8B5CF6",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
        <path d="M12 6v6l4 2" />
      </svg>
    ),
  },
  {
    id: "cannabis",
    title: "Cannabis CPG",
    description: "The world's largest producer of cannabis essential oils. Strain-specific and effect-targeted terpene profiles through our Terpene Belt Farms subsidiary.",
    applications: ["Cannabis essential oils", "Strain-specific profiles", "Fresh Never Frozen\u00AE", "Wholesale terpenes"],
    color: "#10B981",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22V2" />
        <path d="M12 8c-3 0-6 2-6 6" />
        <path d="M12 8c3 0 6 2 6 6" />
        <path d="M12 4c-2 0-4 1.5-4 4" />
        <path d="M12 4c2 0 4 1.5 4 4" />
        <path d="M8 18c1.5 0 3-.5 4-2" />
        <path d="M16 18c-1.5 0-3-.5-4-2" />
      </svg>
    ),
  },
  {
    id: "pharma",
    title: "Pharmaceutical",
    description: "High-purity terpene isolates and novel plant-derived compounds for pharmaceutical R&D and drug delivery systems.",
    applications: ["Active compound isolation", "Transdermal delivery", "Anti-inflammatory actives", "Preclinical research"],
    color: "#06B6D4",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19.5 12.572l-7.5 7.428l-7.5-7.428A5 5 0 1112 6.006a5 5 0 017.5 6.572" />
      </svg>
    ),
  },
  {
    id: "specialty",
    title: "Specialty Ingredients",
    description: "Custom terpene isolation and formulation services for nutraceutical, cosmetics, and wellness brands seeking natural alternatives.",
    applications: ["Nutraceutical actives", "Cosmetic ingredients", "Wellness compounds", "Custom formulation"],
    color: "#F59E0B",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l.548 2.192a.64.64 0 01-.311.72h-7.546a.64.64 0 01-.311-.72L9.464 16.542z" />
      </svg>
    ),
  },
  {
    id: "commodity",
    title: "Commodity Chemicals",
    description: "Hemp as a lower-carbon feedstock to replace petroleum-derived synthetic additives used in food and consumer products at industrial scale.",
    applications: ["Petrochemical replacement", "Industrial terpenes", "Bio-based solvents", "Green chemistry"],
    color: "#EF4444",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
        <path d="M3.27 6.96L12 12.01l8.73-5.05" />
        <path d="M12 22.08V12" />
      </svg>
    ),
  },
];

const MarketsSection: React.FC = () => {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const container: CSSProperties = {
    width: "100%",
    padding: "120px 40px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: "#0A0F1C",
  };

  return (
    <div style={container}>
      <div style={{ textAlign: "center", maxWidth: 700, margin: "0 auto 72px" }}>
        <p style={{
          fontSize: 13, fontWeight: 600, color: "#FF462E",
          textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16,
        }}>
          Target Markets
        </p>
        <h2 style={{
          fontSize: 48, fontWeight: 800, color: "#F1F5F9",
          margin: "0 0 20px", letterSpacing: "-0.03em", lineHeight: 1.1,
        }}>
          Natural Ingredients for{"\n"}Every Industry
        </h2>
        <p style={{
          fontSize: 18, color: "#94A3B8", lineHeight: 1.65, margin: 0,
        }}>
          From functional beverages to commodity chemicals, our platform serves the full spectrum of natural ingredient markets.
        </p>
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, 1fr)",
        gap: 24,
        maxWidth: 1200,
        margin: "0 auto",
      }}>
        {MARKETS.map((market) => {
          const isHovered = hoveredId === market.id;
          return (
            <div
              key={market.id}
              style={{
                padding: 36,
                borderRadius: 20,
                background: isHovered ? "rgba(255, 255, 255, 0.04)" : "rgba(255, 255, 255, 0.02)",
                border: `1px solid ${isHovered ? `${market.color}40` : "rgba(255, 255, 255, 0.06)"}`,
                transition: "all 0.3s ease",
                cursor: "default",
                transform: isHovered ? "translateY(-4px)" : "none",
                boxShadow: isHovered ? `0 20px 40px rgba(0,0,0,0.3), 0 0 40px ${market.color}10` : "none",
              }}
              onMouseEnter={() => setHoveredId(market.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <div style={{
                width: 52, height: 52, borderRadius: 14,
                background: isHovered ? `${market.color}20` : "rgba(255, 255, 255, 0.05)",
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: 24, transition: "all 0.3s ease",
                color: isHovered ? market.color : "#64748B",
              }}>
                {market.icon}
              </div>

              <h3 style={{
                fontSize: 20, fontWeight: 700, color: "#F1F5F9",
                margin: "0 0 12px",
              }}>
                {market.title}
              </h3>

              <p style={{
                fontSize: 14, color: "#94A3B8", lineHeight: 1.65,
                margin: "0 0 24px",
              }}>
                {market.description}
              </p>

              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {market.applications.map((app) => (
                  <span
                    key={app}
                    style={{
                      fontSize: 12, padding: "5px 12px", borderRadius: 8,
                      background: `${market.color}10`,
                      color: `${market.color}`,
                      fontWeight: 500,
                      border: `1px solid ${market.color}20`,
                    }}
                  >
                    {app}
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

export default MarketsSection;
