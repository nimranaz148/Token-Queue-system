# UI Rules

Rules for building Clinic Token & Queue SaaS UI. The PRD is the functional source of truth for information hierarchy, fields and actions. These rules keep every screen consistent.

**Reference the feature/form ID in every UI task.** Never invent business fields.

---

## Font

Import Inter via `next/font/google` in the root layout.

```tsx
import { Inter } from "next/font/google";
const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
```

Apply the variable class to `<html>`. Never use system fonts as the primary face.

Use `--font-mono` for: barcodes, SKUs, document numbers, IMEI/serials, and any column of aligned figures.

---

## Layout

- **Full width.** App screens use all available width — no centered max-width page container.
- Sidebar: 240px expanded, 56px collapsed. Persistent, module navigation.
- Topbar: 56px. Contains company/branch switcher, global search, notifications, user menu.
- Content padding: 24px.
- Gap between page sections: 16px.
- Single-column master forms cap at 960px (`--layout-form-max`) for readability. Grids and dashboards do not cap.

---

## The Mandated Form Layout 

**Every** form follows this order. No exceptions.

```
┌──────────────────────────────────────────────┐
│ Header / Title          [status badge]       │
├──────────────────────────────────────────────┤
│ Filters  or  Master fields                   │
├──────────────────────────────────────────────┤
│ Detail grid                                  │
├──────────────────────────────────────────────┤
│ Totals / summary                             │
├──────────────────────────────────────────────┤
│ Actions (action bar)                         │
├──────────────────────────────────────────────┤
│ Audit / status panel                         │
└──────────────────────────────────────────────┘
```

Master-only forms (Company, Branch, Warehouse) omit the detail grid and totals. They keep everything else, including the audit panel.

The `FormShell` component in `components/form/` implements this. Compose it — never hand-roll the layout.

---

## Data Grid

The single most-used component in the product. Built once, used everywhere .

**Every grid must have:** pagination, search/filter, sortable columns, column visibility, export where specified, and all four states — loading (skeleton rows, not a spinner), empty (with the action that resolves it), error (with retry), unauthorized.

- Default row height 36px. Compact 28px for dense transaction lists. Comfortable 44px only where rows carry two lines.
- Header row: `bg-surface-sunken`, `text-xs`, `font-medium`, `text-fg-muted`, uppercase off.
- Body text `text-sm`.
- Row hover `bg-surface-hover`; selected `bg-surface-active`.
- **Numeric columns right-aligned.** Always. Money, quantity, percentage.
- Dates left-aligned, formatted per company configuration.
- Status renders as a badge, never as raw text.
- Row actions in a trailing column — icon buttons for the top two actions, overflow menu beyond that.
- Server-side pagination by default. Client-side only for lists known to stay small.
- Sticky header on scroll. Sticky first column on wide financial grids.

---

## Forms & Validation

- Labels above inputs. `text-xs`, `text-fg-muted`, `font-medium`.
- Required fields marked with a `text-danger` asterisk after the label .
- Default control height 34px (`--control-md`).
- **Inline validation** — the message sits directly below the field it concerns, `text-xs text-danger` . Never only a summary at the top; a summary may accompany inline messages but never replace them.
- Validate on blur, revalidate on change once a field has errored. Never validate on first keystroke.
- Read-only fields use `bg-surface-sunken` with a normal border — visibly inert, still legible.
- Disabled controls use `text-fg-subtle` and `cursor-not-allowed`.
- Field groups get a section heading (`text-md`, `font-semibold`) with a 24px gap above.
- Lookup fields (product, customer, supplier, account) always open the standard search dialog. Never a plain select for a large master list.

---

## Actions & Authorization

