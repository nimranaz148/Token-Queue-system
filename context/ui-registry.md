# UI Registry

Living document. Updated after every component is built (the `imprint` skill does this). Read this before building any new component â€” match existing patterns exactly before inventing new ones.

This file is what keeps Clinic Token & Queue SaaS from drifting into many slightly different interpretations of the same layout.

---

## How to Use

Before building any component:

1. Check whether a similar component already exists here.
2. If yes â€” use it. If it needs a variant, add the variant to the existing component; do not fork it.
3. If no â€” build it following `ui-rules.md` and `ui-tokens.md`, then add it here.

After building any component, record: name, file path, purpose, variants, and the exact token classes used.

---

## Component Inventory

| Component | Path | Status |
| --- | --- | --- |
| StatusBadge | `apps/web/src/components/ui/status-badge.tsx` | Production |
| Button | `apps/web/src/components/ui/button.tsx` | Production |
| Input | `apps/web/src/components/ui/input.tsx` | Production |
| FormShell | `apps/web/src/components/form/form-shell.tsx` | Production |
| DataGrid | `apps/web/src/components/grid/data-grid.tsx` | Production |
| LayoutShell | `apps/web/src/components/layout/layout-shell.tsx` | Production |

---

## Components

### StatusBadge
- **Path:** `apps/web/src/components/ui/status-badge.tsx`
- **Purpose:** Consistent semantic status indicator (token states, visit status, active flags).
- **Variants:** `success`, `warning`, `danger`, `info`, `neutral`.
- **Token classes used:** `bg-*-subtle`, `text-*`, `border-*-border`, `rounded-sm`, `text-xs`.
- **Do:** Use semantic status variants exclusively instead of plain text.
- **Don't:** Do not use raw Tailwind colors like `bg-green-500`.

### Button
- **Path:** `apps/web/src/components/ui/button.tsx`
- **Purpose:** Primary interactive trigger for actions and form submissions.
- **Variants:** `primary` (accent), `secondary` (surface), `danger` (destructive), `ghost`.
- **Sizes:** `sm` (h-7), `md` (h-8.5 / 34px), `lg` (h-10).
- **Token classes used:** `bg-accent`, `bg-accent-hover`, `bg-surface`, `border-border`, `text-fg`, `focus-visible:ring-border-focus`.
- **Do:** Limit to one primary button per screen.
- **Don't:** Never hardcode custom hex heights or button background colors.

### Input
- **Path:** `apps/web/src/components/ui/input.tsx`
- **Purpose:** Form text, phone, email, and number input control.
- **Props:** `label`, `error`, `required`, `disabled`, `readOnly`.
- **Token classes used:** `h-8.5`, `bg-surface`, `border-border`, `border-border-focus`, `text-fg`, `placeholder:text-fg-subtle`, `text-danger`.
- **Do:** Provide inline validation error below the field.
- **Don't:** Do not show error messages solely at the top of the form.

### FormShell
- **Path:** `apps/web/src/components/form/form-shell.tsx`
- **Purpose:** Mandated structure for all forms per PRD Â§5.1.
- **Sections:** Title/badge header, Master fields / filters, Detail grid, Summary / totals, Action bar, Audit / status panel.
- **Token classes used:** `max-w-[960px]`, `border-border`, `bg-surface`, `bg-surface-sunken`, `text-fg`.
- **Do:** Follow the mandated 6-slot vertical hierarchy.
- **Don't:** Do not fork or change the order of sections across different forms.

### DataGrid
- **Path:** `apps/web/src/components/grid/data-grid.tsx`
- **Purpose:** Standardized table view with the 4 mandatory UI states.
- **Mandatory states:** `loading` (skeleton), `empty` (with CTA), `error` (with retry button), `unauthorized`.
- **Token classes used:** `bg-surface-sunken`, `text-fg-muted`, `bg-surface-hover`, `bg-surface-active`, `font-mono` (for numbers).
- **Do:** Right-align numeric columns (`numeric: true`) and use status badges in cells.
- **Don't:** Never use a bare loading spinner when fetching table rows.

