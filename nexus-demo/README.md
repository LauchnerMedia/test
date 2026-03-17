# Nexus Agriscience — Demo Architecture

A rapid-prototype demo for **Nexus Agriscience**, a terpene science and ingredient platform. Built for Framer Code Components with a Vercel serverless backend.

---

## Project Structure

```
/nexus-demo
  /components
    HeroSection.tsx          — Hero with animated gradient background
    TerpeneProfileExplorer.tsx — Filterable terpene card grid
    SolutionsGrid.tsx        — Solutions/services card grid
    FormulationWizard.tsx    — 3-step blend recommender
    SampleRequestForm.tsx    — Contact/sample request form
  /data
    terpenes.json            — 10 terpene entries
    solutions.json           — 10 solution entries
  /api
    terpenes.ts              — GET /api/terpenes (Vercel serverless)
    sample-request.ts        — POST /api/sample-request (Vercel serverless)
  /utils
    theme.ts                 — Design tokens (colors, fonts, radii, shadows)
  README.md
```

---

## Quick Start — Deploy Backend to Vercel

### 1. Initialize a Vercel project

```bash
cd nexus-demo
npm init -y
npm install @vercel/node --save-dev
```

### 2. Create `vercel.json`

```json
{
  "functions": {
    "api/*.ts": {
      "memory": 128,
      "maxDuration": 10
    }
  }
}
```

### 3. Deploy

```bash
npx vercel deploy
```

Your API endpoints will be live at:
- `GET  https://your-project.vercel.app/api/terpenes`
- `GET  https://your-project.vercel.app/api/terpenes?effect=Energy`
- `POST https://your-project.vercel.app/api/sample-request`

---

## How to Use Components in Framer

### Option A: Framer Code Components (recommended)

1. Open your Framer project
2. Go to **Assets → Code → New File**
3. Copy the contents of any component file (e.g., `HeroSection.tsx`)
4. Paste into the Framer code editor
5. The component will appear in the Assets panel with property controls

### Option B: Framer Code Overrides

Use code overrides to connect fetch calls to the backend:

```tsx
import { Override } from "framer"

export function withTerpeneData(): Override {
  const [data, setData] = React.useState([])

  React.useEffect(() => {
    fetch("https://your-project.vercel.app/api/terpenes")
      .then(res => res.json())
      .then(d => setData(d.terpenes))
  }, [])

  return { data }
}
```

---

## Connecting Fetch Calls

Each component that needs live data can be pointed at your Vercel deployment:

| Component | Property | Value |
|-----------|----------|-------|
| `TerpeneProfileExplorer` | `apiUrl` | `https://your-project.vercel.app/api/terpenes` |
| `SampleRequestForm` | `apiUrl` | `https://your-project.vercel.app/api/sample-request` |

Components ship with embedded mock data so they render immediately in Framer without a backend connection.

---

## Running the Demo Quickly

**For a live demo presentation:**

1. Deploy the `/api` folder to Vercel (3 minutes)
2. Open Framer, create a new project
3. Paste each component as a Code Component
4. Arrange on canvas: Hero → TerpeneExplorer → Solutions → Wizard → Form
5. Update `apiUrl` props to point at your Vercel deployment
6. Present from Framer preview or publish to a `.framer.app` URL

**For a static demo (no backend):**

All components include embedded mock data. Simply paste them into Framer — they work standalone with no API calls required.

---

## Design Direction

The visual language follows a **biotech + modern SaaS** aesthetic:

- **Colors**: Deep greens (`#0B6E4F`) for trust and science, warm amber (`#E8AA42`) for CTAs
- **Typography**: Inter — clean, modern, highly legible
- **Cards**: Soft borders, generous padding, subtle shadows
- **Layout**: Centered, max-width constrained, generous whitespace
- **Motion**: Gentle hover lifts, CSS gradient animation, smooth transitions

Think: **Notion clarity + Stripe polish + biotech credibility**.

---

## Component Summary

| Component | Key Features | Framer Controls |
|-----------|-------------|-----------------|
| **HeroSection** | Headline, subheadline, CTA, animated gradient orbs | headline, subheadline, ctaLabel, ctaUrl, gradientFrom, gradientTo |
| **TerpeneProfileExplorer** | Filter bar, expandable cards, effect badges | apiUrl, accentColor |
| **SolutionsGrid** | 4 solution cards, hover effects, industry tags | sectionTitle, sectionSubtitle, accentColor |
| **FormulationWizard** | 3-step selector, blend bar chart, recommendation | accentColor |
| **SampleRequestForm** | 5-field form, validation, POST to API, success state | apiUrl, accentColor, sectionTitle |

---

## Data Model

### Terpene
```typescript
{
  id: string
  name: string
  aroma: string
  effect: "Relaxation" | "Energy" | "Calm" | "Relief" | "Focus"
  description: string
  applications: string[]
}
```

### Solution
```typescript
{
  id: string
  title: string
  description: string
  industries: string[]
}
```

### Sample Request (POST body)
```typescript
{
  name: string
  email: string
  company: string
  productCategory: string
  notes?: string
}
```

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Framer Code Components
- **Backend**: Vercel Serverless Functions (Node.js)
- **Styling**: Inline CSS (Framer-compatible, zero build dependencies)
- **Data**: Static JSON + mock data embedded in components
- **No external dependencies** beyond React (ships with Framer)
