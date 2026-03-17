import React, { CSSProperties } from "react";

// @framerSupportedLayoutWidth any
// @framerSupportedLayoutHeight any
interface Props {
  headline?: string;
  subheadline?: string;
  ctaLabel?: string;
  ctaUrl?: string;
  stat1Value?: string;
  stat1Label?: string;
  stat2Value?: string;
  stat2Label?: string;
  stat3Value?: string;
  stat3Label?: string;
}

const defaultProps: Required<Props> = {
  headline: "Supplanting Petroleum\nSynthetics With Nature.",
  subheadline:
    "Nexus Agriscience's molecular farming platform uses hemp as a biosynthesis engine to produce natural ingredients at commercial scale — a capital-efficient alternative to precision fermentation.",
  ctaLabel: "Partner With Us",
  ctaUrl: "#contact",
  stat1Value: "$37B",
  stat1Label: "Addressable Market",
  stat2Value: "240+",
  stat2Label: "Acres in Production",
  stat3Value: "100%",
  stat3Label: "Non-Cannabinoid",
};

const HeroSection: React.FC<Props> = (rawProps) => {
  const props = { ...defaultProps, ...rawProps };

  const containerStyle: CSSProperties = {
    position: "relative",
    width: "100%",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "120px 40px 80px",
    background: "#0A0F1C",
    overflow: "hidden",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  };

  return (
    <div style={containerStyle}>
      <style>{`
        @keyframes nexusPulse {
          0%, 100% { opacity: 0.15; transform: scale(1); }
          50% { opacity: 0.25; transform: scale(1.05); }
        }
        @keyframes nexusFloat {
          0% { transform: translateY(0) rotate(0deg); }
          100% { transform: translateY(-20px) rotate(3deg); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes gridMove {
          0% { transform: perspective(1000px) rotateX(60deg) translateY(0); }
          100% { transform: perspective(1000px) rotateX(60deg) translateY(-50px); }
        }
      `}</style>

      {/* Gradient orbs background */}
      <div style={{
        position: "absolute", width: 600, height: 600, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(21, 56, 114, 0.4), transparent 70%)",
        top: "-10%", right: "-5%", animation: "nexusPulse 6s ease-in-out infinite",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", width: 500, height: 500, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(255, 70, 46, 0.12), transparent 70%)",
        bottom: "5%", left: "-5%", animation: "nexusPulse 8s ease-in-out 2s infinite",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", width: 300, height: 300, borderRadius: "50%",
        background: "radial-gradient(circle, rgba(30, 77, 153, 0.25), transparent 70%)",
        top: "40%", left: "50%", animation: "nexusPulse 7s ease-in-out 1s infinite",
        pointerEvents: "none",
      }} />

      {/* Grid pattern overlay */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
        backgroundSize: "80px 80px",
        pointerEvents: "none",
      }} />

      {/* Tag line */}
      <div style={{
        display: "inline-flex", alignItems: "center", gap: 8,
        padding: "8px 20px", borderRadius: 9999,
        background: "rgba(21, 56, 114, 0.2)",
        border: "1px solid rgba(21, 56, 114, 0.3)",
        marginBottom: 32,
        animation: "fadeInUp 0.8s ease-out",
      }}>
        <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#10B981" }} />
        <span style={{ fontSize: 13, fontWeight: 500, color: "#94A3B8", letterSpacing: "0.02em" }}>
          Molecular Farming Platform
        </span>
      </div>

      <h1 style={{
        fontSize: 72, fontWeight: 800, color: "#F1F5F9", textAlign: "center",
        lineHeight: 1.05, margin: 0, maxWidth: 900, whiteSpace: "pre-line",
        letterSpacing: "-0.03em",
        animation: "fadeInUp 0.8s ease-out 0.1s both",
      }}>
        {props.headline}
      </h1>

      <p style={{
        fontSize: 20, fontWeight: 400, color: "#94A3B8", textAlign: "center",
        lineHeight: 1.65, margin: "28px 0 44px", maxWidth: 640,
        animation: "fadeInUp 0.8s ease-out 0.2s both",
      }}>
        {props.subheadline}
      </p>

      <div style={{
        display: "flex", gap: 16, alignItems: "center",
        animation: "fadeInUp 0.8s ease-out 0.3s both",
      }}>
        <a
          href={props.ctaUrl}
          style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            padding: "16px 36px", fontSize: 16, fontWeight: 600, color: "#fff",
            background: "#FF462E", border: "none", borderRadius: 12,
            cursor: "pointer", textDecoration: "none",
            transition: "all 0.2s ease",
            boxShadow: "0 0 30px rgba(255, 70, 46, 0.3)",
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLElement).style.background = "#E63B25";
            (e.target as HTMLElement).style.transform = "translateY(-2px)";
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLElement).style.background = "#FF462E";
            (e.target as HTMLElement).style.transform = "translateY(0)";
          }}
        >
          {props.ctaLabel}
        </a>
        <a
          href="#platform"
          style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            padding: "16px 36px", fontSize: 16, fontWeight: 600, color: "#F1F5F9",
            background: "transparent",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            borderRadius: 12, cursor: "pointer", textDecoration: "none",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLElement).style.background = "rgba(255, 255, 255, 0.05)";
            (e.target as HTMLElement).style.borderColor = "rgba(255, 255, 255, 0.25)";
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLElement).style.background = "transparent";
            (e.target as HTMLElement).style.borderColor = "rgba(255, 255, 255, 0.15)";
          }}
        >
          Explore Platform
        </a>
      </div>

      {/* Stats row */}
      <div style={{
        display: "flex", gap: 64, marginTop: 80,
        animation: "fadeInUp 0.8s ease-out 0.5s both",
      }}>
        {[
          { value: props.stat1Value, label: props.stat1Label },
          { value: props.stat2Value, label: props.stat2Label },
          { value: props.stat3Value, label: props.stat3Label },
        ].map((stat, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div style={{
              fontSize: 40, fontWeight: 800, color: "#F1F5F9",
              letterSpacing: "-0.02em", lineHeight: 1,
            }}>
              {stat.value}
            </div>
            <div style={{
              fontSize: 13, fontWeight: 500, color: "#64748B",
              marginTop: 8, textTransform: "uppercase", letterSpacing: "0.06em",
            }}>
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

if (typeof window !== "undefined" && (window as any).Framer) {
  const { addPropertyControls, ControlType } = require("framer");
  addPropertyControls(HeroSection, {
    headline: { type: ControlType.String, title: "Headline", defaultValue: defaultProps.headline },
    subheadline: { type: ControlType.String, title: "Subheadline", defaultValue: defaultProps.subheadline },
    ctaLabel: { type: ControlType.String, title: "CTA Label", defaultValue: defaultProps.ctaLabel },
    ctaUrl: { type: ControlType.String, title: "CTA URL", defaultValue: defaultProps.ctaUrl },
  });
}

export default HeroSection;
