# UI Registry

Living document. Updated after every component is built (the `imprint` skill does this). Read this before building any new component — match existing patterns exactly before inventing new ones.

This file is what keeps Clinic Token & Queue SaaS from drifting into many slightly different interpretations of the same layout.

---

## How to Use

Before building any component:

1. Check whether a similar component already exists here.
2. If yes — use it. If it needs a variant, add the variant to the existing component; do not fork it.
3. If no — build it following `ui-rules.md` and `ui-tokens.md`, then add it here.

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
- **Purpose:** Mandated structure for all forms per PRD §5.1.
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
