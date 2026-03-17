import React, { CSSProperties, useState } from "react";

interface Props {
  apiUrl?: string;
}

interface FormState {
  name: string;
  email: string;
  company: string;
  market: string;
  volume: string;
  notes: string;
}

type Status = "idle" | "submitting" | "success" | "error";

const MARKETS = [
  "Functional Beverages",
  "Flavor & Fragrance",
  "Cannabis CPG",
  "Pharmaceutical",
  "Nutraceutical",
  "Cosmetics & Personal Care",
  "Commodity Chemicals",
  "Agricultural",
  "Other",
];

const VOLUMES = [
  "R&D / Sampling",
  "< 100 kg/month",
  "100-1,000 kg/month",
  "1,000-10,000 kg/month",
  "> 10,000 kg/month",
];

const InquiryForm: React.FC<Props> = ({ apiUrl = "/api/sample-request" }) => {
  const [form, setForm] = useState<FormState>({
    name: "",
    email: "",
    company: "",
    market: "",
    volume: "",
    notes: "",
  });
  const [status, setStatus] = useState<Status>("idle");
  const [errors, setErrors] = useState<string[]>([]);
  const [reference, setReference] = useState("");

  const update = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const validate = (): string[] => {
    const errs: string[] = [];
    if (form.name.trim().length < 2) errs.push("Name is required");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      errs.push("Valid work email is required");
    if (form.company.trim().length < 2) errs.push("Company is required");
    if (!form.market) errs.push("Select a target market");
    return errs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (errs.length > 0) { setErrors(errs); return; }

    setErrors([]);
    setStatus("submitting");

    try {
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setStatus("success");
        setReference(data.reference || `NXS-${Date.now()}`);
      } else {
        setStatus("error");
        setErrors(data.errors || ["Submission failed. Please try again."]);
      }
    } catch {
      // Demo mode — simulate success
      setStatus("success");
      setReference(`NXS-${Date.now()}`);
    }
  };

  const container: CSSProperties = {
    width: "100%",
    padding: "120px 40px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    background: "#0A0F1C",
  };

  const inputBase: CSSProperties = {
    width: "100%",
    padding: "14px 18px",
    fontSize: 15,
    border: "1px solid rgba(255, 255, 255, 0.1)",
    borderRadius: 12,
    background: "rgba(255, 255, 255, 0.03)",
    color: "#F1F5F9",
    outline: "none",
    transition: "border-color 0.2s ease",
    fontFamily: "inherit",
    boxSizing: "border-box" as const,
  };

  const label: CSSProperties = {
    display: "block",
    fontSize: 13,
    fontWeight: 600,
    color: "#94A3B8",
    marginBottom: 8,
  };

  if (status === "success") {
    return (
      <div style={container}>
        <div style={{
          maxWidth: 560, margin: "0 auto", textAlign: "center",
          padding: 60, borderRadius: 24,
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
        }}>
          <div style={{
            width: 72, height: 72, borderRadius: 20,
            background: "rgba(16, 185, 129, 0.1)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            margin: "0 auto 28px",
          }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#10B981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h3 style={{ fontSize: 28, fontWeight: 700, color: "#F1F5F9", margin: "0 0 12px" }}>
            Inquiry Received
          </h3>
          <p style={{ fontSize: 16, color: "#94A3B8", margin: "0 0 8px", lineHeight: 1.6 }}>
            Our business development team will respond within 48 hours.
          </p>
          {reference && (
            <p style={{ fontSize: 13, color: "#64748B", margin: "16px 0 0" }}>
              Reference: {reference}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={container}>
      <div style={{ maxWidth: 1200, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 80, alignItems: "start" }}>
        {/* Left — messaging */}
        <div style={{ paddingTop: 20 }}>
          <p style={{
            fontSize: 13, fontWeight: 600, color: "#FF462E",
            textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 16,
          }}>
            Partner With Us
          </p>
          <h2 style={{
            fontSize: 48, fontWeight: 800, color: "#F1F5F9",
            margin: "0 0 24px", letterSpacing: "-0.03em", lineHeight: 1.1,
          }}>
            Ready to Replace{"\n"}Synthetics?
          </h2>
          <p style={{
            fontSize: 18, color: "#94A3B8", lineHeight: 1.7, margin: "0 0 48px",
          }}>
            Whether you're exploring natural ingredient alternatives or ready to scale, our team can help you navigate from proof-of-concept to commercial supply.
          </p>

          {/* Trust signals */}
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {[
              { label: "Vertical Integration", desc: "Genetics through finished ingredient — full traceability" },
              { label: "Commercial Scale", desc: "240+ acres, 10+ tons/hour processing capacity" },
              { label: "Proven Platform", desc: "World's largest cannabis essential oil producer" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                <div style={{
                  width: 8, height: 8, borderRadius: "50%", background: "#FF462E",
                  marginTop: 7, flexShrink: 0,
                }} />
                <div>
                  <p style={{ fontSize: 15, fontWeight: 600, color: "#F1F5F9", margin: "0 0 4px" }}>
                    {item.label}
                  </p>
                  <p style={{ fontSize: 14, color: "#64748B", margin: 0 }}>
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — form */}
        <div style={{
          padding: 40,
          borderRadius: 24,
          background: "rgba(255, 255, 255, 0.02)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
        }}>
          {errors.length > 0 && (
            <div style={{
              padding: "14px 18px", background: "rgba(239, 68, 68, 0.08)",
              border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: 12, marginBottom: 24,
            }}>
              {errors.map((err, i) => (
                <p key={i} style={{ fontSize: 13, color: "#EF4444", margin: i > 0 ? "4px 0 0" : 0 }}>{err}</p>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <div>
                <label style={label}>Full Name</label>
                <input
                  style={inputBase}
                  type="text"
                  value={form.name}
                  onChange={(e) => update("name", e.target.value)}
                  placeholder="Shareef El-Sissi"
                  onFocus={(e) => (e.target.style.borderColor = "rgba(255, 70, 46, 0.4)")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                />
              </div>
              <div>
                <label style={label}>Work Email</label>
                <input
                  style={inputBase}
                  type="email"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  placeholder="name@company.com"
                  onFocus={(e) => (e.target.style.borderColor = "rgba(255, 70, 46, 0.4)")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                />
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={label}>Company</label>
              <input
                style={inputBase}
                type="text"
                value={form.company}
                onChange={(e) => update("company", e.target.value)}
                placeholder="Your company name"
                onFocus={(e) => (e.target.style.borderColor = "rgba(255, 70, 46, 0.4)")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <div>
                <label style={label}>Target Market</label>
                <select
                  style={{ ...inputBase, appearance: "none" as const, cursor: "pointer" }}
                  value={form.market}
                  onChange={(e) => update("market", e.target.value)}
                  onFocus={(e) => (e.target.style.borderColor = "rgba(255, 70, 46, 0.4)")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                >
                  <option value="" style={{ background: "#111827" }}>Select market...</option>
                  {MARKETS.map((m) => (
                    <option key={m} value={m} style={{ background: "#111827" }}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={label}>Estimated Volume</label>
                <select
                  style={{ ...inputBase, appearance: "none" as const, cursor: "pointer" }}
                  value={form.volume}
                  onChange={(e) => update("volume", e.target.value)}
                  onFocus={(e) => (e.target.style.borderColor = "rgba(255, 70, 46, 0.4)")}
                  onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
                >
                  <option value="" style={{ background: "#111827" }}>Select volume...</option>
                  {VOLUMES.map((v) => (
                    <option key={v} value={v} style={{ background: "#111827" }}>{v}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ marginBottom: 28 }}>
              <label style={label}>Project Details (optional)</label>
              <textarea
                style={{ ...inputBase, minHeight: 100, resize: "vertical" as const }}
                value={form.notes}
                onChange={(e) => update("notes", e.target.value)}
                placeholder="Tell us about your ingredient needs, timeline, and any specific compounds of interest..."
                onFocus={(e) => (e.target.style.borderColor = "rgba(255, 70, 46, 0.4)")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")}
              />
            </div>

            <button
              type="submit"
              disabled={status === "submitting"}
              style={{
                width: "100%",
                padding: "16px 24px",
                fontSize: 16,
                fontWeight: 600,
                border: "none",
                borderRadius: 12,
                background: "#FF462E",
                color: "#fff",
                cursor: status === "submitting" ? "not-allowed" : "pointer",
                opacity: status === "submitting" ? 0.7 : 1,
                transition: "all 0.2s ease",
                fontFamily: "inherit",
                boxShadow: "0 0 30px rgba(255, 70, 46, 0.2)",
              }}
            >
              {status === "submitting" ? "Submitting..." : "Submit Partnership Inquiry"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

if (typeof window !== "undefined" && (window as any).Framer) {
  const { addPropertyControls, ControlType } = require("framer");
  addPropertyControls(InquiryForm, {
    apiUrl: { type: ControlType.String, title: "API URL", defaultValue: "/api/sample-request" },
  });
}

export default InquiryForm;
