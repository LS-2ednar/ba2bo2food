from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_user
from app.models import MealLog, User, WeightCheckIn
from app.services.calorie_targets import calculate_calorie_target
from app.templating import render

router = APIRouter()


@router.get("/profile")
def profile_detail(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    target = calculate_calorie_target(
        weight_kg=user.Weight,
        height_cm=user.Height,
        dob=user.DOB,
        is_born_male=user.IsBornMale,
        trainings_per_week=user.TrainingsPerWeek,
        goal_weight_kg=user.GoalWeight,
        goal_date=user.GoalDate,
    )
    return render(request, "profile/detail.html", {"target": target}, user=user)


@router.get("/profile/edit")
def profile_edit_form(
    request: Request, user: User = Depends(require_user)
):
    return render(request, "profile/edit.html", user=user)


@router.post("/profile/edit")
def profile_edit(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    name: str = Form(...),
    email: str = Form(...),
    dob: date = Form(...),
    sex: str = Form(...),
    height: float = Form(...),
    goal_weight: float = Form(...),
    goal_date: date = Form(...),
    trainings_per_week: int = Form(...),
):
    user.Name = name
    user.Email = email
    user.DOB = dob
    user.IsBornMale = sex == "male"
    user.Height = height
    user.GoalWeight = goal_weight
    user.GoalDate = goal_date
    user.TrainingsPerWeek = trainings_per_week
    db.commit()
    return RedirectResponse("/profile", status_code=303)


@router.post("/profile/weight-checkins")
def add_weight_checkin(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    weight: float = Form(...),
    recorded_at: date = Form(...),
):
    db.add(WeightCheckIn(UserId=user.Id, Weight=weight, RecordedAt=recorded_at))
    if recorded_at >= (user.WeightCheckIns[-1].RecordedAt if user.WeightCheckIns else date.min):
        user.Weight = weight
    db.commit()
    return RedirectResponse("/profile/progress", status_code=303)


@router.get("/profile/progress")
def profile_progress(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    checkins = (
        db.query(WeightCheckIn)
        .filter(WeightCheckIn.UserId == user.Id)
        .order_by(WeightCheckIn.RecordedAt.desc())
        .all()
    )
    meal_logs = (
        db.query(MealLog)
        .filter(MealLog.UserId == user.Id)
        .order_by(MealLog.LoggedAt.desc())
        .limit(50)
        .all()
    )
    return render(
        request,
        "profile/progress.html",
        {"checkins": checkins, "meal_logs": meal_logs},
        user=user,
    )
