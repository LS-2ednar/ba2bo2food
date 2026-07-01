# ba2bo2food

Household meal planning driven by actual energy needs, not guesswork.

Every person in a household gets a daily calorie target computed from their
own body metrics and activity level. Meals are planned from a shared recipe
library, portioned to each person's target, and turned into a single
consolidated shopping list — while batch-cooking keeps the amount of cooking
and shopping to a minimum.

## Status

The v1 slice described in [project_requirements/](project_requirements/)
is implemented: auth/households, recipes, weekly plan generation,
shopping lists, and progress tracking.

## Core concepts

- **Personal calorie targets** — each user's Basal Metabolic Rate (Harris-Benedict
  formula) is scaled by a Physical Activity Level (PAL) derived from their
  weekly training frequency, giving a daily calorie target tied to their
  current weight, goal weight, and goal date.
- **Households** — each person has their own account; accounts are grouped
  into a household so meals can be planned jointly for everyone who eats
  together, even though each person has a different calorie need.
- **Recipes, scaled per person** — recipes are stored with their nutritional
  info and scaled to fit each diner's remaining calorie budget for that meal.
- **The plate rule** — every planned meal targets roughly 1/4 protein,
  1/4–1/8 carbohydrates, 1/4–1/8 healthy fats, with the remainder made up of
  vegetables.
- **Weekly planning & shopping lists** — a week is planned across the whole
  household at once, ingredients are consolidated into a single shopping
  list, and dinners are cooked in double portions so the next day's lunch is
  the same meal — minimizing both cooking effort and shopping trips.

## Tech stack

- Python 3.10+, managed with [uv](https://docs.astral.sh/uv/)
- FastAPI + Jinja2 server-rendered templates, htmx for light interactivity
- SQLAlchemy models
- SQLite for storage
- pytest for unit and integration tests

## Documentation

Detailed specs live in [project_requirements/](project_requirements/):

- [PRD.md](project_requirements/PRD.md) — product requirements and business rules
- [DATA_MODEL.md](project_requirements/DATA_MODEL.md) — entities and relationships
- [ARCHITECTURE.md](project_requirements/ARCHITECTURE.md) — system design
- [FRONTEND.md](project_requirements/FRONTEND.md) — UI/UX, styling, i18n
- [API.md](project_requirements/API.md) — endpoint reference
- [TESTING.md](project_requirements/TESTING.md) — testing strategy

## Getting started

```bash
uv sync
uv run main.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) — it redirects to
`/login`, where you can register a new account (which also creates your
household) or join an existing one with an invite code.

Run the test suite with:

```bash
uv run pytest
```
