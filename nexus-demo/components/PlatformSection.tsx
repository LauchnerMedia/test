import React, { CSSProperties, useState } from "react";

interface PipelineStep {
  id: string;
  number: string;
  title: string;
  description: string;
  details: string[];
  icon: React.ReactNode;
}

const STEPS: PipelineStep[] = [
  {
    id: "genetics",
    number: "01",
    title: "Proprietary Genetics",
    description: "Patented germplasm engineered for predictable expression of high-value terpene compounds across primary classes.",
    details: [
      "Issued & pending utility patents",
      "Proprietary seed inventory",
      "Predictable compound expression",
      "Acquired Biotech Institute IP",
    ],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v20M2 12h20" />
        <circle cx="12" cy="6" r="2" />
        <circle cx="12" cy="18" r="2" />
        <circle cx="6" cy="12" r="2" />
        <circle cx="18" cy="12" r="2" />
      </svg>
    ),
  },
  {
    id: "cultivation",
    number: "02",
    title: "Precision Cultivation",
    description: "240+ acres in California's San Joaquin Valley. Proven at commercial scale — not a lab experiment.",
    details: [
      "240+ acres of hemp cultivation",
      "San Joaquin Valley, California",
      "Operations in North & South America",
      "Capital-efficient vs. fermentation",
    ],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22V8" />
        <path d="M5 12H2a10 10 0 0020 0h-3" />
        <path d="M12 8a4 4 0 00-4-4" />
        <path d="M12 8a4 4 0 014-4" />
        <path d="M9 16c-1.5 0-3-1-3-3" />
        <path d="M15 16c1.5 0 3-1 3-3" />
      </svg>
    ),
  },
  {
    id: "extraction",
    number: "03",
    title: "Fresh Never Frozen\u00AE Extraction",
    description: "Subcritical H\u2082O solventless processing within 90 minutes of harvest at 10+ tons/hour throughput.",
    details: [
      "Solventless subcritical H\u2082O process",
      "Fresh material within 90 min of harvest",
      "10+ tons/hour processing capacity",
      "Chemical fidelity & stability",
    ],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3h6v7l3 4v4H6v-4l3-4V3z" />
        <path d="M8 3h8" />
        <circle cx="10" cy="17" r="1" />
        <circle cx="14" cy="15" r="1" />
      </svg>
    ),
  },
  {
    id: "ingredients",
    number: "04",
    title: "Natural Ingredients",
    description: "100% non-cannabinoid hemp-derived ingredients with vertical control from genetics through finished product.",
    details: [
      "100% non-cannabinoid ingredients",
      "Terpenes, flavors & functional compounds",
      "Replaces petroleum-based synthetics",
      "B2B ingredient supply worldwide",
    ],
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 7l-8-4-8 4" />
        <path d="M20 7v10l-8 4-8-4V7" />
        <path d="M12 11l8-4" />
        <path d="M12 11L4 7" />
        <path d="M12 11v10" />
      </svg>
    ),
  },
];

