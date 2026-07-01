# Product Requirements — ba2bo2food

## 1. Overview

ba2bo2food plans meals for a household of people who each have different
calorie needs, based on their body metrics and goals. It generates a weekly
dinner plan for a block of consecutive days (dinner leftovers reused as the
next day's lunch), scales each recipe to each person's calorie target,
enforces a healthy plate composition, and produces a single shopping list
for the planned days. Any days left outside that block are still given a
calorie target, but the user manages food for those days themselves.

## 2. Users & Households

- Every person has their own account (profile: name, email, DOB, sex,
  height, weight, goal weight, goal date, workouts/week).
- Accounts are grouped into a **Household**. A household is the unit that
  a weekly meal plan and shopping list are generated for.
- The recipe library is **shared at the household level** — any recipe
  added by any member is available to the whole household for planning.

## 3. Calorie Target Calculation

### 3.1 BMR — Harris-Benedict (original 1919 equation)

```
Men:   BMR = 66.5 + (13.75 × weight_kg) + (5.003 × height_cm) − (6.755 × age)
Women: BMR = 655.1 + (9.563 × weight_kg) + (1.850 × height_cm) − (4.676 × age)
```

`age` is derived from DOB as of the date the target is calculated.
`isBornMale` selects which formula to use.

### 3.2 PAL — Physical Activity Level

Derived from `TrainingsPerWeek` using the standard 5-tier scale:

| Workouts / week | PAL   | Label            |
|------------------|-------|------------------|
| 0                | 1.2   | Sedentary        |
| 1–2              | 1.375 | Lightly active   |
| 3–4              | 1.55  | Moderately active|
| 5–6              | 1.725 | Very active      |
| 7+               | 1.9   | Extra active     |

```
TDEE = BMR × PAL
```

### 3.3 Goal pacing (deficit/surplus)

Uses the ~7700 kcal ≈ 1 kg body-weight approximation, spread evenly over
the days remaining until `GoalDate`:

```
weight_delta_kg   = current_weight − goal_weight        # positive = lose, negative = gain
total_adjustment  = weight_delta_kg × 7700               # kcal
days_remaining    = goal_date − today                    # must be > 0
daily_adjustment  = total_adjustment / days_remaining
daily_target      = TDEE − daily_adjustment
weekly_budget     = daily_target × 7                      # always based on a full 7-day week,
                                                           # regardless of how many days get a
                                                           # recipe plan (see §5.3)
```

If `GoalDate` has been reached or already passed (`days_remaining <= 0`),
skip the deficit/surplus entirely and set `daily_target = TDEE`
(maintenance) until the user sets a new `GoalWeight`/`GoalDate`.

### 3.4 Recalculation

- Users log weight check-ins over time.
- The calorie target (and therefore `weekly_budget`) is **recalculated only
  when the next week's plan is generated**, using the most recent weight
  check-in and the recalculated `days_remaining`. A plan, once generated,
  keeps its targets stable for that week even if new check-ins come in
  mid-week.

## 4. Recipes

- A recipe is a **single dish**: name, ingredients (with quantities/units),
  instructions, and a total calorie + macro count (protein/carb/fat grams)
  for its base serving size.
- Recipes are authored to already satisfy the plate rule (§5.2) at their
  base serving size. Because portions are scaled **proportionally**, the
  plate ratio is preserved automatically at any serving size — no
  per-serving recalculation of ratios is needed.
- Recipes are shared at the household level (§2).

## 5. Meal Planning Rules

### 5.1 Meals in scope

Only **lunch and dinner** are planned in v1 (no breakfast/snacks).

### 5.2 The plate rule

Every recipe's base serving should be composed of roughly:

- 1/4 protein
- 1/4 – 1/8 carbohydrates
- 1/4 – 1/8 healthy fats
- remainder: vegetables

### 5.3 Partial-week planning

A household plans a **block of consecutive days** each week (1–7 days),
not necessarily the full week. Days outside the block still get a calorie
target (per §3.3) surfaced to the user, but no recipe, portioning, or
shopping-list involvement — the user manages food on those days entirely
on their own, and nothing about those days is tracked by the app (§5.6).

### 5.4 Batch cooking within the planned block

Dinner is cooked in **2 identical portions per person** so leftovers cover
the next day's lunch — but only for days *inside* the planned block:

- The **first day** of the block: dinner is planned; that day's lunch is
  not covered by a leftover (it falls outside the block, or comes from
  the previous week — see open assumption in §10) and is left to the user.
- **Middle and last days** of the block: lunch = leftover from the
  previous block-day's dinner; dinner = a newly assigned recipe.
- The **last day's** dinner is cooked as a **single portion**, sized to
  that day's own target — there is no following block-day to hand a
  leftover to.

Because a single cooked dinner portion (for non-final block days) serves
two meal slots, exact per-meal precision isn't the goal. Instead:

- Each dinner portion size targets roughly half of the person's
  `daily_target` (i.e. the average of a day's lunch + dinner target).
- The binding constraint is the **planned block as a whole**: the sum of a
  person's calories from planned meals should track
  `daily_target × (block length)` as closely as possible.

### 5.5 Scale bounds

Since one recipe is shared across the household but scaled per person, a
recipe is only eligible for a given day if its portion can be scaled
within roughly **0.5x–2x** of its `BaseServings` for every household
member eating that day — this keeps portions realistic to actually cook,
and prevents "hit any calorie target by scaling anything arbitrarily"
from making recipe choice meaningless.

If no recipe in the library scales acceptably for *every* member on a
given day, the planner still assigns the **closest-fit** recipe (smallest
maximum deviation across members) and **flags** that day's plan as
outside the ideal scale range, rather than failing outright.

### 5.6 Variety

The weekly planner must **not repeat a recipe within the same planned
block** — one distinct recipe per block day is required. If the
household's recipe library has fewer recipes than the block length, plan
generation should fail with a clear error asking the user to add more
recipes (or shorten the block).

### 5.7 Unplanned days

For days outside the block, the app surfaces only the calorie target
number. No recipe, adherence tracking, or logging is expected or recorded
for those days.

## 6. Weekly Plan Generation

**Input:** household members with their current `daily_target`s, the
chosen block of consecutive days to plan (§5.3), and the household's
recipe library.

**Output:** one dinner assignment per block day (recipe + per-person
portion-scale factor). Per §5.4, each assignment (except the block's last
day) implies that day's dinner *and* the next day's lunch for every
household member.

**Goal:** choose recipes and per-person scale factors such that:

1. No recipe repeats within the block (§5.6).
2. Each recipe scales within the 0.5x–2x bound (§5.5) for every household
   member on that day, where a fitting recipe exists (closest-fit
   fallback + flag otherwise).
3. Each person's total calorie intake across the block's planned meals is
   as close as possible to `daily_target × (block length)`.

v1 planning logic is **deterministic** (no AI/agent involvement) — a
straightforward selection/scaling algorithm, not an LLM call. The
`claude-agent-sdk` dependency is kept for potential future use but is out
of scope for v1's planning logic.

## 7. Shopping List

Once a block's dinner assignments are chosen, ingredient quantities across
all assigned recipes (at their per-person scale factors, summed across all
household members) are consolidated into a single shopping list for that
block.

## 8. Progress Tracking & Logging

- **Weight check-ins:** users log their current weight over time. Progress
  is shown against their `GoalWeight`/`GoalDate` trajectory.
- **Meal adherence:** each planned meal (lunch/dinner, inside the block
  only) can be marked as eaten, skipped, or swapped, to track actual
  adherence to the plan. Unplanned days (§5.6) are not tracked.

## 9. Out of scope for v1

- Breakfast and snacks.
- AI-driven/optimized plan generation (deterministic algorithm only for now).
- External nutrition databases/APIs (recipe macros are entered manually).
- Imperial units (metric only: kg, cm).
- Shopping list store-section grouping / pantry inventory tracking.
- Recipe sharing controls beyond "shared within a household."
- Logging/tracking anything for unplanned days.

## 10. Open questions / assumptions to revisit

- The first planned day's lunch, and whether a block that starts the week
  can inherit a leftover from the *previous* week's final planned dinner —
  currently assumed **no**, it's always left to the user, but this could
  be revisited once real usage shows whether that's annoying.
- No minimum/maximum bound is defined yet for how far a plan is allowed to
  deviate from its block calorie target before generation should be
  considered "failed" rather than "imperfect but acceptable."
- Ingredient units and how they're normalized for shopping-list
  consolidation (e.g. "200g" vs "1 cup") are not yet defined — see
  DATA_MODEL.md.
