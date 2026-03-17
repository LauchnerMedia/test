import React, { CSSProperties, useState } from "react";

// ─── Types ───────────────────────────────────────────────────────
interface Props {
  accentColor?: string;
  onComplete?: (result: BlendResult) => void;
}

interface BlendResult {
  effect: string;
  flavor: string;
  delivery: string;
  blend: { name: string; percentage: number }[];
  notes: string;
}

// ─── Recommendation Engine (mock) ────────────────────────────────
const EFFECTS = ["Relaxation", "Energy", "Focus", "Calm", "Relief"];
const FLAVORS = ["Citrus", "Berry", "Herbal", "Tropical", "Earthy"];
const DELIVERY = ["Beverage", "Edible", "Vaporizer", "Topical", "Tincture"];

const BLENDS: Record<string, { name: string; percentage: number }[]> = {
  "Relaxation-Citrus": [
    { name: "Myrcene", percentage: 40 },
    { name: "Limonene", percentage: 35 },
    { name: "Linalool", percentage: 25 },
  ],
  "Energy-Tropical": [
    { name: "Limonene", percentage: 35 },
    { name: "Terpinolene", percentage: 30 },
    { name: "Ocimene", percentage: 20 },
    { name: "Pinene", percentage: 15 },
  ],
  "Focus-Herbal": [
    { name: "Pinene", percentage: 40 },
    { name: "Geraniol", percentage: 30 },
    { name: "Terpinolene", percentage: 30 },
  ],
  default: [
    { name: "Myrcene", percentage: 30 },
    { name: "Limonene", percentage: 25 },
    { name: "Linalool", percentage: 20 },
    { name: "Pinene", percentage: 15 },
    { name: "Beta-Caryophyllene", percentage: 10 },
  ],
};

function getBlend(effect: string, flavor: string): { name: string; percentage: number }[] {
  return BLENDS[`${effect}-${flavor}`] || BLENDS.default;
}

