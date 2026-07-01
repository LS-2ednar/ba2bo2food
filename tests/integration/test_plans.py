from datetime import date, timedelta

from tests.conftest import login


def test_generate_plan_produces_block_with_portions_and_shopping_list(client, seeded_household):
    login(client, "alice@example.com")
    start = date.today() + timedelta(days=1)
    r = client.post("/plans", data={"start_date": start.isoformat(), "length": "7"})
    assert r.status_code == 200
    assert "/plans/" in str(r.url)

    r = client.get(str(r.url))
    assert "kcal" in r.text

    block_id = str(r.url).rstrip("/").split("/")[-1]
    r = client.get(f"/plans/{block_id}/shopping-list")
    assert r.status_code == 200
    assert "Pasta" in r.text


def test_generate_plan_fails_clearly_with_insufficient_recipes(client, db_session):
    from datetime import datetime

    from app.models import Household, User
    from app.security import generate_invite_code, hash_password

    household = Household(
        Name="Small HH", InviteCode=generate_invite_code(), CreatedAt=datetime.utcnow()
    )
    db_session.add(household)
    db_session.flush()
    db_session.add(
        User(
            HouseholdId=household.Id,
            Name="Solo",
            Email="solo@example.com",
            PasswordHash=hash_password("password123"),
            DOB=date(1990, 1, 1),
            IsBornMale=True,
            Height=180,
            Weight=80,
            GoalWeight=80,
            GoalDate=date.today() + timedelta(days=365),
            TrainingsPerWeek=3,
            Locale="en",
            CreatedAt=datetime.utcnow(),
        )
    )
    db_session.commit()

    login(client, "solo@example.com")
    start = date.today() + timedelta(days=1)
    r = client.post("/plans", data={"start_date": start.isoformat(), "length": "7"})
    assert r.status_code == 400
    assert "recipe" in r.text.lower()


def test_meal_log_persists_and_shows_in_progress(client, seeded_household):
    login(client, "alice@example.com")
    start = date.today() + timedelta(days=1)
    r = client.post("/plans", data={"start_date": start.isoformat(), "length": "3"})
    block_url = str(r.url)
    block_id = block_url.rstrip("/").split("/")[-1]

    r = client.get(block_url)
    day_id_str = r.text.split("meals/dinner/log")[0].split("/days/")[-1]
    day_id = day_id_str.split("/")[0]

    r = client.post(
        f"/plans/{block_id}/days/{day_id}/meals/dinner/log",
        data={"status": "eaten", "note": ""},
    )
    assert r.status_code == 200

    r = client.get("/profile/progress")
    assert "Eaten" in r.text


def test_editing_recipe_does_not_change_historical_plan_portions(client, seeded_household):
    login(client, "alice@example.com")
    start = date.today() + timedelta(days=1)
    r = client.post("/plans", data={"start_date": start.isoformat(), "length": "7"})
    block_url = str(r.url)

    r = client.get(block_url)
    before = r.text

    recipe = seeded_household["recipes"][0]
    r = client.post(
        f"/recipes/{recipe.Id}/edit",
        data={
            "name": recipe.Name,
            "instructions": recipe.Instructions,
            "base_servings": "1",
            "calories": "9999",
            "protein": "1",
            "carbs": "1",
            "fat": "1",
            "ingredient_name": ["Pasta"],
            "ingredient_quantity": ["100"],
            "ingredient_unit": ["g"],
        },
    )
    assert r.status_code == 200

    r = client.get(block_url)
    after = r.text
    assert before == after
