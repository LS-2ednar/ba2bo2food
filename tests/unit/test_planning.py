import pytest

from app.services.planning import (
    Diner,
    InsufficientRecipesError,
    PlannableRecipe,
    generate_block_plan,
)


def make_recipes(*calories_per_base_serving):
    return [
        PlannableRecipe(recipe_id=i, calories_per_base_serving=cal)
        for i, cal in enumerate(calories_per_base_serving, start=1)
    ]


def test_single_diner_single_day_hits_target_exactly():
    diners = [Diner(user_id=1, dinner_target_calories=500)]
    recipes = make_recipes(500)
    [day] = generate_block_plan(diners, recipes, block_length=1)
    assert day.portions[0].calories == pytest.approx(500)
    assert not day.is_flagged


def test_recipe_outside_scale_bound_for_one_member_is_not_chosen_over_a_fitting_one():
    # Diner 1 needs 500 kcal, diner 2 needs 1200 kcal.
    # Recipe A (500 kcal/serving) scales to 1.0x/2.4x -> outside bound for diner 2.
    # Recipe B (700 kcal/serving) scales to ~0.71x/1.71x -> within bound for both.
    diners = [
        Diner(user_id=1, dinner_target_calories=500),
        Diner(user_id=2, dinner_target_calories=1200),
    ]
    recipes = make_recipes(500, 700)
    [day] = generate_block_plan(diners, recipes, block_length=1)
    assert day.recipe_id == 2
    assert not day.is_flagged


def test_no_recipe_fits_everyone_falls_back_to_closest_fit_and_flags():
    # Diner needs are too far apart (250 vs 2000) for either 500 or 2000
    # kcal/serving recipe to fit both within the 0.5x-2x bound.
    diners = [
        Diner(user_id=1, dinner_target_calories=250),
        Diner(user_id=2, dinner_target_calories=2000),
    ]
    recipes = make_recipes(500, 2000)
    [day] = generate_block_plan(diners, recipes, block_length=1)
    assert day.is_flagged


def test_no_recipe_repeats_within_a_block():
    diners = [Diner(user_id=1, dinner_target_calories=500)]
    recipes = make_recipes(500, 510, 490, 505, 495, 520, 480)
    assignments = generate_block_plan(diners, recipes, block_length=7)
    assert len(assignments) == 7
    assert len({a.recipe_id for a in assignments}) == 7


def test_last_day_is_cooked_as_a_single_portion():
    diners = [Diner(user_id=1, dinner_target_calories=500)]
    recipes = make_recipes(500, 500, 500)
    assignments = generate_block_plan(diners, recipes, block_length=3)
    assert [a.portions_cooked for a in assignments] == [2, 2, 1]


def test_single_day_block_is_cooked_as_a_single_portion():
    diners = [Diner(user_id=1, dinner_target_calories=500)]
    recipes = make_recipes(500)
    [day] = generate_block_plan(diners, recipes, block_length=1)
    assert day.portions_cooked == 1


def test_insufficient_recipes_raises_error():
    diners = [Diner(user_id=1, dinner_target_calories=500)]
    recipes = make_recipes(500, 500)
    with pytest.raises(InsufficientRecipesError):
        generate_block_plan(diners, recipes, block_length=3)
