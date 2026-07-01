import pytest

from app.services.planning import DayAssignment, Portion
from app.services.shopping_list import RecipeIngredientLine, build_shopping_list


def test_same_ingredient_same_unit_across_recipes_consolidates():
    assignments = [
        DayAssignment(
            recipe_id=1,
            portions=[Portion(user_id=1, scale_factor=1.0, calories=500)],
            portions_cooked=1,
            is_flagged=False,
        ),
        DayAssignment(
            recipe_id=2,
            portions=[Portion(user_id=1, scale_factor=1.0, calories=500)],
            portions_cooked=1,
            is_flagged=False,
        ),
    ]
    ingredients = {
        1: [RecipeIngredientLine(ingredient_id=100, quantity_per_base_serving=200, unit="g")],
        2: [RecipeIngredientLine(ingredient_id=100, quantity_per_base_serving=100, unit="g")],
    }
    [line] = build_shopping_list(assignments, ingredients)
    assert line.ingredient_id == 100
    assert line.unit == "g"
    assert line.total_quantity == pytest.approx(300)


def test_same_ingredient_different_units_stay_separate_lines():
    assignments = [
        DayAssignment(
            recipe_id=1,
            portions=[Portion(user_id=1, scale_factor=1.0, calories=500)],
            portions_cooked=1,
            is_flagged=False,
        ),
    ]
    ingredients = {
        1: [
            RecipeIngredientLine(ingredient_id=100, quantity_per_base_serving=200, unit="g"),
            RecipeIngredientLine(ingredient_id=100, quantity_per_base_serving=1, unit="pcs"),
        ],
    }
    lines = build_shopping_list(assignments, ingredients)
    assert len(lines) == 2
    units = {line.unit for line in lines}
    assert units == {"g", "pcs"}


def test_quantities_summed_across_multiple_household_members():
    assignments = [
        DayAssignment(
            recipe_id=1,
            portions=[
                Portion(user_id=1, scale_factor=1.0, calories=500),
                Portion(user_id=2, scale_factor=2.0, calories=1000),
            ],
            portions_cooked=1,
            is_flagged=False,
        ),
    ]
    ingredients = {
        1: [RecipeIngredientLine(ingredient_id=100, quantity_per_base_serving=100, unit="g")],
    }
    [line] = build_shopping_list(assignments, ingredients)
    # user 1: 1.0 * 100 = 100g, user 2: 2.0 * 100 = 200g -> 300g total
    assert line.total_quantity == pytest.approx(300)


def test_portions_cooked_multiplies_ingredient_quantity():
    assignments = [
        DayAssignment(
            recipe_id=1,
            portions=[Portion(user_id=1, scale_factor=1.0, calories=500)],
            portions_cooked=2,
            is_flagged=False,
        ),
    ]
    ingredients = {
        1: [RecipeIngredientLine(ingredient_id=100, quantity_per_base_serving=100, unit="g")],
    }
    [line] = build_shopping_list(assignments, ingredients)
    assert line.total_quantity == pytest.approx(200)
