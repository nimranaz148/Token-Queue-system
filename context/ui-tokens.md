# UI Tokens

Design tokens for Clinic Token & Queue SaaS. Use these exact values throughout the codebase — never hardcode colors and never use raw Tailwind palette classes in components.

> **Status: provisional.** The blueprint's look (teal/green clinical primary, deep slate, role accents: patient teal, reception blue, doctor purple, TV dark green, owner amber) is the direction; exact values are set by the `uiux` skill. Final branding, iconography, color palette, typography and visual polish are finalized in a separate UI design pass. This token set is a brand-neutral enterprise system that unblocks Phase 0. When brand assets arrive, **only the values in this file change** — component code that uses tokens correctly needs no edits. That is the entire point of the token layer.
>
> The functional information architecture and workflow defined in the PRD **shall not change** without product-owner approval, regardless of visual restyling.

---

## How to Use

This project uses **Tailwind CSS v4**. Tokens are defined with the `@theme` directive in `apps/web/src/styles/globals.css`. No `tailwind.config.ts` is needed for colors or tokens.

Tailwind v4 generates utilities from `@theme` variables automatically:

- `--color-accent` gives `bg-accent`, `text-accent`, `border-accent`
- `--color-surface` gives `bg-surface`, `text-surface`, `border-surface`

```tsx
// Correct — generated utility classes
className="bg-surface text-fg border-border"

// Also correct — CSS variable reference
style={{ color: "var(--color-fg)" }}

// Never — hardcoded hex
className="bg-[#f8fafc] text-[#0f172a]"

// Never — raw Tailwind palette
className="bg-blue-500 text-gray-600"
```

---

## Design Intent

Clinic queue (patient phones, reception desk, doctor panel, waiting-room TV) screens are read before they are clicked. These tokens optimize for **density, scanability and long-session legibility**, not marketing impact.

- Warm paper ground and botanical teal so queue status remains clear without looking sterile
- One accent, used sparingly — primary actions and active navigation only
- Semantic status colors that survive being the only differentiator in a dense grid

---

## globals.css — Complete Token Definition

