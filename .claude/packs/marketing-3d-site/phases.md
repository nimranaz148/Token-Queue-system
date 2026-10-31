# Marketing site, cinematic and 3D-forward — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- Design system and page documents (run /uiux) — Accept: design-system.md and one document per page pass check_uiux.py
- Scaffold the site with the framework, fonts, tokens and smooth-scroll provider — Accept: Builds; reduced-motion renders the final state of every section
- Asset pipeline for images, video and 3D — Accept: Every asset has a budget and a fallback; the build fails if a budget is exceeded
- Performance and accessibility lane — Accept: A Lighthouse or equivalent lane runs in CI against the preview URL with the budgets from the design system

## Phase 1

- Home page with the hero treatment and scroll storytelling — Accept: Meets the budgets on a throttled CPU; mobile and reduced-motion variants verified
- Remaining pages from their documents — Accept: Each page matches its document; the checklist items for that page are ticked
- Contact or quote form with email delivery — Accept: A test submission arrives; spam protection blocks an automated post
- SEO and share metadata, sitemap, robots — Accept: Every page has unique metadata; sitemap lists public pages only

## Deferred

- Headless CMS — Trigger: A non-technical editor must change content weekly
- Real-time WebGL beyond the hero — Trigger: The core experience depends on interacting with a 3D object and the device budget allows it
- Multi-language site — Trigger: A second market is committed
- A/B tests on the hero — Trigger: Enough traffic to reach significance in two weeks
