"""Weekly plan generation — PRD §5-6, ARCHITECTURE.md §5.

A recipe's portion scales continuously, so hitting a calorie target exactly
is nearly always possible — the actual problem is *which* recipe to assign
to each day, given:

- a recipe is only eligible for a day if scaling it for every attending
  member lands within SCALE_BOUND of its BaseServings (PRD §5.5)
- no recipe may repeat within a block (PRD §5.6)

When no recipe fits every member within the bound, the closest-fit recipe
is used anyway and the day is flagged (PRD §5.5).
"""

from dataclasses import dataclass

SCALE_BOUND_MIN = 0.5
SCALE_BOUND_MAX = 2.0


class InsufficientRecipesError(Exception):
    """Raised when the recipe library has fewer recipes than the block length (PRD §5.6)."""


@dataclass(frozen=True)
class Diner:
    user_id: int
    dinner_target_calories: float


@dataclass(frozen=True)
class PlannableRecipe:
    recipe_id: int
    calories_per_base_serving: float


@dataclass(frozen=True)
class Portion:
    user_id: int
    scale_factor: float
    calories: float


@dataclass(frozen=True)
class DayAssignment:
    recipe_id: int
    portions: list[Portion]
    portions_cooked: int
    is_flagged: bool


def _scale_factors(recipe: PlannableRecipe, diners: list[Diner]) -> dict[int, float]:
    return {
        diner.user_id: diner.dinner_target_calories / recipe.calories_per_base_serving
        for diner in diners
    }


def _max_deviation_from_one(scale_factors: dict[int, float]) -> float:
    return max(abs(factor - 1.0) for factor in scale_factors.values())


def _fits_scale_bound(scale_factors: dict[int, float]) -> bool:
    return all(SCALE_BOUND_MIN <= factor <= SCALE_BOUND_MAX for factor in scale_factors.values())


def _best_recipe_for_day(
    candidates: list[PlannableRecipe], diners: list[Diner]
) -> tuple[PlannableRecipe, dict[int, float], bool]:
    scored = [(recipe, _scale_factors(recipe, diners)) for recipe in candidates]

    eligible = [(recipe, factors) for recipe, factors in scored if _fits_scale_bound(factors)]
    pool = eligible if eligible else scored
    is_flagged = not eligible

    best_recipe, best_factors = min(pool, key=lambda pair: _max_deviation_from_one(pair[1]))
    return best_recipe, best_factors, is_flagged


def generate_block_plan(
    diners: list[Diner], recipe_library: list[PlannableRecipe], block_length: int
) -> list[DayAssignment]:
    if len(recipe_library) < block_length:
        raise InsufficientRecipesError(
            f"Need at least {block_length} recipes to plan {block_length} day(s), "
            f"only {len(recipe_library)} available."
        )

    remaining = list(recipe_library)
    assignments: list[DayAssignment] = []

    for day_index in range(block_length):
        recipe, factors, is_flagged = _best_recipe_for_day(remaining, diners)
        remaining = [r for r in remaining if r.recipe_id != recipe.recipe_id]

        portions = [
            Portion(
                user_id=diner.user_id,
                scale_factor=factors[diner.user_id],
                calories=factors[diner.user_id] * recipe.calories_per_base_serving,
            )
            for diner in diners
        ]
        is_last_day = day_index == block_length - 1
        assignments.append(
            DayAssignment(
                recipe_id=recipe.recipe_id,
                portions=portions,
                portions_cooked=1 if is_last_day else 2,
                is_flagged=is_flagged,
            )
        )

    return assignments
