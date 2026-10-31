# Page document standard

One file per page: `docs/ui-ux/<page>/<page>.md`. Eleven numbered sections, in this order, with these exact headings (the validator checks them). A section that does not apply says `Not applicable — <reason>`; it is never deleted.

## 1. Page overview
Purpose of the page, the visitor it serves, the one action it must drive, the PRD sections and IDs it implements (for example F-004), and how a visitor arrives.

## 2. Section-by-section breakdown
A numbered list of every section top to bottom, one line each: name, job (arrival, proof, explanation, conversion), and its background (paper, ink, night).

## 3. Content
The real text for every section: headline, supporting copy, labels, button text, form field labels. Copy taken from the PRD is cited; anything the client has not provided is marked `[CLIENT TO CONFIRM]`. Never lorem ipsum.

## 4. Layout structure
Grid usage per section (columns, offsets, bleed), spacing rhythm using the design-system scale, and the responsive behaviour at three widths (mobile, tablet, desktop).

## 5. Component breakdown
Each component, its states (default, hover, focus, active, disabled, loading, error, empty), and whether it exists already in `context/ui-registry.md` (reuse) or is new.

## 6. Visual hierarchy
What the eye sees first, second, third on each screen width, and how scale, weight, colour and space produce that order. One focal point per viewport.

## 7. CTAs
Every call to action: label, position, primary or secondary, destination or action, and the success state. A page has one primary CTA style.

## 8. Media
Every image, video and 3D asset: purpose, aspect ratio, maximum bytes, format (AVIF/WebP, video codec), alt text or the reason it is decorative, and the loading strategy (priority only above the fold, lazy elsewhere). 3D assets name their fallback.

## 9. Interactions
Every motion and interaction: trigger, what changes, which motion token (easing and duration), the purpose (arrival, emphasis, transition or spatial continuity), the mobile variant and the reduced-motion variant. At the cinematic level: hero treatment, scroll storytelling, reveals, page transition, 3D usage.

## 10. Diagram
An ASCII wireframe of the page at desktop width, and a short mermaid flow of the visitor's path to the primary CTA. Field and section names match sections 2 and 3 exactly.

## 11. Notes
Implementation notes, performance risks for this page, accessibility notes (focus order, landmarks, form errors), SEO notes (title, description, headings), and open questions.
