# Data Model — ba2bo2food

Entities and relationships implied by [PRD.md](PRD.md). This supersedes
the early sketches in `utils/datamodel.py` and `data/model.sql`.

## Entity overview

```
Household 1───* User
Household 1───* Recipe
Recipe    1───* RecipeIngredient *───1 Ingredient
User      1───* WeightCheckIn
Household 1───* PlannedBlock
PlannedBlock 1───* PlannedDay ───1 Recipe (dinner)
PlannedDay   1───* PlannedPortion *───1 User
PlannedDay   1───* MealLog *───1 User
PlannedBlock 1───1 ShoppingList 1───* ShoppingListItem *───1 Ingredient
```

## Household

| Field      | Type          | Notes                                                          |
|------------|---------------|-------------------------------------------------------------------|
| Id         | int (PK)      |                                                                     |
| Name       | string        | e.g. "The Schaub Household"                                       |
| InviteCode | string, unique| Shared out-of-band so new registrants can join this household (API.md). Regeneratable. |
| CreatedAt  | datetime      |                                                                     |

## User

| Field            | Type          | Notes                                                        |
|------------------|---------------|---------------------------------------------------------------|
| Id               | int (PK)      |                                                                 |
| HouseholdId      | int (FK)      | One household per user in v1 (no multi-household membership). |
| Name             | string        |                                                                 |
| Email            | string, unique|                                                                 |
| PasswordHash     | string        | Auth mechanism itself is defined in ARCHITECTURE.md.           |
| DOB              | date          | Used to compute age for BMR.                                   |
| IsBornMale       | bool          | Selects Harris-Benedict formula (PRD §3.1).                    |
| Height           | float (cm)    |                                                                 |
| Weight           | float (kg)    | **Cached** most recent weight — kept in sync from the latest `WeightCheckIn` so reads don't always need a join. |
| GoalWeight       | float (kg)    |                                                                 |
| GoalDate         | date          |                                                                 |
| TrainingsPerWeek | int           | Drives PAL (PRD §3.2).                                          |
| Locale           | string        | UI language preference (`en`/`de`) — FRONTEND.md. Defaults from browser `Accept-Language` at registration. |
| CreatedAt        | datetime      |                                                                 |

## WeightCheckIn

Full weight history, used for progress tracking (PRD §8) and for
recalculating targets when the next plan is generated (PRD §3.4).

| Field       | Type      | Notes |
|-------------|-----------|-------|
| Id          | int (PK)  |       |
| UserId      | int (FK)  |       |
| Weight      | float (kg)|       |
| RecordedAt  | date      |       |

## Recipe

| Field                       | Type      | Notes                                             |
|-----------------------------|-----------|----------------------------------------------------|
| Id                          | int (PK)  |                                                      |
| HouseholdId                 | int (FK)  | Shared at household level (PRD §2, §4).             |
| CreatedByUserId             | int (FK)  | Who authored it.                                    |
| Name                        | string    |                                                      |
| Instructions                | text      |                                                      |
| BaseServings                | int       | Serving count the values below refer to.            |
| CaloriesPerBaseServing      | float     |                                                      |
| ProteinGramsPerBaseServing  | float     |                                                      |
| CarbGramsPerBaseServing     | float     |                                                      |
| FatGramsPerBaseServing      | float     |                                                      |
| CreatedAt                   | datetime  |                                                      |

Macro grams are stored for reference/display; the plate rule (PRD §5.2) is
a recipe-authoring guideline checked once, not recalculated per serving,
since proportional scaling preserves ratios.

## Ingredient

A lightweight, global lookup table so identical ingredients used across
different recipes can be consolidated on the shopping list.

| Field | Type          | Notes                          |
|-------|---------------|----------------------------------|
| Id    | int (PK)      |                                  |
| Name  | string, unique| e.g. "Chicken breast", "Rice".  |

## RecipeIngredient

| Field        | Type      | Notes                                                    |
|--------------|-----------|-----------------------------------------------------------|
| Id           | int (PK)  |                                                              |
| RecipeId     | int (FK)  |                                                              |
| IngredientId | int (FK)  |                                                              |
| Quantity     | float     | Amount needed for the recipe's `BaseServings`.              |
| Unit         | string    | e.g. "g", "ml", "pcs". **v1 simplification:** no unit conversion — the shopping list sums quantities that share the same `(Ingredient, Unit)` pair and lists mismatched units as separate lines. |

## PlannedBlock

One planning cycle for a household — a run of consecutive days (PRD §5.3).

