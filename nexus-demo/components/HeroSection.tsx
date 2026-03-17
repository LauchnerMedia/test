import React, { CSSProperties } from "react";

// ─── Framer Property Controls ────────────────────────────────────
// @framerSupportedLayoutWidth any
// @framerSupportedLayoutHeight any
interface Props {
  headline?: string;
  subheadline?: string;
  ctaLabel?: string;
  ctaUrl?: string;
  gradientFrom?: string;
  gradientTo?: string;
}

const defaultProps: Required<Props> = {
  headline: "Nature's Complexity,\nPrecision Delivered.",
  subheadline:
    "Nexus Agriscience engineers terpene-based ingredient systems for beverages, cannabis, flavor, and wellness brands.",
  ctaLabel: "Request a Sample",
  ctaUrl: "#sample-request",
  gradientFrom: "#0B6E4F",
  gradientTo: "#14A76C",
};

const HeroSection: React.FC<Props> = (rawProps) => {
  const props = { ...defaultProps, ...rawProps };

  const containerStyle: CSSProperties = {
    position: "relative",
    width: "100%",
    minHeight: 600,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "80px 24px",
    background: `linear-gradient(135deg, ${props.gradientFrom} 0%, ${props.gradientTo} 60%, #0B6E4F 100%)`,
    overflow: "hidden",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  };

  const orbStyle = (
    size: number,
    top: string,
    left: string,
    delay: string
  ): CSSProperties => ({
    position: "absolute",
    width: size,
    height: size,
    borderRadius: "50%",
    background: "rgba(255,255,255,0.06)",
    top,
    left,
    animation: `nexusFloat 8s ease-in-out ${delay} infinite alternate`,
    pointerEvents: "none",
  });

  const headlineStyle: CSSProperties = {
    fontSize: 56,
    fontWeight: 700,
    color: "#FFFFFF",
    textAlign: "center",
    lineHeight: 1.1,
    margin: 0,
    maxWidth: 720,
    whiteSpace: "pre-line",
    letterSpacing: "-0.02em",
  };

  const subStyle: CSSProperties = {
    fontSize: 20,
    fontWeight: 400,
    color: "rgba(255,255,255,0.82)",
    textAlign: "center",
    lineHeight: 1.6,
    margin: "24px 0 40px",
    maxWidth: 560,
  };

  const ctaStyle: CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "16px 36px",
    fontSize: 16,
    fontWeight: 600,
    color: "#0F1F17",
    background: "#E8AA42",
    border: "none",
    borderRadius: 9999,
    cursor: "pointer",
    textDecoration: "none",
    transition: "background 0.2s ease, transform 0.2s ease",
    boxShadow: "0 4px 16px rgba(232, 170, 66, 0.3)",
  };

  return (
    <div style={containerStyle}>
      {/* Keyframes injected once */}
      <style>{`
        @keyframes nexusFloat {
          0%   { transform: translateY(0) scale(1); }
          100% { transform: translateY(-30px) scale(1.08); }
        }
      `}</style>

      {/* Animated background orbs */}
      <div style={orbStyle(320, "-5%", "70%", "0s")} />
      <div style={orbStyle(200, "60%", "-5%", "2s")} />
      <div style={orbStyle(160, "40%", "80%", "4s")} />

      <h1 style={headlineStyle}>{props.headline}</h1>
      <p style={subStyle}>{props.subheadline}</p>
      <a
        href={props.ctaUrl}
        style={ctaStyle}
        onMouseEnter={(e) => {
          (e.target as HTMLElement).style.background = "#D4962E";
          (e.target as HTMLElement).style.transform = "translateY(-2px)";
        }}
        onMouseLeave={(e) => {
          (e.target as HTMLElement).style.background = "#E8AA42";
          (e.target as HTMLElement).style.transform = "translateY(0)";
        }}
      >
        {props.ctaLabel}
      </a>
    </div>
  );
};

// ─── Framer Property Controls ────────────────────────────────────
if (typeof window !== "undefined" && (window as any).Framer) {
  const { addPropertyControls, ControlType } = require("framer");
  addPropertyControls(HeroSection, {
    headline: { type: ControlType.String, title: "Headline", defaultValue: defaultProps.headline },
    subheadline: { type: ControlType.String, title: "Subheadline", defaultValue: defaultProps.subheadline },
    ctaLabel: { type: ControlType.String, title: "CTA Label", defaultValue: defaultProps.ctaLabel },
    ctaUrl: { type: ControlType.String, title: "CTA URL", defaultValue: defaultProps.ctaUrl },
    gradientFrom: { type: ControlType.Color, title: "Gradient Start", defaultValue: defaultProps.gradientFrom },
    gradientTo: { type: ControlType.Color, title: "Gradient End", defaultValue: defaultProps.gradientTo },
  });
}

export default HeroSection;
