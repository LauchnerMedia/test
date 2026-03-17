import React from "react";
import HeroSection from "../components/HeroSection";
import PlatformSection from "../components/PlatformSection";
import MarketsSection from "../components/MarketsSection";
import NewsSection from "../components/NewsSection";
import InquiryForm from "../components/InquiryForm";

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
      padding: "16px 40px",
      background: "rgba(10, 15, 28, 0.8)",
      backdropFilter: "blur(20px)",
      borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {/* Nexus logo mark — molecular/hexagonal motif */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 10,
          background: "linear-gradient(135deg, #153872, #1E4D99)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 20px rgba(21, 56, 114, 0.4)",
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" />
          <path d="M12 12L2 7" />
          <path d="M12 12l10-5" />
          <path d="M12 12v10" />
        </svg>
      </div>
      <span style={{ fontSize: 18, fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em" }}>
        Nexus Agriscience
      </span>
    </div>

    <div style={{ display: "flex", gap: 32, alignItems: "center" }}>
      {[
        { label: "Platform", href: "#platform" },
        { label: "Markets", href: "#markets" },
        { label: "News", href: "#news" },
        { label: "Contact", href: "#contact" },
      ].map((link) => (
        <a
          key={link.href}
          href={link.href}
          style={{
            fontSize: 14,
            fontWeight: 500,
            color: "#94A3B8",
            textDecoration: "none",
            transition: "color 0.2s",
          }}
          onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "#F1F5F9")}
          onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "#94A3B8")}
        >
          {link.label}
        </a>
      ))}
      <a
        href="#contact"
        style={{
          fontSize: 14,
          fontWeight: 600,
          color: "#fff",
          background: "#FF462E",
          padding: "8px 20px",
          borderRadius: 8,
          textDecoration: "none",
          transition: "background 0.2s",
          boxShadow: "0 0 20px rgba(255, 70, 46, 0.2)",
        }}
        onMouseEnter={(e) => ((e.target as HTMLElement).style.background = "#E63B25")}
        onMouseLeave={(e) => ((e.target as HTMLElement).style.background = "#FF462E")}
      >
        Partner With Us
      </a>
    </div>
  </nav>
);

const Footer: React.FC = () => (
  <footer
    style={{
      padding: "60px 40px 40px",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      borderTop: "1px solid rgba(255, 255, 255, 0.06)",
      background: "#070B14",
    }}
  >
    <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 40 }}>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "linear-gradient(135deg, #153872, #1E4D99)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" />
              <path d="M12 12L2 7" />
              <path d="M12 12l10-5" />
              <path d="M12 12v10" />
            </svg>
          </div>
          <span style={{ fontSize: 16, fontWeight: 700, color: "#F1F5F9" }}>Nexus Agriscience</span>
        </div>
        <p style={{ fontSize: 14, color: "#64748B", maxWidth: 360, lineHeight: 1.6 }}>
          Unlocking hemp's potential as a scalable source of natural ingredients for wellness, flavor, fragrance, and pharmaceutical applications.
        </p>
      </div>

      <div style={{ display: "flex", gap: 64 }}>
        <div>
          <p style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>Company</p>
          {["Platform", "Markets", "News", "Careers"].map((item) => (
            <p key={item} style={{ fontSize: 14, color: "#94A3B8", marginBottom: 10, cursor: "pointer" }}>{item}</p>
          ))}
        </div>
        <div>
          <p style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>Subsidiaries</p>
          <p style={{ fontSize: 14, color: "#94A3B8", marginBottom: 10 }}>Terpene Belt Farms</p>
          <p style={{ fontSize: 14, color: "#94A3B8", marginBottom: 10 }}>Biotech Institute</p>
        </div>
        <div>
          <p style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>Location</p>
          <p style={{ fontSize: 14, color: "#94A3B8", marginBottom: 4 }}>Livermore, California</p>
          <p style={{ fontSize: 14, color: "#64748B" }}>North America & South America</p>
        </div>
      </div>
    </div>

    <div style={{ maxWidth: 1200, margin: "40px auto 0", paddingTop: 24, borderTop: "1px solid rgba(255, 255, 255, 0.06)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
      <p style={{ fontSize: 13, color: "#475569" }}>
        &copy; 2026 Nexus Agriscience. All rights reserved.
      </p>
      <p style={{ fontSize: 12, color: "#334155" }}>
        Demo prototype — Data is illustrative
      </p>
    </div>
  </footer>
);

export default function App() {
  return (
    <div style={{ background: "#0A0F1C", minHeight: "100vh" }}>
      <Nav />

      <section id="hero">
        <HeroSection />
      </section>

      <section id="platform">
        <PlatformSection />
      </section>

      <section id="markets">
        <MarketsSection />
      </section>

      <section id="news">
        <NewsSection />
      </section>

      <section id="contact">
        <InquiryForm />
      </section>

      <Footer />
    </div>
  );
}
