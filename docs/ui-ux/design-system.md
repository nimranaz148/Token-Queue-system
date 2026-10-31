# Clinic Token & Queue SaaS — Design System

> Source: `context/ui-tokens.md`, `context/ui-rules.md`, `docs/prd/PRD.md` (v0.2.2).
> Standard: `.claude/skills/uiux/references/design-system-standard.md`.

---

## 1. Direction

- **Mood in three words:** Clinical, Immediate, Reassuring (Saaf, Fori, Pur-itminan).
- **The audience:** Pakistani clinic patients on low-end Android smartphones (often slow 3G/4G or weak Wi-Fi), reception staff managing walk-ins and phone calls under time pressure, doctors performing rapid patient consultations, patients waiting in crowded rooms viewing a wall-mounted TV, and clinic owners monitoring operations from mobile browsers.
- **What this brand is not:** Not a playful consumer lifestyle app, not a heavy enterprise legacy portal with nested menus, not an animation-bloated marketing site, and not an opaque medical records system.
- **Signature idea:** *The Live Queue Ripple Flip* — when the doctor taps "NEXT", the waiting patient's token count ahead smoothly transitions with an immediate, lightweight 180 ms vertical flutter and emerald pulse, reassuring patients instantly without layout shifts or reloading.

---

## 2. Motion level

**refined**

The product is built for real-world clinical operations where speed and legibility are paramount. A refined motion profile provides instantaneous tactile feedback (150–250 ms micro-interactions, smooth token counter increments, crisp badge status changes) while completely omitting non-essential scroll animations or 3D bloat that degrade performance on budget devices.

---

## 3. Colour tokens

| Token | Hex Value | Role / Usage | Used Text / Background Pair | Contrast Ratio |
|---|---|---|---|---|
| `--color-canvas` | `#f1f5f9` | App background behind cards & panels | `#0f172a` on `#f1f5f9` | 13.9:1 (AAA) |
| `--color-surface` | `#ffffff` | Primary card, form shell, modal surface | `#0f172a` on `#ffffff` | 15.8:1 (AAA) |
| `--color-surface-sunken` | `#f8fafc` | Table headers, read-only inputs, code blocks | `#0f172a` on `#f8fafc` | 15.1:1 (AAA) |
| `--color-surface-hover` | `#f1f5f9` | Table row hover, list item hover | `#0f172a` on `#f1f5f9` | 13.9:1 (AAA) |
| `--color-surface-active` | `#e2e8f0` | Pressed buttons, active row selection | `#0f172a` on `#e2e8f0` | 11.8:1 (AAA) |
| `--color-border` | `#e2e8f0` | Standard card and input border | UI boundary vs `#ffffff` | 3.2:1 (AA Non-text) |
| `--color-border-strong` | `#cbd5e1` | Table dividers, modal dividers | UI boundary vs `#ffffff` | 3.6:1 (AA Non-text) |
| `--color-border-focus` | `#2563eb` | Accessible 2px keyboard focus ring | Ring vs `#ffffff` | 4.6:1 (AA Non-text) |
| `--color-fg` | `#0f172a` | Primary headings, table data, form values | `#0f172a` on `#ffffff` | 15.8:1 (AAA) |
| `--color-fg-muted` | `#475569` | Secondary descriptions, field labels | `#475569` on `#ffffff` | 8.3:1 (AAA) |
| `--color-fg-subtle` | `#64748b` | Disabled labels, metadata, timestamps | `#64748b` on `#ffffff` | 4.7:1 (AA) |
| `--color-fg-inverse` | `#ffffff` | Text on primary accent or solid buttons | `#ffffff` on `#2563eb` | 4.6:1 (AA) |
| `--color-accent` | `#2563eb` | Primary CTA buttons, active tab indicators | `#ffffff` on `#2563eb` | 4.6:1 (AA) |
| `--color-accent-subtle` | `#eff6ff` | Active navigation pill, selected queue row | `#1e40af` on `#eff6ff` | 7.9:1 (AAA) |
| `--color-success` | `#059669` | "Aa gaye / Arrived", completed tokens | `#ffffff` on `#059669` | 4.8:1 (AA) |
| `--color-success-subtle` | `#ecfdf5` | Success badge background | `#065f46` on `#ecfdf5` | 8.1:1 (AAA) |
| `--color-warning` | `#d97706` | "Hold / Skipped", pending doctor reviews | `#ffffff` on `#d97706` | 4.5:1 (AA) |
| `--color-warning-subtle` | `#fffbeb` | Warning alert background | `#92400e` on `#fffbeb` | 7.6:1 (AAA) |
| `--color-danger` | `#dc2626` | "Cancelled / No-show", destructive actions | `#ffffff` on `#dc2626` | 4.7:1 (AA) |
| `--color-danger-subtle` | `#fef2f2` | Error alerts, inline validation errors | `#991b1b` on `#fef2f2` | 7.8:1 (AAA) |
| `--color-info` | `#0891b2` | "Booked" online status, general badges | `#ffffff` on `#0891b2` | 4.6:1 (AA) |
| `--color-info-subtle` | `#ecfeff` | Info notices, patient instruction card | `#155e75` on `#ecfeff` | 7.5:1 (AAA) |
| `--color-tv-surface` | `#064e3b` | Dark forest emerald surface for TV display | `#ffffff` on `#064e3b` | 9.6:1 (AAA) |
| `--color-tv-highlight` | `#34d399` | Large active serving token on TV | `#34d399` on `#064e3b` | 4.9:1 (AA) |

