# design-system.md standard

`docs/ui-ux/design-system.md`. These top-level sections, in this order (the validator checks the headings).

## 1. Direction
Mood in three words, the audience, what this brand is not, and the signature idea (one memorable visual or motion move). Source: PRD plus the confirmed proposal.

## 2. Motion level
One of `cinematic`, `refined`, `minimal`, exactly as the user chose, with a one-line reason. See `motion-levels.md` for what each level must specify.

## 3. Colour tokens
A table: token, value, role, and the contrast ratio for each text/background pair that is used. Body text on its background meets WCAG AA (4.5:1) at minimum; large text 3:1; non-text UI 3:1. Accent colours state where they may and may not appear. A dark-surface variant is specified if the design uses one.

## 4. Typography
Display, body, mono and (rarely) serif faces with licence and self-hosting plan (free for commercial use or paid, stated). A fluid type scale with sizes, line heights and tracking per step. Rules: one `h1` per page, prose measure about 62 to 70 characters, `text-wrap: balance` on headings, tabular numerals where numbers align. Not a default system stack unless the brief asks for it.

## 5. Spacing and grid
Column count, outer margin, gutter, maximum width, the spacing scale, section rhythm, and the radius budget. State what is deliberately broken (asymmetry, bleed) and where.

## 6. Motion language
Easing tokens, duration tokens, stagger tokens, and the pattern catalogue for the chosen level (name, where used, technique, mobile fallback, reduced-motion fallback). Every pattern states its purpose: arrival, emphasis, transition or spatial continuity.

## 7. Components
Rules shared by all components: states, focus ring, form controls, buttons (one primary style), cards (or why there are none), icons, toasts.

## 8. Accessibility and performance budgets
Written as numbers a lane can check. Accessibility: contrast, keyboard operation, visible focus, `prefers-reduced-motion` honoured, no content only reachable by hover. Performance: animate only `transform`, `opacity`, `clip-path`; maximum hero image bytes; maximum JavaScript (gzip) for the first route; LCP, CLS and INP targets; fonts do not block first paint; 3D loads after first paint and has a static fallback. State which verify lane or tool enforces each (for example a Lighthouse CI lane).

## 9. Skills used
A table of the installed skills actually used (id, source, what it was used for). If a role had no skill available, say so.
