# Architecture — ba2bo2food

## 1. Shape of the system

A single Python monolith: FastAPI serving server-rendered Jinja2 pages,
backed by SQLite via SQLAlchemy. No separate frontend build, no external
services. Deployment is local/self-hosted (see README).

```
Browser ── HTML forms/pages ──▶ FastAPI routers ──▶ services (domain logic) ──▶ SQLAlchemy models ──▶ SQLite
                                       ▲                     │
                                       └── Jinja2 templates ◀┘
```

## 2. Layering

Three layers, kept strictly separated so the domain logic in the middle
layer can be unit-tested without a database or an HTTP client (see
TESTING.md):

1. **Web layer** (`app/routers/`) — FastAPI path operations. Parses
   requests, calls services, renders templates or returns redirects.
   Contains no business rules itself.
2. **Domain/service layer** (`app/services/`) — plain Python, framework-
   and DB-agnostic where possible. This is where PRD.md's rules live:
   BMR/PAL/goal-pacing calculations, the weekly plan-generation algorithm,
   and shopping-list consolidation. Pure functions in, plain data out —
   easy to unit test exhaustively.
3. **Persistence layer** (`app/models/`, `app/db.py`) — SQLAlchemy ORM
   models (per DATA_MODEL.md) and session/engine setup.

Routers parse form data with FastAPI's own `Form(...)` request parameters
directly (no separate Pydantic request-schema layer) — there's no JSON
API to validate against, and FastAPI's form parameters already give
type coercion and validation errors for free.

## 3. Project structure

```
ba2bo2food/
  app/
    main.py              # FastAPI app instance, router registration
    db.py                 # engine/session setup
    security.py            # password hashing, invite code generation
    dependencies.py          # get_db, current-user/session dependencies
    templating.py              # Jinja2Templates + locale-aware render() helper
    i18n.py                      # translation lookup
    models/                        # SQLAlchemy models (User, Household, Recipe, ...)
    services/
      calorie_targets.py            # BMR, PAL, goal pacing (PRD §3)
      planning.py                     # weekly plan generation (PRD §5-6)
      shopping_list.py                  # ingredient consolidation (PRD §7)
    routers/
      auth.py
      households.py
      recipes.py
      plans.py
      progress.py                         # weight check-ins, adherence logging (PRD §8)
    i18n/                                   # en.json, de.json translation strings (FRONTEND.md)
    templates/                                # Jinja2 templates
    static/                                     # CSS (Pico.css + custom.css), vendored htmx (FRONTEND.md)
  data/                        # sqlite db file (gitignored)
  project_requirements/
  tests/
    unit/                      # services/, no DB or HTTP
    integration/                # routers + a test DB
```

The root `main.py` is just a thin `uv run main.py` convenience wrapper
around `uvicorn app.main:app`; the early `utils/datamodel.py` sketch has
been absorbed into `app/models/` as described above.

## 4. Authentication

Session-cookie based (not JWT/OAuth) — appropriate for a server-rendered,
self-hosted app with no external API consumers:

- Passwords hashed with a modern algorithm (e.g. `bcrypt`/`argon2` via
  `passlib`), never stored in plaintext.
- A signed session cookie (Starlette's `SessionMiddleware`, or an
  equivalent lightweight mechanism) identifies the logged-in `User`.
- No password reset/email-verification flow in v1 — out of scope, since
  this targets a single self-hosted household, not the public internet.

## 5. Weekly plan generation algorithm

Implements PRD §5–6. Key insight: because a recipe's portion can be
scaled continuously, calorie-matching alone is nearly trivial (any recipe
can hit any target by scaling) — so the actual combinatorial problem is
**which recipe to assign to each block day**, constrained by:

- **Scale bound (PRD §5.5):** a recipe is only eligible for a day if
  scaling it to fit every attending household member's target lands
  within ~0.5x–2x of `BaseServings`.
- **Variety (PRD §5.6):** no recipe repeats within a block.

Proposed approach for v1 (deterministic, no search library needed given
small inputs — a block is at most 7 days, recipe libraries are expected
to be tens, not thousands, of recipes):

1. For each block day (in order), compute each household member's target
   calories for that day's dinner portion (≈ half their `daily_target`,
   per PRD §5.4).
2. For each not-yet-used recipe, compute the scale factor each member
   would need (`target ÷ CaloriesPerBaseServing`) and check whether all
   of them fall within the bound.
3. Among recipes that pass, pick the one minimizing the maximum deviation
   across members (ties broken arbitrarily, e.g. by recipe id).
4. If none pass, fall back to the closest-fit recipe overall (still
   respecting the no-repeat constraint) and flag that day (PRD §5.5).
5. Mark the recipe used; continue to the next day.

This greedy day-by-day approach doesn't guarantee a globally optimal
week, but is simple, fast, testable in isolation, and sufficient for
libraries of realistic size. It can be revisited (e.g. backtracking, or
an actual solver) if greedy assignment produces poor real-world plans.

## 6. Role of claude-agent-sdk

Not used in v1's planning logic (PRD §6 — deterministic only). The
dependency is kept in `pyproject.toml` for potential future features
(e.g. AI-assisted recipe intake, smarter plan optimization) but nothing
in the v1 architecture calls it. If v1 ships without ever using it, it
should be removed rather than kept as dead weight.

## 7. Testing hooks this architecture enables

(Full strategy in TESTING.md.) The layering above exists specifically so:

- `app/services/*` can be unit-tested with plain function calls and
  fixtures — no DB, no HTTP, no FastAPI `TestClient` needed.
- `app/routers/*` are covered by integration tests using FastAPI's
  `TestClient` against a throwaway SQLite test database.

## 8. Open questions

- Greedy plan generation (§5) is a starting point, not a proven approach
  — worth revisiting once there's a real recipe library to test against.
- Session storage: in-memory/cookie-signed sessions are fine for a
  single-instance self-hosted deployment; would need revisiting (e.g.
  server-side session store) if ever deployed with multiple instances.