```css
@import "tailwindcss";

@theme {
  /* ---------- Typography ---------- */
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --font-display: Georgia, "Times New Roman", serif;

  /* ---------- Page and surface backgrounds ---------- */
  --color-canvas: #f3f4ed;          /* warm paper ground */
  --color-surface: #fffefa;          /* cards, panels, form shells */
  --color-surface-raised: #fffefa;   /* modals, popovers, dropdowns */
  --color-surface-sunken: #e9ede4;   /* grid headers, read-only fields */
  --color-surface-hover: #f0f2ea;    /* row and menu hover */
  --color-surface-active: #dce5d9;   /* pressed, selected row */

  /* ---------- Borders ---------- */
  --color-border: #dce2d7;           /* default panel and input border */
  --color-border-strong: #c5d0c3;    /* grid cell dividers, separators */
  --color-border-focus: #19745e;     /* focus ring */

  /* ---------- Text ---------- */
  --color-fg: #1a2e27;               /* primary text, grid values */
  --color-fg-muted: #5d6d64;         /* labels, secondary text */
  --color-fg-subtle: #819087;        /* placeholders, disabled, meta */
  --color-fg-inverse: #ffffff;       /* text on accent/solid fills */

  /* ---------- Accent (primary action) ---------- */
  --color-accent: #19745e;
  --color-accent-hover: #145d4d;
  --color-accent-active: #104b3f;
  --color-accent-subtle: #e3efe8;    /* active nav background, selected tint */
  --color-accent-border: #bfd7c7;

  /* ---------- Semantic status ---------- */
  --color-success: #28734f;
  --color-success-subtle: #e8f3e9;
  --color-success-border: #c1dec6;

  --color-warning: #a56721;
  --color-warning-subtle: #f7f0df;
  --color-warning-border: #ead4a9;

  --color-danger: #a8453c;
  --color-danger-hover: #91382f;
  --color-danger-subtle: #f7e9e5;
  --color-danger-border: #e7c4bc;

  --color-info: #3c7180;
  --color-info-subtle: #e7f0f0;
  --color-info-border: #c4d9da;

  --color-neutral: #6a756f;
  --color-neutral-subtle: #ecefe9;
  --color-neutral-border: #cbd2c8;

  /* ---------- Special TV Display ---------- */
  --color-tv-surface: #064e3b;
  --color-tv-highlight: #34d399;

  /* ---------- Financial figures ---------- */
  --color-positive: #28734f;
  --color-negative: #a8453c;

  /* ---------- Charts (dashboards) ---------- */
  --color-chart-1: #19745e;
  --color-chart-2: #739b80;
  --color-chart-3: #3c7180;
  --color-chart-4: #ad7a36;
  --color-chart-5: #508b68;
  --color-chart-6: #a66d63;
  --color-chart-grid: #dce2d7;
  --color-chart-axis: #819087;

  /* ---------- Type scale ---------- */
  --text-display: clamp(3.25rem, 6vw, 4.5rem);
  --text-2xs: 0.6875rem;   /* 11px */
  --text-xs: 0.75rem;      /* 12px */
  --text-sm: 0.8125rem;    /* 13px */
  --text-base: 0.875rem;   /* 14px */
  --text-md: 1rem;         /* 16px */
  --text-lg: 1.125rem;     /* 18px */
  --text-xl: 1.375rem;     /* 22px */
  --text-2xl: 1.75rem;     /* 28px */
  --text-3xl: 2.25rem;     /* 36px */

  /* ---------- Spacing ---------- */
  --spacing-0-5: 0.125rem;
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-3: 0.75rem;
  --spacing-4: 1rem;
  --spacing-5: 1.25rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
  --spacing-10: 2.5rem;
  --spacing-12: 3rem;

  /* ---------- Radius ---------- */
  --radius-sm: 0.25rem;
  --radius-md: 0.625rem;
  --radius-lg: 0.875rem;
  --radius-full: 9999px;

  /* ---------- Elevation ---------- */
  --shadow-sm: 0 2px 8px 0 rgb(26 46 39 / 0.04);
  --shadow-md: 0 8px 24px -8px rgb(26 46 39 / 0.12);
  --shadow-lg: 0 18px 48px -20px rgb(26 46 39 / 0.24);

  /* ---------- Layout ---------- */
  --layout-sidebar: 15rem;
  --layout-sidebar-collapsed: 3.5rem;
  --layout-topbar: 3.5rem;
  --layout-page-max: 100%;
  --layout-form-max: 60rem;

  /* ---------- Motion ---------- */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 120ms;
  --duration-base: 180ms;
}
```

---

## Status Color Mapping

Document and transaction statuses appear constantly. Map them consistently — a status badge must mean the same thing on every screen.

| Status | Token |
| --- | --- |
| Draft, Not Submitted, Pending | `neutral` |
| Submitted, Submitting, In Progress, Pending Retry | `info` |
| Approved, Posted, Accepted, Reconciled, Active, Completed, Paid | `success` |
| Warning, Low Stock, Near Expiry, Partial, Awaiting Approval | `warning` |
| Rejected, Failed, Cancelled, Void, Expired, Out of Stock, Communication Failure, Inactive | `danger` |

Token statuses (PRD W-001):

| Token status | Label (Roman Urdu / English) | Token |
| --- | --- | --- |
| `booked` | Booked | `info` |
| `arrived` | Aa gaye / Arrived | `success` |
| `serving` | Chal raha / Now serving | `accent` |
| `done` | Ho gaya / Done | `neutral` |
| `skipped`, `hold` | Skip / Hold | `warning` |
| `no_show` | Aaye nahi / No-show | `danger` |
| `cancelled` | Cancel | `danger` |

Clinic status: `trial` `info` · `active` `success` · `suspended` `danger`.

AI autonomy levels: L1/L2 `info` · L3 `warning` (needs approval) · L4/L5 `accent`.

---

## Dark Mode

Not required for the first phase. When it is added, define the same token names under `@media (prefers-color-scheme: dark)` and a `[data-theme="dark"]` selector. Because components reference tokens rather than values, no component code changes. Do not introduce a component that hardcodes a light-mode assumption.

---

## Rules

1. Never a hex value in a component.
2. Never a raw Tailwind palette class.
3. New token needed? Add it here first, then use it. A one-off value in a component is a defect.
4. Status color comes from the mapping table above — never chosen ad hoc per screen.
5. Touch/kiosk screens use the touch scale. forms and grids use the control and grid scales. Do not mix them.
