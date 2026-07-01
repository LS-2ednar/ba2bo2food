# Frontend — ba2bo2food

Companion to ARCHITECTURE.md's choice of server-rendered Jinja2 over
FastAPI. This document covers everything specific to what the user sees
and touches: styling, interactivity, layout priority, and language.

## 1. Rendering approach

No SPA, no frontend build step. Every page is server-rendered HTML from
Jinja2 templates (`app/templates/`). Interactivity beyond plain form
submissions is added with **htmx** (`app/static/htmx.min.js`, vendored —
no CDN dependency, matching the local/self-hosted deployment target):

- Server endpoints return small HTML fragments (not JSON) for htmx to
  swap into the page.
- Two current use cases (API.md): adding a blank ingredient row while
  writing a recipe, and toggling a shopping-list item's checked state
  without a full page reload. Ingredient *autocomplete* itself is a plain
  HTML `<datalist>` rendered with the form (no round-trip needed at the
  scale of one household's ingredient list).
- Default to plain forms/links first; reach for htmx only where a full
  page reload would be annoyingly slow or would lose scroll position
  (e.g. checking off items while scrolling a long shopping list).

## 2. Styling

[Pico.css](https://picocss.com/) (classless/minimal): write semantic HTML
(`<article>`, `<nav>`, `<table>`, standard form elements) and get a
reasonably polished look with little custom CSS. A small
`app/static/custom.css` layers on top for the few things Pico doesn't
cover (e.g. the plate-ratio visual in §5, checked-off shopping list item
styling).

No component library, no CSS build step (no Sass/PostCSS/Tailwind
pipeline) — one stylesheet, vendored Pico, done.

## 3. Layout priority: mobile-first

Designed for a phone screen first, then scaled up:

- Single-column layouts by default; multi-column (e.g. a 7-day plan grid)
  only introduced at wider breakpoints via CSS `min-width` media queries.
- Primary navigation is a **bottom tab bar on mobile** (Plan, Recipes,
  Shopping List, Profile) that becomes a **top nav bar on desktop**
  widths — implemented as one `<nav>` restyled by media query, not two
  separate templates.
- Touch targets (buttons, checkboxes on the shopping list) sized for
  fingers, not just mouse pointers.
- The shopping list and meal-adherence logging views are the two screens
  most likely used one-handed on a phone (in a store, at the table) and
  get the most attention here; the recipe-authoring and plan-generation
  forms are more likely used at a desk and can be denser.

## 4. Language: English + German, switchable

Full i18n from the start, since both languages are needed on day one:

- Translation strings live in flat per-locale files (e.g.
  `app/i18n/en.json`, `app/i18n/de.json`) — a simple key→string lookup, no
  `gettext`/Babel toolchain needed for a page count this small.
- A Jinja2 global function (e.g. `t("recipes.new.title")`) resolves the
  current request's locale to a string, falling back to English if a key
  is missing in German (so an untranslated new string never breaks the
  page, just shows English).
- **Locale resolution order:** logged-in user's `User.Locale` (§ see
  DATA_MODEL.md) → browser `Accept-Language` header → English default.
  `POST /locale` (API.md) updates `User.Locale` for logged-in users; for
  the pre-login `/register`/`/login` pages, it's stored in the session.
- A visible language switcher ("EN / DE") lives in the nav as a plain form
  post-redirect (not htmx) — a locale change re-renders every string on
  the page, so there's no fragment small enough to swap.
- Numbers/dates use each locale's convention where they differ (e.g. date
  format), but units stay metric always (PRD §9 — no imperial support).

## 5. Notable UI-specific requirements

- **Shopping list:** checkable items (DATA_MODEL
  `ShoppingListItem.Checked`) toggle via htmx tap, with a visual
  strikethrough/dim state for checked items. The checked state is
  household-shared — if someone else on the household is also viewing
  the list, checking an item should be reflected for them too on their
  next interaction (no realtime sync needed for v1; a page revisit is
  enough).
- **Plate visual:** the recipe view and plan-day view show a simple
  visual breakdown of the plate rule (PRD §5.2) — e.g. a segmented bar or
  simple pie showing the protein/carb/fat/veg proportions of that
  recipe's base serving — rather than only listing macro grams as
  numbers.
- **Scale-bound warnings:** a day flagged as outside the ideal scale
  range (PRD §5.5) is visually distinguished on the plan view (e.g. a
  warning badge), not just mentioned in passing text.
- **Print-friendly shopping list:** a print stylesheet (`@media print`)
  hides navigation/chrome and renders the shopping list as a clean
  checklist, for anyone who'd rather print it than use it on a phone.

## 6. Accessibility baseline

No dedicated WCAG audit planned for v1, but the approach (semantic HTML +
Pico.css defaults, which are built with accessible contrast and focus
states) provides a reasonable baseline for free. Form fields get proper
`<label>`s; icon-only buttons (if any) get `aria-label`s.

## 7. Out of scope for v1

- No offline/PWA support.
- No realtime multi-user sync (e.g. websockets) — see shopping list note
  above.
- No native mobile app — the mobile-first responsive web UI is the
  mobile experience.
- No dark mode toggle (Pico.css respects OS-level `prefers-color-scheme`
  automatically, which is enough for v1).

## 8. Open questions

- Should the plate-visual (§5) be computed client-side from the macro
  grams already sent to the template, or does it need a dedicated
  service-layer helper (`app/services/`) so it's unit-testable the same
  way calorie/PAL logic is (TESTING.md)? Leaning toward the latter for
  consistency, but not yet decided.
