from datetime import date

import pytest

from app.services.calorie_targets import (
    calculate_age,
    calculate_bmr,
    calculate_calorie_target,
    pal_for_trainings_per_week,
)


def test_bmr_male_known_value():
    # 66.5 + 13.75*80 + 5.003*180 - 6.755*30
    assert calculate_bmr(weight_kg=80, height_cm=180, age=30, is_born_male=True) == pytest.approx(
        1864.39
    )


def test_bmr_female_known_value():
    # 655.1 + 9.563*60 + 1.850*165 - 4.676*25
    assert calculate_bmr(
        weight_kg=60, height_cm=165, age=25, is_born_male=False
    ) == pytest.approx(1417.23)


@pytest.mark.parametrize(
    "trainings_per_week,expected_pal",
    [
        (0, 1.2),
        (1, 1.375),
        (2, 1.375),
        (3, 1.55),
        (4, 1.55),
        (5, 1.725),
        (6, 1.725),
        (7, 1.9),
        (10, 1.9),
    ],
)
def test_pal_boundaries(trainings_per_week, expected_pal):
    assert pal_for_trainings_per_week(trainings_per_week) == expected_pal


def test_calculate_age_before_and_after_birthday():
    assert calculate_age(date(1990, 6, 15), date(2026, 6, 14)) == 35
    assert calculate_age(date(1990, 6, 15), date(2026, 6, 15)) == 36


def test_goal_pacing_produces_deficit_when_losing_weight():
    target = calculate_calorie_target(
        weight_kg=90,
        height_cm=180,
        dob=date(1990, 1, 1),
        is_born_male=True,
        trainings_per_week=3,
        goal_weight_kg=80,
        goal_date=date(2026, 12, 31),
        today=date(2026, 1, 1),
    )
    assert target.daily_target < target.tdee


def test_goal_pacing_produces_surplus_when_gaining_weight():
    target = calculate_calorie_target(
        weight_kg=70,
        height_cm=180,
        dob=date(1990, 1, 1),
        is_born_male=True,
        trainings_per_week=3,
        goal_weight_kg=80,
        goal_date=date(2026, 12, 31),
        today=date(2026, 1, 1),
    )
    assert target.daily_target > target.tdee


def test_goal_pacing_is_maintenance_when_already_at_goal():
    target = calculate_calorie_target(
        weight_kg=75,
        height_cm=180,
        dob=date(1990, 1, 1),
        is_born_male=True,
        trainings_per_week=3,
        goal_weight_kg=75,
        goal_date=date(2026, 12, 31),
        today=date(2026, 1, 1),
    )
    assert target.daily_target == pytest.approx(target.tdee)


@pytest.mark.parametrize("goal_date", [date(2026, 1, 1), date(2025, 6, 1)])
def test_goal_pacing_falls_back_to_maintenance_when_goal_date_reached_or_passed(goal_date):
    target = calculate_calorie_target(
        weight_kg=90,
        height_cm=180,
        dob=date(1990, 1, 1),
        is_born_male=True,
        trainings_per_week=3,
        goal_weight_kg=80,
        goal_date=goal_date,
        today=date(2026, 1, 1),
    )
    assert target.daily_target == pytest.approx(target.tdee)


def test_weekly_budget_is_always_seven_times_daily_target():
    target = calculate_calorie_target(
        weight_kg=90,
        height_cm=180,
        dob=date(1990, 1, 1),
        is_born_male=True,
        trainings_per_week=3,
        goal_weight_kg=80,
        goal_date=date(2026, 12, 31),
        today=date(2026, 1, 1),
    )
    assert target.weekly_budget == pytest.approx(target.daily_target * 7)
