# Testing Strategy — ba2bo2food

Tooling: `pytest`, plus FastAPI's `TestClient` (httpx-based) for
integration tests. Run with:

```bash
uv run pytest
```

The split below follows the layering in ARCHITECTURE.md: domain/service
logic is unit-tested in isolation; routers are integration-tested against
a real (throwaway) database.

## Unit tests — `tests/unit/`

Target `app/services/*` directly — no DB, no HTTP client. These tests
encode the business rules from PRD.md as executable assertions.

### `calorie_targets.py` (PRD §3)

- BMR: known-value assertions for both the male and female Harris-Benedict
  formulas (§3.1) against hand-calculated examples.
- PAL: every boundary of the 5-tier table (§3.2) — 0, 1, 2, 3, 4, 5, 6, 7,
  and a large value (e.g. 10) — maps to the correct multiplier.
- Goal pacing (§3.3):
  - Losing weight (current > goal) produces a deficit.
  - Gaining weight (current < goal) produces a surplus.
  - Maintaining (current == goal) produces `daily_target == TDEE`.
  - `days_remaining <= 0` (GoalDate today or in the past) falls back to
    maintenance (`daily_target == TDEE`) rather than dividing by zero or
    a negative number.
  - `weekly_budget == daily_target * 7` always, independent of block
    length.

### `planning.py` (PRD §5-6)

- A recipe within the 0.5x–2x scale bound for every attending household
  member is eligible; one outside the bound for even one member is not.
- No-repeat constraint: the same recipe is never assigned twice within
  one generated block.
- Closest-fit fallback: when no recipe fits every member within the
  bound, the recipe with the smallest maximum deviation is chosen, and
  the day is flagged.
- Block-length edge cases: block length of 1 (single day, cooked as a
  single portion, no leftover) and block length of 7 (full week).
- Insufficient recipes (library smaller than block length) raises a clear
  error (§5.6).

### `shopping_list.py` (PRD §7)

- Two recipes sharing an ingredient at the same unit consolidate into one
  summed line item.
- The same ingredient at different units produces separate line items
  (no unit conversion — DATA_MODEL.md decision).
- Quantities are correctly summed across multiple household members'
  portions, not just per recipe.

## Integration tests — `tests/integration/`

Use FastAPI's `TestClient` against a temporary SQLite database created
fresh per test (or per test module), covering the routes in API.md
end-to-end:

- **Auth:** register creates a household + invite code; a second
  registration using that invite code joins the same household; login/
  logout gate access to the rest of the app.
- **Recipes:** create, edit (and confirm an existing plan's snapshotted
  `PlannedPortion` macros are unaffected — DATA_MODEL.md decision), and
  delete a recipe; ingredient autocomplete returns existing matches.
- **Plan generation:** `POST /plans` for a household with enough varied
  recipes produces a block covering the requested days, with per-person
  portions and a shopping list; a household without enough recipes gets a
  clear error instead of a broken plan.
- **Meal logging:** marking a planned meal eaten/skipped/swapped persists
  and shows up in `/profile/progress`.
- **Weight check-ins:** logging a new weight is reflected in
  `/profile/progress`, but does **not** change the calorie target of an
  already-generated plan (only the next one generated — PRD §3.4).

## Fixtures

Shared `tests/conftest.py` fixtures:

- A test household with 2+ users with deliberately different calorie
  needs (to exercise the scale-bound logic).
- A small recipe library (enough recipes to fill a 7-day block, plus at
  least one recipe intentionally outside a reasonable scale range for one
  test user, to exercise the closest-fit fallback).
- A `TestClient` wired to a temporary SQLite database, torn down after
  each test.

## Out of scope for v1

- No load/performance testing.
- No security penetration testing (see project_requirements/ARCHITECTURE.md
  §4 for the intentionally minimal auth model).
- No automated visual/UI testing of the rendered Jinja2 templates —
  verified manually in-browser during development.

## CI

Tests run automatically via GitHub Actions on every push and pull
request against `main` (`uv sync && uv run pytest`). This is a v1
requirement — the workflow should be added alongside the first real
application code, not deferred.
