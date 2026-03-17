import React, { CSSProperties, useState } from "react";

// ─── Types ───────────────────────────────────────────────────────
interface Props {
  apiUrl?: string;
  accentColor?: string;
  sectionTitle?: string;
}

interface FormState {
  name: string;
  email: string;
  company: string;
  productCategory: string;
  notes: string;
}

type Status = "idle" | "submitting" | "success" | "error";

const CATEGORIES = [
  "Beverage",
  "Cannabis",
  "Flavor & Fragrance",
  "Nutraceutical",
  "Cosmetics",
  "Agricultural",
  "Other",
];

// ─── Component ───────────────────────────────────────────────────
const SampleRequestForm: React.FC<Props> = ({
  apiUrl = "/api/sample-request",
  accentColor = "#0B6E4F",
  sectionTitle = "Request a Sample",
}) => {
  const [form, setForm] = useState<FormState>({
    name: "",
    email: "",
    company: "",
    productCategory: "",
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
      errs.push("Valid email is required");
    if (form.company.trim().length < 2) errs.push("Company is required");
    if (!form.productCategory) errs.push("Select a product category");
    return errs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (errs.length > 0) {
      setErrors(errs);
      return;
    }

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
        setReference(data.reference || "");
      } else {
        setStatus("error");
        setErrors(data.errors || ["Submission failed. Please try again."]);
      }
    } catch {
      setStatus("error");
      setErrors(["Network error. Please check your connection."]);
    }
  };

  const container: CSSProperties = {
    width: "100%",
    maxWidth: 560,
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

  const fieldGroup: CSSProperties = {
    marginBottom: 20,
  };

  const label: CSSProperties = {
    display: "block",
    fontSize: 13,
    fontWeight: 600,
    color: "#0F1F17",
    marginBottom: 6,
  };

  const inputBase: CSSProperties = {
    width: "100%",
    padding: "12px 16px",
    fontSize: 15,
    border: "1px solid #E2E8E5",
    borderRadius: 10,
    background: "#F8FAF9",
    color: "#0F1F17",
    outline: "none",
    transition: "border-color 0.2s ease",
    fontFamily: "inherit",
    boxSizing: "border-box",
  };

  const submitBtn: CSSProperties = {
    width: "100%",
    padding: "14px 24px",
    fontSize: 16,
    fontWeight: 600,
    border: "none",
    borderRadius: 10,
    background: accentColor,
    color: "#FFFFFF",
    cursor: status === "submitting" ? "not-allowed" : "pointer",
    opacity: status === "submitting" ? 0.7 : 1,
    transition: "opacity 0.2s ease",
    fontFamily: "inherit",
  };

  if (status === "success") {
    return (
      <div style={container}>
        <div
          style={{
            textAlign: "center",
            padding: 40,
            background: "#F8FAF9",
            borderRadius: 16,
            border: "1px solid #E2E8E5",
          }}
        >
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: `${accentColor}15`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 20px",
            }}
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h3
            style={{
              fontSize: 22,
              fontWeight: 600,
              color: "#0F1F17",
              margin: "0 0 8px",
            }}
          >
            Request Received
          </h3>
          <p style={{ fontSize: 15, color: "#4A6358", margin: "0 0 8px", lineHeight: 1.6 }}>
            Our formulation team will reach out within 24 hours.
          </p>
          {reference && (
            <p style={{ fontSize: 13, color: "#8A9E94", margin: 0 }}>
              Reference: {reference}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={container}>
      <h2 style={heading}>{sectionTitle}</h2>
      <p style={subtitle}>
        Tell us about your project and we'll prepare a custom terpene sample kit.
      </p>

      {errors.length > 0 && (
        <div
          style={{
            padding: "12px 16px",
            background: "#FEF2F2",
            border: "1px solid #FCA5A5",
            borderRadius: 10,
            marginBottom: 20,
          }}
        >
          {errors.map((err, i) => (
            <p
              key={i}
              style={{ fontSize: 13, color: "#D94F4F", margin: i > 0 ? "4px 0 0" : 0 }}
            >
              {err}
            </p>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={fieldGroup}>
          <label style={label}>Full Name</label>
          <input
            style={inputBase}
            type="text"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            placeholder="Jane Chen"
          />
        </div>

        <div style={fieldGroup}>
          <label style={label}>Work Email</label>
          <input
            style={inputBase}
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            placeholder="jane@company.com"
          />
        </div>

        <div style={fieldGroup}>
          <label style={label}>Company</label>
          <input
            style={inputBase}
            type="text"
            value={form.company}
            onChange={(e) => update("company", e.target.value)}
            placeholder="Acme Beverages"
          />
        </div>

        <div style={fieldGroup}>
          <label style={label}>Product Category</label>
          <select
            style={{ ...inputBase, appearance: "none", cursor: "pointer" }}
            value={form.productCategory}
            onChange={(e) => update("productCategory", e.target.value)}
          >
            <option value="">Select a category...</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div style={fieldGroup}>
          <label style={label}>Project Notes (optional)</label>
          <textarea
            style={{ ...inputBase, minHeight: 100, resize: "vertical" }}
            value={form.notes}
            onChange={(e) => update("notes", e.target.value)}
            placeholder="Tell us about your formulation goals..."
          />
        </div>

        <button type="submit" style={submitBtn} disabled={status === "submitting"}>
          {status === "submitting" ? "Submitting..." : "Submit Request"}
        </button>
      </form>
    </div>
  );
};

// ─── Framer Property Controls ────────────────────────────────────
if (typeof window !== "undefined" && (window as any).Framer) {
  const { addPropertyControls, ControlType } = require("framer");
  addPropertyControls(SampleRequestForm, {
    apiUrl: { type: ControlType.String, title: "API URL", defaultValue: "/api/sample-request" },
    accentColor: { type: ControlType.Color, title: "Accent Color", defaultValue: "#0B6E4F" },
    sectionTitle: { type: ControlType.String, title: "Title", defaultValue: "Request a Sample" },
  });
}

export default SampleRequestForm;
