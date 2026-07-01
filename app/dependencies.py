from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User


class NotAuthenticated(Exception):
    pass


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def require_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise NotAuthenticated()
    return user
