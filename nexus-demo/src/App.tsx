import React from "react";
import HeroSection from "../components/HeroSection";
import TerpeneProfileExplorer from "../components/TerpeneProfileExplorer";
import SolutionsGrid from "../components/SolutionsGrid";
import FormulationWizard from "../components/FormulationWizard";
import SampleRequestForm from "../components/SampleRequestForm";

const Nav: React.FC = () => (
  <nav
    style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      zIndex: 100,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "14px 32px",
      background: "rgba(248, 250, 249, 0.85)",
      backdropFilter: "blur(12px)",
      borderBottom: "1px solid rgba(226, 232, 229, 0.6)",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: "linear-gradient(135deg, #0B6E4F, #14A76C)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>
      <span style={{ fontSize: 17, fontWeight: 700, color: "#0F1F17", letterSpacing: "-0.02em" }}>
        Nexus Agriscience
      </span>
    </div>

    <div style={{ display: "flex", gap: 28 }}>
      {[
        { label: "Terpenes", href: "#terpenes" },
        { label: "Solutions", href: "#solutions" },
        { label: "Wizard", href: "#wizard" },
        { label: "Contact", href: "#contact" },
      ].map((link) => (
        <a
          key={link.href}
          href={link.href}
          style={{
            fontSize: 14,
            fontWeight: 500,
            color: "#4A6358",
            textDecoration: "none",
            transition: "color 0.2s",
          }}
          onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "#0B6E4F")}
          onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "#4A6358")}
        >
          {link.label}
        </a>
      ))}
    </div>
  </nav>
);

const Divider: React.FC = () => (
  <div
    style={{
      maxWidth: 1080,
      margin: "0 auto",
      padding: "0 24px",
    }}
  >
    <div style={{ height: 1, background: "#E2E8E5" }} />
  </div>
);

const Footer: React.FC = () => (
  <footer
    style={{
      padding: "48px 24px",
      textAlign: "center",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      borderTop: "1px solid #E2E8E5",
    }}
  >
    <p style={{ fontSize: 14, color: "#8A9E94", margin: 0 }}>
      Nexus Agriscience — Terpene Science, Precision Delivered.
    </p>
    <p style={{ fontSize: 12, color: "#BCC8C2", margin: "8px 0 0" }}>
      Demo prototype. Data is illustrative.
    </p>
  </footer>
);

export default function App() {
  return (
    <div>
      <Nav />

      <section id="hero">
        <HeroSection />
      </section>

      <section id="terpenes">
        <TerpeneProfileExplorer />
      </section>

      <Divider />

      <section id="solutions">
        <SolutionsGrid />
      </section>

      <Divider />

      <section id="wizard">
        <FormulationWizard />
      </section>

      <Divider />

      <section id="contact">
        <SampleRequestForm />
      </section>

      <Footer />
    </div>
  );
}