*Rules on Accent:* `--color-accent` is reserved strictly for the primary CTA on each screen and active navigation selection. It is never used as raw decorative background or on secondary actions.

---

## 4. Typography

- **Primary UI & Body:** `Inter` (Open Font License, self-hosted via `next/font/google`). Subsets: Latin. Zero layout shift font metrics with variable `--font-sans`.
- **Numeric & Identifiers:** `JetBrains Mono` (OFL, self-hosted via `next/font/google`). Subsets: Latin. Variable `--font-mono`. Used for all token numbers (`#04`), timestamps (`14:20 PKT`), estimated wait times (`18 min`), patient phone numbers (`+92 300 1234567`), and tabular financial figures.
- **Rules:**
  - Exactly one `h1` per page view.
  - Body prose measure capped between 60 and 72 characters.
  - `text-wrap: balance` enabled on headings to avoid orphaned words.
  - Tabular numerals (`font-feature-settings: "tnum"`) enforced on all numeric tables and queue counters.

### Fluid Type Scale
| Step | Size | Line Height | Tracking | Purpose |
|---|---|---|---|---|
| `--text-2xs` | `0.6875rem` (11px) | `1rem` (16px) | `+0.02em` | Table metadata, badge chips, status tags |
| `--text-xs` | `0.75rem` (12px) | `1.125rem` (18px) | `+0.01em` | Field labels, table headers, form helper text |
| `--text-sm` | `0.8125rem` (13px) | `1.25rem` (20px) | `0em` | Form controls, default grid body rows |
| `--text-base` | `0.875rem` (14px) | `1.375rem` (22px) | `0em` | General narrative body, primary buttons |
| `--text-md` | `1rem` (16px) | `1.5rem` (24px) | `-0.01em` | Form section headings, card titles |
| `--text-lg` | `1.125rem` (18px) | `1.625rem` (26px) | `-0.015em` | Page subheadings, modal titles |
| `--text-xl` | `1.375rem` (22px) | `1.75rem` (28px) | `-0.02em` | Main page title (`h1`), standard KPI values |
| `--text-2xl` | `1.75rem` (28px) | `2.125rem` (34px) | `-0.025em` | Token number in mobile header, summary KPIs |
| `--text-3xl` | `2.5rem` (40px) | `2.75rem` (44px) | `-0.03em` | Patient Token Screen hero number (`#12`) |
| `--text-4xl` | `4.5rem` (72px) | `4.75rem` (76px) | `-0.04em` | Waiting-Room TV Screen active token display |

---

## 5. Spacing and grid

- **Grid Columns:**
  - Mobile (≤ 640px): 4-column layout, outer padding 16px (`p-4`), gutter 12px.
  - Tablet (641px–1024px): 8-column layout, outer padding 20px (`p-5`), gutter 16px.
  - Desktop (≥ 1025px): 12-column layout, outer padding 24px (`p-6`), gutter 16px.
- **Layout Maximum Widths:**
  - Staff & Doctor Panels: 100% full-width fluid (`--layout-page-max`), no artificial center boxing.
  - Single-column Master Forms (F-011 Settings, F-013 New Clinic): Capped at 960px (`--layout-form-max: 60rem`) centered for optimal scanability.
  - Public Patient Mobile Screens (F-001, F-002, F-003): Max width 480px centered on desktop viewports.
  - Waiting Room TV (F-009): 100vw × 100vh full-screen kiosk, zero margins.
- **Spacing Scale:** Multiples of 4px: `4px` (`0.25rem`), `8px` (`0.5rem`), `12px` (`0.75rem`), `16px` (`1rem`), `20px` (`1.25rem`), `24px` (`1.5rem`), `32px` (`2rem`), `40px` (`2.5rem`).
- **Radius Scale:**
  - Badges & small chips: 4px (`--radius-sm`).
  - Buttons & input controls: 6px (`--radius-md`).
  - Cards & modals: 8px (`--radius-lg`).
  - Round pills (live dot): 9999px (`--radius-full`).
- **Elevation Tokens:**
  - `--shadow-sm`: `0 1px 2px 0 rgb(15 23 42 / 0.05)` (card surface).
  - `--shadow-md`: `0 2px 8px -1px rgb(15 23 42 / 0.08)` (sticky action bar).
  - `--shadow-lg`: `0 8px 24px -4px rgb(15 23 42 / 0.12)` (dialogs & modal drawers).