- **Unauthorized actions are hidden or disabled** . Prefer hidden for navigation, disabled with a tooltip for in-context actions where absence would be confusing.
- The API rejects unauthorized actions regardless of UI state. UI hiding is convenience, never security.
- Action bar sits below the form content, right-aligned, primary action rightmost.
- One primary action per screen. Everything else is secondary or ghost.
- **Destructive actions require confirmation** . The dialog names the specific record and what will happen.
- **Posted financial and inventory transactions expose no Edit or Delete** . Offer Reverse or Amend instead, and only to authorized roles.
- Every transaction form displays document status and posting state prominently in the header .

---

## Buttons

| Variant | Use |
| --- | --- |
| Primary | `bg-accent text-fg-inverse` — the one main action |
| Secondary | `bg-surface border-border text-fg` — supporting actions |
| Ghost | transparent, `text-fg-muted` — tertiary, toolbar, icon buttons |
| Danger | `bg-danger text-fg-inverse` — destructive, confirmed |

Heights: 28px small, 34px default, 40px large. Touch/kiosk screens use the touch scale instead.

---

## Feedback

- Success and error notifications must be **actionable**  — say what happened and what to do next. "Failed to save" is not acceptable; "Could not save branch: code BR-01 is already in use" is.
- Toast for transient success. Inline alert for errors that need a decision. Modal only for blocking confirmation.
- Never leave a mutation without feedback.
- Optimistic updates are forbidden for financial and inventory operations. Wait for the server.

---

## Dashboards 

- KPI cards in a row at the top. Value `text-xl`/`text-2xl`, label `text-xs text-fg-muted`, trend indicator using `positive`/`negative` tokens.
- **Every KPI drills down** to a filtered report or transaction list . A KPI that is not clickable is incomplete.
- Filters at the top affect **all** widgets on the page consistently.
- Every dashboard is permission-aware and company/branch scoped . Users see only authorized data.
- Dashboard values must reconcile with source reports — same endpoint, same calculation.
- Chart colors from `--color-chart-1..6`. Never a library default palette.
- Loading and error states handled per widget, not per page — one slow widget must not blank the dashboard.
- Mobile dashboard (§29.6) must be usable on phone screens.

---

## States — All Four, Every Time

Every data-bound view implements:

| State | Requirement |
| --- | --- |
| Loading | Skeleton matching the real layout. Not a centered spinner |
| Empty | Explain why it is empty and offer the action that fixes it |
| Error | Say what failed, offer retry. Never expose stack traces or SQL |
| Unauthorized | Explain that access is restricted. Never a blank screen or a 404 |

---

## Formatting

All formatting goes through `lib/format` using **company configuration**  — currency, date format, quantity precision, rounding. Never `toLocaleString` inline, never a hardcoded currency symbol, never a hardcoded date format.

- Money: right-aligned, mono figures, currency per company, negative values in `--color-negative` with parentheses in financial reports.
- Quantities: precision per unit definition.
- Dates: company format; timestamps rendered in company timezone from UTC storage.

---

## Responsive

- Desktop and tablet are both mandatory and both tested .
- Sidebar collapses to icons below 1280px, to a drawer below 1024px.
- Grids scroll horizontally inside their own container below their minimum width — the page body never scrolls horizontally.
- Touch/kiosk screens are designed tablet-first.
- Owner Mobile Dashboard (§29.6) is the only phone-targeted screen in scope.

---

## Accessibility

- Visible focus ring on every interactive element (`--color-border-focus`), never removed.
- Full keyboard navigation — mandatory for operator efficiency , useful for everyone.
- Status is never communicated by color alone. Badges carry text.
- Labels are associated with controls. Icon-only buttons carry `aria-label`.
- Meet WCAG AA contrast. The provisional palette does; verify again after the §33 branding pass.

---

## Before Building Any Component

1. Check `ui-registry.md` — if it exists, use it and match its classes exactly.
2. If it does not exist, build it from these rules and `ui-tokens.md`.
3. Register it in `ui-registry.md` immediately, with file path and classes.
4. Verify against the PRD's screen definition for the corresponding feature ID.
5. Check it against the UI acceptance checklist .
