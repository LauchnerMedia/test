/** Nexus Agriscience — Design Tokens */

export const colors = {
  /** Primary brand green — biotech / agriculture */
  primary: "#0B6E4F",
  primaryLight: "#14A76C",
  primaryMuted: "rgba(11, 110, 79, 0.08)",

  /** Accent — warm amber for CTAs */
  accent: "#E8AA42",
  accentHover: "#D4962E",

  /** Neutrals */
  white: "#FFFFFF",
  bg: "#F8FAF9",
  bgCard: "#FFFFFF",
  border: "#E2E8E5",
  textPrimary: "#0F1F17",
  textSecondary: "#4A6358",
  textMuted: "#8A9E94",

  /** Semantic */
  success: "#14A76C",
  error: "#D94F4F",

  /** Gradient stops */
  gradientStart: "#0B6E4F",
  gradientMid: "#0E8960",
  gradientEnd: "#14A76C",
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
  full: 9999,
} as const;

export const shadows = {
  sm: "0 1px 2px rgba(15, 31, 23, 0.06)",
  md: "0 4px 12px rgba(15, 31, 23, 0.08)",
  lg: "0 12px 32px rgba(15, 31, 23, 0.12)",
} as const;
