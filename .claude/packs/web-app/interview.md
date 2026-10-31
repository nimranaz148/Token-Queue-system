# Web application — technical interview

Ask only what changes the build. Each question carries a recommendation and a free-tier default; the user answers yes or names a change.

## Q1. Which front-end framework?

- **Recommend:** Next.js (App Router) with TypeScript: one codebase for pages, API routes and server rendering, and the largest skill ecosystem.
- **Free default:** Vercel hobby tier or any Node host; no paid tool needed.

## Q2. Rendering model: server-rendered, static, or client-only?

- **Recommend:** Server-render public and data-heavy pages, client-render only interactive islands; static where content rarely changes.
- **Free default:** Static export on a free host when there is no per-user data.

## Q3. Who signs users in?

- **Recommend:** A managed auth provider for the MVP (less security code to own); self-hosted only if the PRD forbids a third party.
- **Free default:** Free tier of the provider; migrate when the user count or price changes.

## Q4. Accessibility target and supported browsers/devices?

- **Recommend:** WCAG 2.2 AA, last two versions of evergreen browsers, mobile from 360 px wide.
- **Free default:** Automated checks (axe) in the fast tier; manual keyboard pass per page.

## Q5. Does the product need other languages or right-to-left layout?

- **Recommend:** Only if the PRD names a second market; otherwise English only and keep strings out of components so i18n can be added later.
- **Free default:** No i18n library until a second language is real.

## Q6. Analytics and error monitoring?

- **Recommend:** One error monitor and one privacy-friendly analytics tool; no tracking that needs a consent banner unless the PRD requires it.
- **Free default:** Free tiers.

