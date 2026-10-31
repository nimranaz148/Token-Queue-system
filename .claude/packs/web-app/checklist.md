# Web application — checklist

Every item must be answered in the PRD before Phase 1 exits. Each becomes a requirement and a candidate acceptance test.

- [ ] C-WA-01 Every protected page and every API route checks the user and role on the server, not only in the UI; one test per role proves a 403.
- [ ] C-WA-02 Session expiry, refresh and logout are defined and tested, including what the user sees when a session ends mid-form.
- [ ] C-WA-03 All input is validated on the client for feedback and again on the server for safety; the same rules are shared, not copied.
- [ ] C-WA-04 Every list and screen has designed loading, empty and error states.
- [ ] C-WA-05 Forms cannot be double-submitted; a repeated submit is safe.
- [ ] C-WA-06 Keyboard-only use works on every page: logical focus order, visible focus, no keyboard traps; forms have labels and linked error messages.
- [ ] C-WA-07 Layouts work at 360 px, tablet and desktop widths without horizontal scroll.
- [ ] C-WA-08 Every page has a title, a description, one h1 and a canonical URL; public pages appear in the sitemap; private pages are noindex.
- [ ] C-WA-09 Security headers and a content security policy are set; cookies are HttpOnly, Secure and SameSite; state-changing requests are protected against CSRF.
- [ ] C-WA-10 Rate limiting protects sign-in, password reset and any public form.
- [ ] C-WA-11 No secret reaches the browser bundle; environment files are separated per environment and `.env.example` lists every variable.
- [ ] C-WA-12 Image, font and JavaScript budgets are written down as numbers and checked in a lane.
- [ ] C-WA-13 Errors are captured with a request or session id and without personal data.
- [ ] C-WA-14 404 and 500 pages exist and keep the navigation usable.
