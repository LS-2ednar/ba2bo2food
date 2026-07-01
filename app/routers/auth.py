from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_optional_user
from app.i18n import SUPPORTED_LOCALES
from app.models import Household, User, WeightCheckIn
from app.security import generate_invite_code, hash_password, verify_password
from app.templating import locale_for, render

router = APIRouter()


@router.get("/register")
def register_form(request: Request, user: User | None = Depends(get_optional_user)):
    return render(request, "auth/register.html", user=user)


@router.post("/register")
def register(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    dob: date = Form(...),
    sex: str = Form(...),
    height: float = Form(...),
    weight: float = Form(...),
    goal_weight: float = Form(...),
    goal_date: date = Form(...),
    trainings_per_week: int = Form(...),
    household_mode: str = Form(...),
    household_name: str = Form(""),
    invite_code: str = Form(""),
):
    locale = locale_for(request, None)

    if db.query(User).filter(User.Email == email).first() is not None:
        return render(
            request,
            "auth/register.html",
            {"error_key": "errors.email_taken"},
            status_code=400,
        )

    if household_mode == "join":
        household = db.query(Household).filter(Household.InviteCode == invite_code).first()
        if household is None:
            return render(
                request,
                "auth/register.html",
                {"error_key": "errors.invalid_invite_code"},
                status_code=400,
            )
    else:
        household = Household(
            Name=household_name or f"{name}'s household",
            InviteCode=generate_invite_code(),
            CreatedAt=datetime.utcnow(),
        )
        db.add(household)
        db.flush()

    user = User(
        HouseholdId=household.Id,
        Name=name,
        Email=email,
        PasswordHash=hash_password(password),
        DOB=dob,
        IsBornMale=(sex == "male"),
        Height=height,
        Weight=weight,
        GoalWeight=goal_weight,
        GoalDate=goal_date,
        TrainingsPerWeek=trainings_per_week,
        Locale=locale,
        CreatedAt=datetime.utcnow(),
    )
    db.add(user)
    db.flush()
    db.add(WeightCheckIn(UserId=user.Id, Weight=weight, RecordedAt=date.today()))
    db.commit()

    request.session["user_id"] = user.Id
    return RedirectResponse("/profile", status_code=303)


@router.get("/login")
def login_form(request: Request, user: User | None = Depends(get_optional_user)):
    return render(request, "auth/login.html", user=user)


@router.post("/login")
def login(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    user = db.query(User).filter(User.Email == email).first()
    if user is None or not verify_password(password, user.PasswordHash):
        return render(
            request,
            "auth/login.html",
            {"error_key": "errors.invalid_credentials"},
            status_code=400,
        )
    request.session["user_id"] = user.Id
    return RedirectResponse("/profile", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.post("/locale")
def switch_locale(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    locale: str = Form(...),
    redirect_to: str = Form("/"),
):
    if locale not in SUPPORTED_LOCALES:
        locale = "en"
    if user is not None:
        user.Locale = locale
        db.commit()
    else:
        request.session["locale"] = locale
    return RedirectResponse(redirect_to, status_code=303)
