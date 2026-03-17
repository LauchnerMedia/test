import React, { CSSProperties } from "react";

interface NewsItem {
  id: string;
  date: string;
  source: string;
  title: string;
  summary: string;
  tag: string;
  tagColor: string;
}

const NEWS: NewsItem[] = [
  {
    id: "news-001",
    date: "February 2026",
    source: "PR Newswire",
    title: "Terpene Belt Farms Selected for UCLA-Led, State-Funded Cannabis Research Grant",
    summary: "Nexus subsidiary joins a $1.23M UCLA-led coalition to establish California's first Flower Flavor-Compound Reference Dataset (FRD), creating scientifically validated terpene concentration baselines for regulators.",
    tag: "Research",
    tagColor: "#3B82F6",
  },
  {
    id: "news-002",
    date: "January 2026",
    source: "PR Newswire",
    title: "Nexus Agriscience Acquires Biotech Institute IP Portfolio",
    summary: "Acquisition of Biotech Institute's hemp division expands molecular farming platform with patented genetics, proprietary germplasm, and key scientific talent — positioning Nexus for a $37B addressable market.",
    tag: "Acquisition",
    tagColor: "#8B5CF6",
  },
  {
    id: "news-003",
    date: "February 2026",
    source: "Authority Magazine",
    title: "AgTech: Shareef El-Sissi on Technologies Revolutionizing Agriculture",
    summary: "CEO Shareef El-Sissi discusses Nexus's vision of supplanting petroleum-based synthetics with plant-derived alternatives, and how hemp's molecular farming potential is reshaping the global ingredient supply chain.",
    tag: "Leadership",
    tagColor: "#10B981",
  },
];

const LEADERSHIP = [
  {
    name: "Shareef El-Sissi",
    title: "Chief Executive Officer",
    bio: "Bay Area native with 15+ years of cannabis and biotech leadership. Co-founder of Treez, former CEO of Eden Enterprises. Founded Terpene Belt Farms in 2019, now leading Nexus Agriscience's expansion into global ingredient markets.",
  },
  {
    name: "Pamela Epstein",
    title: "Chief Legal & Regulatory Officer",
    bio: "Guides regulatory strategy across cannabis, hemp, and natural ingredient markets, ensuring compliance as Nexus scales into new verticals and geographies.",
  },
  {
    name: "Dr. Mark Lewis",
    title: "Chief Genetic Architect",
    bio: "Key inventor of the Biotech Institute patent portfolio. Leads genetic development of hemp cultivars engineered for predictable high-value terpene expression at commercial scale.",
  },
];

const NewsSection: React.FC = () => {
  const container: CSSProperties = {
    width: "100%",
    padding: "120px 40px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: "#0E1525",
  };

  return (
    <div style={container}>
      {/* News */}
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ textAlign: "center", maxWidth: 700, margin: "0 auto 72px" }}>
          <p style={{
            fontSize: 13, fontWeight: 600, color: "#FF462E",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16,
          }}>
            Latest News
          </p>
          <h2 style={{
            fontSize: 48, fontWeight: 800, color: "#F1F5F9",
            margin: "0 0 20px", letterSpacing: "-0.03em", lineHeight: 1.1,
          }}>
            Advancing the Science
          </h2>
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 24,
          marginBottom: 120,
        }}>
          {NEWS.map((item) => (
            <div
              key={item.id}
              style={{
                padding: 32,
                borderRadius: 20,
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
                transition: "all 0.3s ease",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                <span style={{
                  fontSize: 12, fontWeight: 600, padding: "4px 12px",
                  borderRadius: 8, background: `${item.tagColor}15`,
                  color: item.tagColor, border: `1px solid ${item.tagColor}25`,
                }}>
                  {item.tag}
                </span>
                <span style={{ fontSize: 12, color: "#64748B" }}>{item.date}</span>
              </div>

              <h3 style={{
                fontSize: 18, fontWeight: 700, color: "#F1F5F9",
                margin: "0 0 12px", lineHeight: 1.4,
              }}>
                {item.title}
              </h3>

              <p style={{
                fontSize: 14, color: "#94A3B8", lineHeight: 1.65,
                margin: "0 0 20px", flex: 1,
              }}>
                {item.summary}
              </p>

              <p style={{ fontSize: 12, color: "#64748B", margin: 0 }}>
                Source: {item.source}
              </p>
            </div>
          ))}
        </div>

        {/* Leadership */}
        <div style={{ textAlign: "center", maxWidth: 700, margin: "0 auto 72px" }}>
          <p style={{
            fontSize: 13, fontWeight: 600, color: "#FF462E",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16,
          }}>
            Leadership
          </p>
          <h2 style={{
            fontSize: 48, fontWeight: 800, color: "#F1F5F9",
            margin: "0 0 20px", letterSpacing: "-0.03em", lineHeight: 1.1,
          }}>
            Built by Operators
          </h2>
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 24,
        }}>
          {LEADERSHIP.map((person) => (
            <div
              key={person.name}
              style={{
                padding: 36,
                borderRadius: 20,
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 255, 255, 0.06)",
              }}
            >
              {/* Avatar placeholder */}
              <div style={{
                width: 64, height: 64, borderRadius: 16,
                background: "linear-gradient(135deg, rgba(21, 56, 114, 0.3), rgba(30, 77, 153, 0.15))",
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: 24, fontSize: 24, fontWeight: 700, color: "#64748B",
              }}>
                {person.name.split(" ").map(n => n[0]).join("")}
              </div>

              <h3 style={{
                fontSize: 20, fontWeight: 700, color: "#F1F5F9",
                margin: "0 0 4px",
              }}>
                {person.name}
              </h3>

              <p style={{
                fontSize: 14, fontWeight: 500, color: "#FF462E",
                margin: "0 0 16px",
              }}>
                {person.title}
              </p>

              <p style={{
                fontSize: 14, color: "#94A3B8", lineHeight: 1.65, margin: 0,
              }}>
                {person.bio}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NewsSection;
