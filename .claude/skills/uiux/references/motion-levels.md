# Motion levels

The level is chosen in the PRD interview (or here, if the PRD did not). The user decides; the recommendation below is a default, not a rule.

| Level | Recommended for | Not for |
| --- | --- | --- |
| **cinematic** (3D-forward, scroll-driven storytelling) | marketing and brand sites, launches, portfolios, anything judged on first impression | dense admin tools, data entry, dashboards |
| **refined** (purposeful reveals, smooth scroll, micro-interactions) | most product sites, SaaS marketing, content sites | when the audience is on weak devices and the budget is tight |
| **minimal** (state changes only, no scroll effects) | admin panels, dashboards, internal tools, accessibility-first products | brand sites that need to stand out |

## What each level must specify

**Cinematic** — per page: the hero treatment; scroll storytelling (pinned sections, parallax layers, text and image reveals); page transitions; where 3D is used, what it is built with (Three.js or WebGL, or pre-rendered video/frame sequence), when it loads (after first paint), and its static fallback; easing, duration and stagger tokens; the mobile variant (pins and horizontal scroll become vertical staggered reveals; parallax at most 8px); the reduced-motion variant (final state, no scrubbing, no autoplay, same content). Typical tools: GSAP with ScrollTrigger, Lenis smooth scroll, SplitText-style line and word reveals, clip-path wipes, Three.js.

**Refined** — the pattern catalogue (reveal, stagger, hover and focus feedback, count-up, scroll-aware nav), tokens, mobile and reduced-motion variants. No pinned multi-screen sequences.

**Minimal** — transition and feedback timings only (about 150 to 250 ms), skeleton and loading states, focus and validation feedback. No decorative motion.

## Rules at every level

- Animate only `transform`, `opacity` and `clip-path`. Never animate layout properties.
- `will-change` only while animating. Revert split text after its reveal.
- `prefers-reduced-motion: reduce` removes motion and keeps content and layout identical.
- Below the fold, create triggers lazily. The first route has a stated JavaScript budget.
- Every motion states its purpose: arrival, emphasis, transition or spatial continuity.
- The slow path is real: test on a throttled CPU and a small viewport before calling a page done.
