from functools import partial
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.i18n import resolve_locale, translate
from app.models import User

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def locale_for(request: Request, user: User | None) -> str:
    if user is not None:
        return user.Locale
    session_locale = request.session.get("locale")
    if session_locale:
        return session_locale
    return resolve_locale(request.headers.get("accept-language"))


def render(
    request: Request,
    name: str,
    context: dict | None = None,
    *,
    user: User | None = None,
    status_code: int = 200,
):
    context = dict(context or {})
    locale = locale_for(request, user)
    context["locale"] = locale
    context["t"] = partial(translate, locale)
    context["current_user"] = user
    return templates.TemplateResponse(request, name, context, status_code=status_code)
