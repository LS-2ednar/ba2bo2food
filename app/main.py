import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.db import init_db
from app.dependencies import NotAuthenticated
from app.routers import auth, households, plans, progress, recipes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="ba2bo2food", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY", "dev-only-secret-change-me"),
)

app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static"
)

app.include_router(auth.router)
app.include_router(households.router)
app.include_router(recipes.router)
app.include_router(plans.router)
app.include_router(progress.router)


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.get("/")
def index():
    return RedirectResponse("/profile", status_code=303)
