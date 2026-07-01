"""Calorie target calculation — PRD §3.

BMR (Harris-Benedict, 1919) -> TDEE (x PAL) -> daily/weekly target
(adjusted for the pace needed to reach GoalWeight by GoalDate).
"""

from dataclasses import dataclass
from datetime import date

KCAL_PER_KG = 7700


@dataclass(frozen=True)
class CalorieTarget:
    bmr: float
    pal: float
    tdee: float
    daily_target: float
    weekly_budget: float


def calculate_age(dob: date, as_of: date) -> int:
    years = as_of.year - dob.year
    if (as_of.month, as_of.day) < (dob.month, dob.day):
        years -= 1
    return years


def calculate_bmr(weight_kg: float, height_cm: float, age: int, is_born_male: bool) -> float:
    if is_born_male:
        return 66.5 + (13.75 * weight_kg) + (5.003 * height_cm) - (6.755 * age)
    return 655.1 + (9.563 * weight_kg) + (1.850 * height_cm) - (4.676 * age)


def pal_for_trainings_per_week(trainings_per_week: int) -> float:
    """PRD §3.2's 5-tier PAL scale."""
    if trainings_per_week <= 0:
        return 1.2
    if trainings_per_week <= 2:
        return 1.375
    if trainings_per_week <= 4:
        return 1.55
    if trainings_per_week <= 6:
        return 1.725
    return 1.9


def calculate_calorie_target(
    *,
    weight_kg: float,
    height_cm: float,
    dob: date,
    is_born_male: bool,
    trainings_per_week: int,
    goal_weight_kg: float,
    goal_date: date,
    today: date | None = None,
) -> CalorieTarget:
    today = today or date.today()
    age = calculate_age(dob, today)
    bmr = calculate_bmr(weight_kg, height_cm, age, is_born_male)
    pal = pal_for_trainings_per_week(trainings_per_week)
    tdee = bmr * pal

    days_remaining = (goal_date - today).days
    if days_remaining <= 0:
        # Goal date reached or passed: fall back to maintenance (PRD §3.3).
        daily_target = tdee
    else:
        weight_delta_kg = weight_kg - goal_weight_kg
        total_adjustment = weight_delta_kg * KCAL_PER_KG
        daily_adjustment = total_adjustment / days_remaining
        daily_target = tdee - daily_adjustment

    return CalorieTarget(
        bmr=bmr,
        pal=pal,
        tdee=tdee,
        daily_target=daily_target,
        weekly_budget=daily_target * 7,
    )
