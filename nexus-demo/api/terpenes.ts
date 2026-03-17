import type { VercelRequest, VercelResponse } from "@vercel/node";

const terpenes = [
  {
    id: "terp-001",
    name: "Myrcene",
    aroma: "Earthy, musky, with hints of ripe fruit",
    effect: "Relaxation",
    description:
      "The most abundant terpene in modern cannabis cultivars. Myrcene contributes sedative, analgesic, and anti-inflammatory properties.",
    applications: [
      "Cannabis extracts",
      "Sleep-aid beverages",
      "Topical formulations",
      "Herbal supplements",
    ],
  },
  {
    id: "terp-002",
    name: "Limonene",
    aroma: "Bright citrus, lemon zest, orange peel",
    effect: "Energy",
    description:
      "A monocyclic monoterpene prevalent in citrus rinds. Limonene is associated with elevated mood, stress relief, and improved gastric motility.",
    applications: [
      "Citrus beverages",
      "Mood-enhancing edibles",
      "Cleaning products",
      "Flavor systems",
    ],
  },
  {
    id: "terp-003",
    name: "Linalool",
    aroma: "Floral, lavender, subtle spice",
    effect: "Calm",
    description:
      "Found abundantly in lavender and over 200 plant species. Linalool demonstrates anxiolytic, sedative, and anticonvulsant properties.",
    applications: [
      "Aromatherapy products",
      "Calming beverages",
      "Skincare formulations",
      "Cannabis blends",
    ],
  },
  {
    id: "terp-004",
    name: "Beta-Caryophyllene",
    aroma: "Spicy, peppery, woody",
    effect: "Relief",
    description:
      "A sesquiterpene unique in its ability to bind CB2 cannabinoid receptors. Exhibits potent anti-inflammatory and analgesic activity.",
    applications: [
      "Anti-inflammatory supplements",
      "Spice-forward beverages",
      "Pain-relief topicals",
      "Functional foods",
    ],
  },
  {
    id: "terp-005",
    name: "Pinene",
    aroma: "Fresh pine, coniferous, herbal",
    effect: "Focus",
    description:
      "The most widely encountered terpene in nature. Alpha-pinene acts as a bronchodilator and acetylcholinesterase inhibitor.",
    applications: [
      "Focus-enhancing beverages",
      "Respiratory supplements",
      "Forest-inspired flavors",
      "Cannabis cultivar design",
    ],
  },
  {
    id: "terp-006",
    name: "Terpinolene",
    aroma: "Piney, floral, herbaceous, slightly citrus",
    effect: "Energy",
    description:
      "A multifaceted monoterpene with a complex aromatic profile. Shows antioxidant and mildly sedative properties at higher concentrations.",
    applications: [
      "Uplifting beverage formulations",
      "Personal care products",
      "Flavor complexity agents",
      "Sativa-dominant blends",
    ],
  },
  {
    id: "terp-007",
    name: "Humulene",
    aroma: "Hoppy, earthy, subtle wood",
    effect: "Relief",
    description:
      "An isomer of beta-caryophyllene found in hops, sage, and ginseng. Demonstrates appetite-suppressant and anti-inflammatory properties.",
    applications: [
      "Hop-forward beverages",
      "Weight management supplements",
      "Anti-inflammatory formulas",
      "Craft flavor profiles",
    ],
  },
  {
    id: "terp-008",
    name: "Ocimene",
    aroma: "Sweet, herbaceous, tropical, woody",
    effect: "Energy",
    description:
      "A monoterpene found in mint, parsley, orchids, and mangoes. Exhibits antiviral, antifungal, and decongestant properties.",
    applications: [
      "Tropical beverages",
      "Fragrance blending",
      "Decongestant formulations",
      "Exotic flavor systems",
    ],
  },
  {
    id: "terp-009",
    name: "Bisabolol",
    aroma: "Light floral, sweet, chamomile-like",
    effect: "Calm",
    description:
      "A monocyclic sesquiterpene alcohol derived primarily from chamomile. Prized for anti-irritant, anti-inflammatory, and antimicrobial properties.",
    applications: [
      "Skincare actives",
      "Calming teas and beverages",
      "Sensitive-skin topicals",
      "Nighttime cannabis blends",
    ],
  },
  {
    id: "terp-010",
    name: "Geraniol",
    aroma: "Rose, geranium, citronella",
    effect: "Focus",
    description:
      "A monoterpenoid alcohol found in rose oil, citronella, and lemongrass. Functions as a natural insect repellent and shows neuroprotective potential.",
    applications: [
      "Floral beverages",
      "Natural insect repellents",
      "Premium fragrance compounds",
      "Neuroprotective research",
    ],
  },
];

export default function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const { effect } = req.query;

  let filtered = terpenes;
  if (typeof effect === "string" && effect.length > 0) {
    filtered = terpenes.filter(
      (t) => t.effect.toLowerCase() === effect.toLowerCase()
    );
  }

  return res.status(200).json({ terpenes: filtered, count: filtered.length });
}
