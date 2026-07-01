# API — ba2bo2food

This is a server-rendered app (FastAPI + Jinja2), not a JSON API for an
external client — most routes render or redirect to an HTML page rather
than returning JSON. Routes marked **(JSON)** are the exception, used for
small in-page interactions (e.g. autocomplete).

All routes below except the Auth group require an active session
(logged-in user); unauthenticated requests redirect to `/login`.

This document is provisional — expect route names/shapes to shift once
routers are actually implemented; it exists to sanity-check that every
PRD feature has a place to live before coding starts.

## Auth

| Method | Path        | Purpose                                              |
|--------|-------------|--------------------------------------------------------|
| GET    | `/register` | Registration form (account fields from DATA_MODEL `User`, plus create-or-join household). |
| POST   | `/register` | Create the account. First registrant for a household creates it (generating an invite code); subsequent registrants enter an invite code to join that household instead of creating a new one. |
| GET    | `/login`    | Login form.                                             |
| POST   | `/login`    | Authenticate, start session.                            |
| POST   | `/logout`   | End session.                                            |
| POST   | `/locale`   | **(JSON, htmx)** Switch the current user's UI language (FRONTEND.md); persists to `User.Locale`. |

## Household

| Method | Path                | Purpose                                                    |
|--------|---------------------|-------------------------------------------------------------|
| GET    | `/household`        | View household members and their profiles, and the current invite code. |
| POST   | `/household/invite`  | Generate/refresh the household's invite code.                |

## Profile & progress (PRD §8)

| Method | Path                    | Purpose                                                      |
|--------|-------------------------|-----------------------------------------------------------------|
| GET    | `/profile`               | View own profile + current calculated `daily_target`/`weekly_budget` (PRD §3). |
| GET    | `/profile/edit`          | Edit profile form (metrics, goal weight/date, workouts/week).    |
| POST   | `/profile/edit`          | Save profile changes.                                            |
| POST   | `/profile/weight-checkins` | Log a new weight check-in (PRD §8).                             |
| GET    | `/profile/progress`      | Weight trend vs. goal, meal adherence history.                    |

## Recipes (PRD §4)

| Method | Path                     | Purpose                                             |
|--------|--------------------------|--------------------------------------------------------|
| GET    | `/recipes`                | List household's shared recipe library.                |
| GET    | `/recipes/new`            | New recipe form.                                        |
| POST   | `/recipes`                | Create a recipe (name, instructions, base servings, calories/macros, ingredient lines). |
| GET    | `/recipes/{id}`           | View a recipe.                                          |
| GET    | `/recipes/{id}/edit`      | Edit recipe form.                                       |
| POST   | `/recipes/{id}/edit`      | Save recipe changes (does not retroactively change past plans — DATA_MODEL `PlannedPortion` snapshot). |
| POST   | `/recipes/{id}/delete`    | Delete a recipe.                                        |
| GET    | `/ingredients/search`     | **(JSON)** Autocomplete existing `Ingredient`s by name, for the recipe form (DATA_MODEL decision). |

## Weekly plans (PRD §5-7)

| Method | Path                                          | Purpose                                                          |
|--------|-----------------------------------------------|---------------------------------------------------------------------|
| GET    | `/plans`                                       | List past/current planned blocks for the household.                  |
| GET    | `/plans/new`                                   | Form to choose a block's start date + length (1-7 days, PRD §5.3).    |
| POST   | `/plans`                                       | Run plan generation (ARCHITECTURE §5) for the chosen block; redirects to the generated plan. |
| GET    | `/plans/{id}`                                  | View a block: each day's dinner recipe, per-person portions, any scale-bound warnings (PRD §5.5), and each day's calorie target for days outside the block. |
| POST   | `/plans/{id}/days/{day_id}/meals/{meal_type}/log` | Log adherence (eaten/skipped/swapped) for the current user's lunch or dinner on that day (PRD §8). |
| GET    | `/plans/{id}/shopping-list`                    | View/print the block's consolidated shopping list (PRD §7).          |
| POST   | `/plans/{id}/shopping-list/items/{item_id}/check` | **(JSON, htmx)** Toggle a shopping list item's checked state (household-shared, FRONTEND.md/DATA_MODEL `ShoppingListItem.Checked`). |

## Open questions

- Should plan generation (`POST /plans`) be synchronous (user waits for
  the page to render the result) or is it fast enough that this is a
  non-issue? Given the greedy algorithm's expected input sizes
  (ARCHITECTURE §5), this should be near-instant, so synchronous is
  assumed sufficient.