const PlatformSection: React.FC = () => {
  const [activeStep, setActiveStep] = useState<string | null>(null);

  const container: CSSProperties = {
    width: "100%",
    padding: "120px 40px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: "#0E1525",
    position: "relative",
  };

  return (
    <div style={container}>
      {/* Section header */}
      <div style={{ textAlign: "center", maxWidth: 700, margin: "0 auto 80px" }}>
        <p style={{
          fontSize: 13, fontWeight: 600, color: "#FF462E",
          textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16,
        }}>
          The Nexus Hemp Platform
        </p>
        <h2 style={{
          fontSize: 48, fontWeight: 800, color: "#F1F5F9",
          margin: "0 0 20px", letterSpacing: "-0.03em", lineHeight: 1.1,
        }}>
          From Seed to Ingredient,{"\n"}Vertically Integrated
        </h2>
        <p style={{
          fontSize: 18, color: "#94A3B8", lineHeight: 1.65, margin: 0,
        }}>
          Our molecular farming platform offers a capital-efficient, scalable alternative to precision fermentation — proven at hundreds of acres, not stuck in a lab.
        </p>
      </div>

      {/* Pipeline steps */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 24,
        maxWidth: 1200,
        margin: "0 auto",
        position: "relative",
      }}>
        {/* Connecting line */}
        <div style={{
          position: "absolute", top: 48, left: "12.5%", right: "12.5%", height: 2,
          background: "linear-gradient(90deg, rgba(21, 56, 114, 0.3), rgba(30, 77, 153, 0.6), rgba(21, 56, 114, 0.3))",
          zIndex: 0,
        }} />

        {STEPS.map((step) => {
          const isActive = activeStep === step.id;
          return (
            <div
              key={step.id}
              style={{
                position: "relative",
                zIndex: 1,
                padding: 32,
                borderRadius: 20,
                background: isActive ? "rgba(21, 56, 114, 0.15)" : "rgba(255, 255, 255, 0.02)",
                border: `1px solid ${isActive ? "rgba(30, 77, 153, 0.4)" : "rgba(255, 255, 255, 0.06)"}`,
                cursor: "pointer",
                transition: "all 0.3s ease",
                transform: isActive ? "translateY(-4px)" : "none",
                boxShadow: isActive ? "0 12px 40px rgba(21, 56, 114, 0.2)" : "none",
              }}
              onMouseEnter={() => setActiveStep(step.id)}
              onMouseLeave={() => setActiveStep(null)}
            >
              {/* Step number + icon */}
              <div style={{
                width: 56, height: 56, borderRadius: 16,
                background: isActive
                  ? "linear-gradient(135deg, #153872, #1E4D99)"
                  : "rgba(255, 255, 255, 0.05)",
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: 24, transition: "all 0.3s ease",
                color: isActive ? "#fff" : "#64748B",
                boxShadow: isActive ? "0 0 30px rgba(21, 56, 114, 0.3)" : "none",
              }}>
                {step.icon}
              </div>

              <span style={{
                fontSize: 12, fontWeight: 700, color: "#FF462E",
                letterSpacing: "0.08em", marginBottom: 8, display: "block",
              }}>
                STEP {step.number}
              </span>

              <h3 style={{
                fontSize: 20, fontWeight: 700, color: "#F1F5F9",
                margin: "0 0 12px", lineHeight: 1.3,
              }}>
                {step.title}
              </h3>

              <p style={{
                fontSize: 14, color: "#94A3B8", lineHeight: 1.65, margin: 0,
              }}>
                {step.description}
              </p>

              {/* Expanded details */}
              {isActive && (
                <div style={{ marginTop: 20, paddingTop: 20, borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  {step.details.map((detail, i) => (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", gap: 10, marginBottom: 10,
                    }}>
                      <div style={{
                        width: 5, height: 5, borderRadius: "50%", background: "#FF462E",
                        flexShrink: 0,
                      }} />
                      <span style={{ fontSize: 13, color: "#94A3B8" }}>{detail}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom quote */}
      <div style={{
        maxWidth: 800, margin: "80px auto 0", textAlign: "center",
        padding: "40px", borderRadius: 20,
        background: "rgba(255, 255, 255, 0.02)",
        border: "1px solid rgba(255, 255, 255, 0.06)",
      }}>
        <p style={{
          fontSize: 18, color: "#94A3B8", fontStyle: "italic", lineHeight: 1.7,
          margin: "0 0 20px",
        }}>
          "Hemp is an extraordinarily powerful biosynthetic platform when engineered with precision — turning plants into factories."
        </p>
        <p style={{
          fontSize: 14, fontWeight: 600, color: "#F1F5F9", margin: "0 0 4px",
        }}>
          Dr. Mark Lewis
        </p>
        <p style={{
          fontSize: 13, color: "#64748B", margin: 0,
        }}>
          Chief Genetic Architect, Nexus Agriscience
        </p>
      </div>
    </div>
  );
};

export default PlatformSection;
