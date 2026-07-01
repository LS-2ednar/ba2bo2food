from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import get_db
from app.main import app
from app.models import Base, Household, Ingredient, Recipe, RecipeIngredient, User
from app.security import generate_invite_code, hash_password


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Not using `with TestClient(...)` deliberately: entering it would run the
    # real ASGI lifespan (app.main.lifespan -> init_db()) against the actual
    # default sqlite engine, touching data/ba2bo2food.db as a side effect.
    # Tables already exist on the per-test engine via db_session above.
    test_client = TestClient(app, follow_redirects=True)
    yield test_client
    app.dependency_overrides.clear()


PASSWORD = "password123"


def make_user(db_session, household, *, name, email, weight, height, trainings_per_week=3):
    user = User(
        HouseholdId=household.Id,
        Name=name,
        Email=email,
        PasswordHash=hash_password(PASSWORD),
        DOB=date(1990, 1, 1),
        IsBornMale=True,
        Height=height,
        Weight=weight,
        GoalWeight=weight,
        GoalDate=date.today() + timedelta(days=365),
        TrainingsPerWeek=trainings_per_week,
        Locale="en",
        CreatedAt=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.flush()
    return user


def make_recipe(db_session, household, user, *, name, calories, ingredient_name="Pasta"):
    recipe = Recipe(
        HouseholdId=household.Id,
        CreatedByUserId=user.Id,
        Name=name,
        Instructions="Cook it.",
        BaseServings=1,
        CaloriesPerBaseServing=calories,
        ProteinGramsPerBaseServing=calories * 0.2 / 4,
        CarbGramsPerBaseServing=calories * 0.5 / 4,
        FatGramsPerBaseServing=calories * 0.3 / 9,
        CreatedAt=datetime.utcnow(),
    )
    db_session.add(recipe)
    db_session.flush()

    ingredient = (
        db_session.query(Ingredient).filter(Ingredient.Name == ingredient_name).first()
    )
    if ingredient is None:
        ingredient = Ingredient(Name=ingredient_name)
        db_session.add(ingredient)
        db_session.flush()
    db_session.add(
        RecipeIngredient(RecipeId=recipe.Id, IngredientId=ingredient.Id, Quantity=100, Unit="g")
    )
    db_session.flush()
    return recipe


@pytest.fixture()
def seeded_household(db_session):
    """A household with two members with different calorie needs and a
    7-recipe library, per TESTING.md's fixture guidance."""
    household = Household(
        Name="Test Household", InviteCode=generate_invite_code(), CreatedAt=datetime.utcnow()
    )
    db_session.add(household)
    db_session.flush()

    alice = make_user(
        db_session, household, name="Alice", email="alice@example.com", weight=60, height=165
    )
    bob = make_user(
        db_session, household, name="Bob", email="bob@example.com", weight=95, height=190
    )

    recipes = [
        make_recipe(db_session, household, alice, name=f"Recipe {i}", calories=550 + i * 20)
        for i in range(7)
    ]
    db_session.commit()

    return {"household": household, "alice": alice, "bob": bob, "recipes": recipes}


def login(client, email, password=PASSWORD):
    return client.post("/login", data={"email": email, "password": password})