| Field       | Type      | Notes                              |
|-------------|-----------|--------------------------------------|
| Id          | int (PK)  |                                      |
| HouseholdId | int (FK)  |                                      |
| StartDate   | date      |                                      |
| EndDate     | date      | `EndDate − StartDate` = block length (1–7 days). |
| CreatedAt   | datetime  |                                      |

## PlannedDay

One day within a block, with its assigned dinner recipe (PRD §6).

| Field           | Type      | Notes                                                        |
|-----------------|-----------|----------------------------------------------------------------|
| Id              | int (PK)  |                                                                  |
| PlannedBlockId  | int (FK)  |                                                                  |
| Date            | date      |                                                                  |
| DinnerRecipeId  | int (FK)  | The recipe cooked for dinner this day (and lunch the next day, unless this is the block's last day — PRD §5.4). |
| PortionsCooked  | int       | 2 for every day except the block's last (1) — PRD §5.4.          |
| IsFlagged       | bool      | Set when no recipe fit every member's scale bound and the closest-fit fallback was used instead (PRD §5.5). |

## PlannedPortion

Per-person scaling for a given day's dinner recipe. Macros are **snapshot
at generation time** so a later edit (or deletion) of the recipe doesn't
retroactively change what a historical plan "was."

| Field         | Type      | Notes                                                  |
|---------------|-----------|-------------------------------------------------------|
| Id            | int (PK)  |                                                              |
| PlannedDayId  | int (FK)  |                                                              |
| UserId        | int (FK)  |                                                              |
| ScaleFactor   | float     | Multiplier against `Recipe.BaseServings` at generation time, kept for reference/display. |
| Calories      | float     | Snapshot: `ScaleFactor × Recipe.CaloriesPerBaseServing` at generation time. |
| ProteinGrams  | float     | Snapshot, same basis.                                       |
| CarbGrams     | float     | Snapshot, same basis.                                       |
| FatGrams      | float     | Snapshot, same basis.                                       |

## MealLog

Adherence tracking (PRD §8). One row per person per planned dinner
represents both that dinner and the lunch it becomes the next day.

| Field         | Type                          | Notes                                           |
|---------------|-------------------------------|---------------------------------------------------|
| Id            | int (PK)                      |                                                     |
| UserId        | int (FK)                      |                                                     |
| PlannedDayId  | int (FK)                      | The day whose dinner this log refers to.           |
| MealType      | enum(Dinner, Lunch)           | Dinner = eaten same day; Lunch = eaten as leftover the next day. |
| Status        | enum(Eaten, Skipped, Swapped) |                                                     |
| Note          | text, nullable                | Freeform, e.g. what it was swapped for.            |
| LoggedAt      | datetime                      |                                                     |

## ShoppingList / ShoppingListItem

| Field           | Type      | Notes                        |
|-----------------|-----------|--------------------------------|
| ShoppingList.Id | int (PK)  |                                |
| PlannedBlockId  | int (FK, unique) | One shopping list per block. |
| GeneratedAt     | datetime  |                                |

| Field               | Type      | Notes                                          |
|---------------------|-----------|--------------------------------------------------|
| ShoppingListItem.Id | int (PK)  |                                                    |
| ShoppingListId      | int (FK)  |                                                    |
| IngredientId        | int (FK)  |                                                    |
| TotalQuantity       | float     | Summed across all recipes/portions in the block.  |
| Unit                | string    |                                                    |
| Checked             | bool, default false | Tap-to-check while shopping (FRONTEND.md). Household-shared state, not per-user. |

## Decisions & simplifications made for v1

- **One household per user.** No support yet for a person belonging to
  multiple households or switching households.
- **`User.Weight` is a cache**, kept current from the latest
  `WeightCheckIn`; it exists so profile/calorie-target reads don't require
  a join, while `WeightCheckIn` remains the source of truth for history.
- **No unit conversion.** Shopping-list consolidation only merges line
  items that already share the same ingredient *and* unit.
- **`Ingredient` is global**, not household-scoped — simplifies matching
  for shopping-list consolidation across recipes from different authors.
- **Ingredients are picked via autocomplete**, not typed free-text: when
  adding a recipe ingredient, the user searches existing `Ingredient` rows
  first and only creates a new one if it truly doesn't exist yet, keeping
  consolidation reliable without a curated master list to maintain.
- **`PlannedPortion` snapshots macros** at generation time (see above) —
  editing or deleting a `Recipe` later does not change historical plans.
- `data/model.sql` and the `Weight`/no-household version of `User` in
  `utils/datamodel.py` are now superseded by this document.
