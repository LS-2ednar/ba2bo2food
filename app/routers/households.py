from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_user
from app.models import Household, User
from app.security import generate_invite_code
from app.templating import render

router = APIRouter()


@router.get("/household")
def household_detail(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    household = db.get(Household, user.HouseholdId)
    members = db.query(User).filter(User.HouseholdId == user.HouseholdId).order_by(User.Name).all()
    return render(
        request,
        "household/detail.html",
        {"household": household, "members": members},
        user=user,
    )


@router.post("/household/invite")
def regenerate_invite(db: Session = Depends(get_db), user: User = Depends(require_user)):
    household = db.get(Household, user.HouseholdId)
    household.InviteCode = generate_invite_code()
    db.commit()
    return RedirectResponse("/household", status_code=303)