### LayoutShell
- **Path:** `apps/web/src/components/layout/layout-shell.tsx`
- **Purpose:** Application desktop and mobile responsive layout shell.
- **Features:** Persistent collapsible sidebar (240px expanded, 56px collapsed), 56px sticky topbar, responsive mobile drawer, 24px content padding.
- **Token classes used:** `w-60`, `w-14`, `h-14`, `bg-surface`, `bg-canvas`, `border-border`, `overflow-x-hidden`.
- **Do:** Ensure zero horizontal overflow across mobile (360px) and desktop (1440px).

### Public Token Booking Layout

File: `apps/web/src/app/(public)/c/[slug]/page.tsx`
Last updated: 2026-11-05

| Property | Class |
| --- | --- |
| Background | `bg-canvas`, `bg-surface` |
| Border | `border-border`, `border-accent-border` |
| Border radius | `rounded-lg` for panels and controls; `rounded-full` for status pills |
| Text — primary | `text-fg`, `font-display` for the main heading |
| Text — secondary | `text-fg-muted`, `text-2xs` |
| Spacing | `p-5` to `p-9` in the form panel; `gap-7` between columns |
| Hover state | `hover:bg-surface-hover` |
| Shadow | `shadow-lg` on the form panel; `shadow-sm` on the clinic mark |
| Accent usage | `bg-accent`, `text-accent`, `bg-accent-subtle` |

**Pattern notes:** Keep the clinic identity and Roman Urdu explanation beside the existing booking form on wide screens; stack them above the form on phones. The explanatory queue steps are informational only. Keep the four existing booking fields and booking behavior intact.

### Owner Report Dashboard

File: `apps/web/src/app/(owner)/reports/page.tsx`
Last updated: 2026-11-05

| Property | Class |
| --- | --- |
| Background | `bg-canvas`, `bg-surface` |
| Border | `border-border`, `border-border-strong` |
| Border radius | `rounded-lg` |
| Text — primary | `text-fg`, `font-display` for the page title |
| Text — secondary | `text-fg-muted`, `text-fg-inverse/70` on the accent KPI |
| Spacing | `p-5` for KPI cards; `p-5` to `p-7` for charts |
| Hover state | `hover:-translate-y-0.5`, `hover:shadow-md` |
| Shadow | `shadow-sm`, `shadow-md` on the lead KPI |
| Accent usage | `bg-accent` for the lead KPI; `bg-chart-1` and `bg-chart-2` for the trend bars |

**Pattern notes:** Keep the four PRD KPIs visible before the seven-day trend. The lead KPI may carry the accent surface; all other KPI cards stay neutral. The chart uses theme chart tokens.

### Owner AI Dashboards

Files: `apps/web/src/app/(owner)/daily-brief/page.tsx`, `apps/web/src/app/(owner)/ai/command-center/page.tsx`
Last updated: 2026-11-05

| Property | Class |
| --- | --- |
| Background | `bg-canvas`, `bg-surface` |
| Border | `border-border`, `border-danger-border` for errors |
| Border radius | `rounded-lg` |
| Text — primary | `text-fg`, `font-display` for dashboard headings |
| Text — secondary | `text-fg-muted`, `text-danger` for errors |
| Spacing | `p-4` for KPI cards; `p-6` to `p-8` for brief content |
| Hover state | `hover:-translate-y-0.5`, `hover:shadow-md` on metrics |
| Shadow | `shadow-sm` |
| Accent usage | `text-accent`, semantic `text-success`, `text-warning`, `text-danger` |

**Pattern notes:** Keep AI spend and run outcomes readable as operational metrics. Use semantic status tokens and preserve the existing data, refresh and feedback actions.

### Public Product Homepage

