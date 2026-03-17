/** Nexus Agriscience — Design Tokens (Dark Biotech Theme) */

export const colors = {
  /** Primary — deep navy from real brand */
  primary: "#153872",
  primaryLight: "#1E4D99",
  primaryMuted: "rgba(21, 56, 114, 0.15)",

  /** Accent — coral/red from real brand */
  accent: "#FF462E",
  accentHover: "#E63B25",
  accentMuted: "rgba(255, 70, 46, 0.12)",

  /** Dark backgrounds */
  bgDark: "#0A0F1C",
  bgCard: "#111827",
  bgCardHover: "#1A2236",
  bgSurface: "#0E1525",

  /** Light text on dark */
  white: "#FFFFFF",
  textPrimary: "#F1F5F9",
  textSecondary: "#94A3B8",
  textMuted: "#64748B",

  /** Borders */
  border: "rgba(255, 255, 255, 0.08)",
  borderHover: "rgba(255, 255, 255, 0.15)",

  /** Semantic */
  success: "#10B981",
  error: "#EF4444",

  /** Gradient stops */
  gradientStart: "#0A0F1C",
  gradientMid: "#153872",
  gradientEnd: "#1E4D99",

  /** Terpene class colors */
  terpMono: "#3B82F6",
  terpSesqui: "#8B5CF6",
  terpDi: "#06B6D4",
} as const;

export const fonts = {
  heading: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  body: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
} as const;

export const radii = {
  sm: 6,
  md: 12,
  lg: 20,
  xl: 24,
  full: 9999,
} as const;

export const shadows = {
  sm: "0 1px 3px rgba(0, 0, 0, 0.3)",
  md: "0 4px 16px rgba(0, 0, 0, 0.4)",
  lg: "0 12px 40px rgba(0, 0, 0, 0.5)",
  glow: "0 0 40px rgba(21, 56, 114, 0.3)",
  accentGlow: "0 0 30px rgba(255, 70, 46, 0.25)",
} as const;
