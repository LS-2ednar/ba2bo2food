"""Shopping list consolidation — PRD §7, DATA_MODEL.md decisions.

No unit conversion: quantities only consolidate across recipes/portions
when they already share the same (ingredient, unit) pair.
"""

from dataclasses import dataclass

from app.services.planning import DayAssignment


@dataclass(frozen=True)
class RecipeIngredientLine:
    ingredient_id: int
    quantity_per_base_serving: float
    unit: str


@dataclass(frozen=True)
class ShoppingListLine:
    ingredient_id: int
    unit: str
    total_quantity: float


def build_shopping_list(
    day_assignments: list[DayAssignment],
    recipe_ingredients_by_recipe_id: dict[int, list[RecipeIngredientLine]],
) -> list[ShoppingListLine]:
    totals: dict[tuple[int, str], float] = {}

    for day in day_assignments:
        ingredient_lines = recipe_ingredients_by_recipe_id[day.recipe_id]
        for portion in day.portions:
            # A day's dinner is physically cooked `portions_cooked` times
            # (dinner + next day's leftover lunch, PRD §5.4), so ingredients
            # are needed that many times over for each diner's portion.
            multiplier = portion.scale_factor * day.portions_cooked
            for line in ingredient_lines:
                key = (line.ingredient_id, line.unit)
                totals[key] = totals.get(key, 0.0) + line.quantity_per_base_serving * multiplier

    return [
        ShoppingListLine(ingredient_id=ingredient_id, unit=unit, total_quantity=total)
        for (ingredient_id, unit), total in totals.items()
    ]