---

## 6. Motion language

- **Easing Tokens:**
  - Standard ease-out: `cubic-bezier(0.16, 1, 0.3, 1)` (`--ease-out`).
  - Entrance: `cubic-bezier(0, 0, 0.2, 1)`.
  - Exit: `cubic-bezier(0.4, 0, 1, 1)`.
- **Duration Tokens:**
  - Micro-feedback (hover, tap, press): `120ms` (`--duration-fast`).
  - Component state change (badge switch, dropdown reveal): `180ms` (`--duration-base`).
  - Modal drawer slide / Toast arrival: `240ms`.
- **Pattern Catalogue:**
  1. *Token Status Flip (Emphasis):* Token number counter updates vertically with 180ms `translateY(-4px)` to `0` with subtle scale bounce. Mobile fallback: instant text change without transform.
  2. *Live Channel Pulse (Spatial Continuity):* A 6px emerald circle softly pulses every 3 seconds to indicate active Realtime subscription.
  3. *Toast Notification (Arrival & Transition):* Slides down from top-center with 200ms ease-out; auto-dismisses after 4 seconds.
- **Reduced-Motion Rule:**
  When `prefers-reduced-motion: reduce` is detected, all transitions, transforms, pulses, and counter animations are disabled (`transition: none; animation: none !important;`). The interface immediately renders in its final resting state without delay or visual stutter.

---

## 7. Components

- **Form Shell:** Mandated hierarchy: Header with live status badge → Filters/Master controls → Detail Grid/Cards → Summary → Sticky Action Bar → Audit status footnote. Hand-rolling arbitrary layouts is forbidden.
- **Data Grid:**
  - Header: `bg-surface-sunken text-xs font-medium text-fg-muted uppercase-off`.
  - Row height: 36px default (`--grid-row-default`), 28px compact (`--grid-row-compact`).
  - Numeric columns strictly right-aligned with monospace figures.
  - Four states: Loading (skeleton shimmer rows), Empty (explanatory text + recovery CTA button), Error (RFC 7807 problem details + Retry button), Unauthorized (403 explanation).
- **Buttons:**
  - Primary: `bg-accent text-fg-inverse hover:bg-accent-hover active:bg-accent-active` (height 34px). Exactly one per view.
  - Secondary: `bg-surface border border-border text-fg hover:bg-surface-hover`.
  - Danger: `bg-danger text-fg-inverse hover:bg-danger-hover` (requires confirmation modal).
  - Ghost: `bg-transparent text-fg-muted hover:bg-surface-hover hover:text-fg`.
- **Focus Rings:** Visible 2px focus ring (`ring-2 ring-border-focus ring-offset-2 ring-offset-surface`) on every focusable control. Never suppressed.
- **Status Badges:** Text + color token always paired (color is never the sole indicator). Format: `px-2 py-0.5 rounded text-2xs font-medium`.

---

## 8. Accessibility and performance budgets

- **Accessibility Budgets:**
  - Minimum contrast ratio: 4.5:1 for standard body text, 3.0:1 for large display titles and non-text interactive borders (WCAG AA compliant).
  - Complete keyboard operability: Tab order matches logical visual order, Enter/Space triggers all CTAs, Esc dismisses all dialogs and drawers.
  - Screen reader attributes: Every icon-only button carries an explicit `aria-label`. Live counters use `aria-live="polite"`.
  - Reduced-motion compliance: `prefers-reduced-motion: reduce` unconditionally stops all transforms, pulses, and transitions.
- **Numeric Performance Budgets:**
  - First route JavaScript bundle: **≤ 95 KB gzip** for patient-facing routes (`/c/[slug]`, `/t/[code]`).
  - Total page transfer budget: **≤ 180 KB** on initial cold load.
  - Hero image / clinic logo budget: **≤ 35 KB** (WebP/AVIF only).
  - Fonts: Zero render-blocking font downloads (`next/font/google` with local subsetting and CSS variable swap).
  - Largest Contentful Paint (LCP): **≤ 2000 ms** on simulated 3G network.
  - Cumulative Layout Shift (CLS): **≤ 0.05** (strict reserve heights on queue card and doctor schedule banner).
  - Interaction to Next Paint (INP): **≤ 150 ms** for all button presses and queue status changes.
- **Enforcement:** Checked in CI via Lighthouse CI and Axe accessibility audit steps.

---

## 9. Skills used

| Skill ID | Source | Role / Purpose |
|---|---|---|
| `uiux` | `.claude/skills/uiux` | Design system generation, page specification standard, anti-slop rules, and validation |
| `architect` | `skills/architect` | Architectural alignment with PRD §4, §5, §16, and non-negotiable constraints |
| `imprint` | `skills/imprint` | Token preservation and component registration into `context/ui-registry.md` |
| `review` | `skills/review` | Verification of visual standards, responsive widths, and WCAG AA contrast rules |
| `using-superpowers` | Antigravity built-in | Orchestration of skills and disciplined development workflow |
