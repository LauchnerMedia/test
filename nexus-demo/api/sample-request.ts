import type { VercelRequest, VercelResponse } from "@vercel/node";

interface SampleRequestBody {
  name: string;
  email: string;
  company: string;
  productCategory: string;
  notes?: string;
}

function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validateRequest(body: unknown): {
  valid: boolean;
  errors: string[];
  data?: SampleRequestBody;
} {
  const errors: string[] = [];

  if (!body || typeof body !== "object") {
    return { valid: false, errors: ["Request body is required"] };
  }

  const b = body as Record<string, unknown>;

  if (!b.name || typeof b.name !== "string" || b.name.trim().length < 2) {
    errors.push("Name is required (minimum 2 characters)");
  }

  if (!b.email || typeof b.email !== "string" || !validateEmail(b.email)) {
    errors.push("A valid email address is required");
  }

  if (
    !b.company ||
    typeof b.company !== "string" ||
    b.company.trim().length < 2
  ) {
    errors.push("Company name is required (minimum 2 characters)");
  }

  if (
    !b.productCategory ||
    typeof b.productCategory !== "string" ||
    b.productCategory.trim().length === 0
  ) {
    errors.push("Product category is required");
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  return {
    valid: true,
    errors: [],
    data: {
      name: (b.name as string).trim(),
      email: (b.email as string).trim().toLowerCase(),
      company: (b.company as string).trim(),
      productCategory: (b.productCategory as string).trim(),
      notes:
        typeof b.notes === "string" ? b.notes.trim() : undefined,
    },
  };
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { valid, errors, data } = validateRequest(req.body);

  if (!valid) {
    return res.status(400).json({ success: false, errors });
  }

  // Log the submission (in production, persist to database)
  console.log("[Sample Request]", {
    timestamp: new Date().toISOString(),
    ...data,
  });

  return res.status(200).json({
    success: true,
    message: "Sample request received. Our formulation team will be in touch within 24 hours.",
    reference: `NXS-${Date.now().toString(36).toUpperCase()}`,
  });
}
