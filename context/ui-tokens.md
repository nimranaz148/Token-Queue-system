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

- Neutral slate ground so status colors carry all the signal
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

  /* ---------- Page and surface backgrounds ---------- */
  --color-canvas: #f1f5f9;          /* app background behind panels */
  --color-surface: #ffffff;          /* cards, panels, form shells */
  --color-surface-raised: #ffffff;   /* modals, popovers, dropdowns */
  --color-surface-sunken: #f8fafc;   /* grid headers, read-only fields */
  --color-surface-hover: #f1f5f9;    /* row and menu hover */
  --color-surface-active: #e2e8f0;   /* pressed, selected row */

  /* ---------- Borders ---------- */
  --color-border: #e2e8f0;           /* default panel and input border */
  --color-border-strong: #cbd5e1;    /* grid cell dividers, separators */
  --color-border-focus: #2563eb;     /* focus ring */

  /* ---------- Text ---------- */
  --color-fg: #0f172a;               /* primary text, grid values */
  --color-fg-muted: #475569;         /* labels, secondary text */
  --color-fg-subtle: #94a3b8;        /* placeholders, disabled, meta */
  --color-fg-inverse: #ffffff;       /* text on accent/solid fills */

  /* ---------- Accent (primary action) ---------- */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-active: #1e40af;
  --color-accent-subtle: #eff6ff;    /* active nav background, selected tint */
  --color-accent-border: #bfdbfe;

  /* ---------- Semantic status ---------- */
  --color-success: #059669;
  --color-success-subtle: #ecfdf5;
  --color-success-border: #a7f3d0;

  --color-warning: #d97706;
  --color-warning-subtle: #fffbeb;
  --color-warning-border: #fde68a;

  --color-danger: #dc2626;
  --color-danger-hover: #b91c1c;
  --color-danger-subtle: #fef2f2;
  --color-danger-border: #fecaca;

  --color-info: #0891b2;
  --color-info-subtle: #ecfeff;
  --color-info-border: #a5f3fc;

  --color-neutral: #64748b;
  --color-neutral-subtle: #f1f5f9;
  --color-neutral-border: #cbd5e1;

  /* ---------- Financial figures ---------- */
  --color-positive: #059669;         /* credits, gains, in-stock */
  --color-negative: #dc2626;         /* debits, losses, negative stock */

  /* ---------- Charts (dashboards) ---------- */
  --color-chart-1: #2563eb;
  --color-chart-2: #0891b2;
  --color-chart-3: #7c3aed;
  --color-chart-4: #d97706;
  --color-chart-5: #059669;
  --color-chart-6: #db2777;
  --color-chart-grid: #e2e8f0;
  --color-chart-axis: #94a3b8;

  /* ---------- Type scale ---------- */
  --text-2xs: 0.6875rem;   /* 11px — grid meta, badges */
  --text-xs: 0.75rem;      /* 12px — labels, table headers, captions */
  --text-sm: 0.8125rem;    /* 13px — GRID AND FORM DEFAULT */
  --text-base: 0.875rem;   /* 14px — body, buttons */
  --text-md: 1rem;         /* 16px — section headings */
  --text-lg: 1.125rem;     /* 18px — page titles */
  --text-xl: 1.375rem;     /* 22px — KPI values */
  --text-2xl: 1.75rem;     /* 28px — large KPI, headline totals */
  --text-3xl: 2.25rem;     /* 36px — grand total */

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
  --radius-sm: 0.25rem;    /* inputs, badges */
  --radius-md: 0.375rem;   /* buttons, cards */
  --radius-lg: 0.5rem;     /* panels, modals */
  --radius-full: 9999px;

  /* ---------- Elevation ---------- */
  --shadow-sm: 0 1px 2px 0 rgb(15 23 42 / 0.05);
  --shadow-md: 0 2px 8px -1px rgb(15 23 42 / 0.08);
  --shadow-lg: 0 8px 24px -4px rgb(15 23 42 / 0.12);
  --shadow-popover: 0 4px 16px -2px rgb(15 23 42 / 0.14);

  /* ---------- Layout ---------- */
  --layout-sidebar: 15rem;         /* 240px expanded */
  --layout-sidebar-collapsed: 3.5rem;
  --layout-topbar: 3.5rem;         /* 56px */
  --layout-page-max: 100%;         /* dense app: full width, no centered max */
  --layout-form-max: 60rem;        /* 960px for single-column master forms */

  /* ---------- Data grid density ---------- */
  --grid-row-compact: 1.75rem;     /* 28px */
  --grid-row-default: 2.25rem;     /* 36px */
  --grid-row-comfortable: 2.75rem; /* 44px */
  --grid-header: 2.25rem;
  --grid-cell-px: 0.75rem;

  /* ---------- Form controls ---------- */
  --control-sm: 1.75rem;           /* 28px */
  --control-md: 2.125rem;          /* 34px — DEFAULT for forms */
  --control-lg: 2.5rem;            /* 40px */

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