// ─── Component ───────────────────────────────────────────────────
const FormulationWizard: React.FC<Props> = ({ accentColor = "#0B6E4F" }) => {
  const [step, setStep] = useState(0);
  const [effect, setEffect] = useState("");
  const [flavor, setFlavor] = useState("");
  const [delivery, setDelivery] = useState("");
  const [result, setResult] = useState<BlendResult | null>(null);

  const handleSelect = (value: string) => {
    if (step === 0) {
      setEffect(value);
      setStep(1);
    } else if (step === 1) {
      setFlavor(value);
      setStep(2);
    } else if (step === 2) {
      setDelivery(value);
      const blend = getBlend(effect, value);
      setResult({
        effect,
        flavor,
        delivery: value,
        blend,
        notes: `Optimized ${effect.toLowerCase()} blend with ${flavor.toLowerCase()} notes, formulated for ${value.toLowerCase()} delivery. Recommended starting concentration: 2-4% by weight.`,
      });
      setStep(3);
    }
  };

  const reset = () => {
    setStep(0);
    setEffect("");
    setFlavor("");
    setDelivery("");
    setResult(null);
  };

  const container: CSSProperties = {
    width: "100%",
    maxWidth: 640,
    margin: "0 auto",
    padding: "64px 24px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  };

  const heading: CSSProperties = {
    fontSize: 32,
    fontWeight: 700,
    color: "#0F1F17",
    textAlign: "center",
    margin: "0 0 8px",
    letterSpacing: "-0.02em",
  };

  const subtitle: CSSProperties = {
    fontSize: 15,
    color: "#4A6358",
    textAlign: "center",
    margin: "0 0 36px",
  };

  const stepIndicator: CSSProperties = {
    display: "flex",
    justifyContent: "center",
    gap: 8,
    marginBottom: 32,
  };

  const stepDot = (active: boolean, completed: boolean): CSSProperties => ({
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: completed ? accentColor : active ? "#E8AA42" : "#E2E8E5",
    transition: "background 0.3s ease",
  });

  const stepLabel: CSSProperties = {
    fontSize: 13,
    fontWeight: 600,
    color: "#8A9E94",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    textAlign: "center",
    marginBottom: 16,
  };

  const optionGrid: CSSProperties = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
    gap: 12,
  };

  const optionBtn = (selected: boolean): CSSProperties => ({
    padding: "16px 12px",
    fontSize: 15,
    fontWeight: 500,
    border: `2px solid ${selected ? accentColor : "#E2E8E5"}`,
    borderRadius: 12,
    background: selected ? `${accentColor}0D` : "#fff",
    color: selected ? accentColor : "#0F1F17",
    cursor: "pointer",
    transition: "all 0.2s ease",
    textAlign: "center",
  });

  const STEPS = [
    { label: "Choose Effect", options: EFFECTS },
    { label: "Choose Flavor Profile", options: FLAVORS },
    { label: "Delivery Format", options: DELIVERY },
  ];

  return (
    <div style={container}>
      <h2 style={heading}>Formulation Wizard</h2>
      <p style={subtitle}>Three steps to your custom terpene blend recommendation</p>

      <div style={stepIndicator}>
        {[0, 1, 2].map((i) => (
          <div key={i} style={stepDot(step === i, step > i)} />
        ))}
      </div>

      {step < 3 && (
        <>
          <p style={stepLabel}>
            Step {step + 1} of 3 — {STEPS[step].label}
          </p>
          <div style={optionGrid}>
            {STEPS[step].options.map((opt) => {
              const selected =
                (step === 0 && opt === effect) ||
                (step === 1 && opt === flavor) ||
                (step === 2 && opt === delivery);
              return (
                <button
                  key={opt}
                  style={optionBtn(selected)}
                  onClick={() => handleSelect(opt)}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </>
      )}

      {step === 3 && result && (
        <div
          style={{
            background: "#F8FAF9",
            borderRadius: 16,
            padding: 32,
            border: "1px solid #E2E8E5",
          }}
        >
          <h3
            style={{
              fontSize: 20,
              fontWeight: 600,
              color: "#0F1F17",
              margin: "0 0 4px",
            }}
          >
            Recommended Blend
          </h3>
          <p style={{ fontSize: 14, color: "#4A6358", margin: "0 0 24px" }}>
            {result.effect} + {result.flavor} + {result.delivery}
          </p>

          {/* Bar chart */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 }}>
            {result.blend.map((b) => (
              <div key={b.name}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 13,
                    fontWeight: 500,
                    color: "#0F1F17",
                    marginBottom: 4,
                  }}
                >
                  <span>{b.name}</span>
                  <span>{b.percentage}%</span>
                </div>
                <div
                  style={{
                    height: 8,
                    borderRadius: 4,
                    background: "#E2E8E5",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${b.percentage}%`,
                      height: "100%",
                      borderRadius: 4,
                      background: accentColor,
                      transition: "width 0.5s ease",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <p
            style={{
              fontSize: 14,
              color: "#4A6358",
              lineHeight: 1.6,
              margin: "0 0 24px",
              padding: "16px",
              background: "rgba(11, 110, 79, 0.04)",
              borderRadius: 8,
            }}
          >
            {result.notes}
          </p>

          <button
            onClick={reset}
            style={{
              padding: "12px 28px",
              fontSize: 14,
              fontWeight: 600,
              border: `2px solid ${accentColor}`,
              borderRadius: 9999,
              background: "transparent",
              color: accentColor,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            Start Over
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Framer Property Controls ────────────────────────────────────
if (typeof window !== "undefined" && (window as any).Framer) {
  const { addPropertyControls, ControlType } = require("framer");
  addPropertyControls(FormulationWizard, {
    accentColor: { type: ControlType.Color, title: "Accent Color", defaultValue: "#0B6E4F" },
  });
}

export default FormulationWizard;