File: `apps/web/src/app/page.tsx`
Last updated: 2026-11-06

| Property | Class |
| --- | --- |
| Background | `bg-canvas`, `bg-surface` |
| Border | `border-border`, `border-accent-border` |
| Border radius | `rounded-lg`, `rounded-md`, `rounded-full` |
| Text — primary | `text-fg`, `font-display`, `text-display` |
| Text — secondary | `text-fg-muted`, `text-2xs` |
| Spacing | `px-5` to `px-10`; sections use `py-20` to `py-28` |
| Hover state | `hover:-translate-y-0.5`, `hover:bg-accent-hover` |
| Shadow | `shadow-sm`, `shadow-md`, `shadow-lg` |
| Accent usage | `bg-accent`, `text-accent`, `bg-accent-subtle`, semantic `bg-success-subtle` |

**Pattern notes:** Public home uses editorial display type, warm paper background, botanical teal and code-native product previews. Clearly label illustrative token numbers and dashboard metrics as samples. Keep the primary action pointed to `/login`; patient booking remains clinic-specific.

### Doctor Consultation Dashboard

File: `apps/web/src/app/(doctor)/doctor/page.tsx`
Last updated: 2026-11-06

| Property | Class |
| --- | --- |
| Background | `bg-canvas`, `bg-surface`, `bg-accent-subtle` for token number |
| Border | `border-border`, `border-accent-border`, semantic status borders |
| Border radius | `rounded-2xl` for active patient and queue panels; `rounded-xl` for controls |
| Text - primary | `text-fg`, `font-display` for title, `font-mono` for token numbers |
| Text - secondary | `text-fg-muted`, `text-accent` for active queue labels |
| Spacing | `p-5` to `p-8` for active consultation; `p-3.5` for waiting patients |
| Hover state | `hover:bg-surface-hover` for waiting patient rows |
| Shadow | `shadow-sm`, `shadow-md` on the active consultation |
| Accent usage | Queue counts use semantic status surfaces; NEXT stays the primary action |

**Pattern notes:** Keep the active consultation and NEXT action visually dominant. Present current token, patient details, note field, then skip/hold actions. The next-in-line list and recall queue stay secondary. Preserve the F-007 role guard and queue actions.

### Platform Overview Dashboard

File: `apps/web/src/app/(admin)/admin/overview/page.tsx`
Last updated: 2026-11-06

| Property | Class |
| --- | --- |
| Background | `bg-canvas`, `bg-surface`, `bg-accent` for active-clinic KPI |
| Border | `border-border`, semantic `border-warning-border` |
| Border radius | `rounded-2xl` for dashboard panels; `rounded-lg` for controls |
| Text - primary | `text-fg`, `font-display` for title, `font-mono` for metrics |
| Text - secondary | `text-fg-muted`, `text-fg-inverse/75` on the lead KPI |
| Spacing | Active-clinic KPI spans 4/12 columns; other metrics span 2/12 |
| Hover state | `hover:bg-surface-hover` for clinic rows |
| Shadow | `shadow-sm`, `shadow-md` on the lead KPI |
| Accent usage | Active clinics use accent; idle clinics use warning; token metrics use chart/info colors |

**Pattern notes:** Use active clinics as the network focal point, compact D-002 metrics beside it, and the clinic roster below. Preserve platform-wide scope, clinic status, search, refresh, and new-clinic action.

### Dashboard Visual Pass

Files: `apps/web/src/app/(owner)/reports/page.tsx`, `apps/web/src/app/(owner)/ai/command-center/page.tsx`
Last updated: 2026-11-06

The owner report gives patients seen the focal accent surface; supporting KPIs use restrained semantic surfaces and the seven-day chart uses theme chart tokens. The AI Command Center gives AI calls the focal panel, with failures, fallback, cost, and feedback in compact status tiles. Both keep existing filters, data, refresh, export, and report actions.
