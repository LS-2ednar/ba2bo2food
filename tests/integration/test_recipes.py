from tests.conftest import login


def test_create_view_edit_delete_recipe(client, seeded_household):
    login(client, "alice@example.com")

    r = client.post(
        "/recipes",
        data={
            "name": "Test Bowl",
            "instructions": "Mix it up.",
            "base_servings": "1",
            "calories": "600",
            "protein": "40",
            "carbs": "60",
            "fat": "15",
            "ingredient_name": ["Chicken breast"],
            "ingredient_quantity": ["150"],
            "ingredient_unit": ["g"],
        },
    )
    assert r.status_code == 200
    assert "Test Bowl" in r.text
    assert "Chicken breast" in r.text

    recipe_url = str(r.url)
    r = client.post(
        f"{recipe_url}/edit",
        data={
            "name": "Test Bowl (updated)",
            "instructions": "Mix it up well.",
            "base_servings": "1",
            "calories": "650",
            "protein": "45",
            "carbs": "60",
            "fat": "15",
            "ingredient_name": ["Chicken breast"],
            "ingredient_quantity": ["150"],
            "ingredient_unit": ["g"],
        },
    )
    assert "Test Bowl (updated)" in r.text
    assert "650" in r.text

    r = client.post(f"{recipe_url}/delete")
    r = client.get("/recipes")
    assert "Test Bowl" not in r.text


def test_recipe_ingredient_blank_trailing_row_is_ignored(client, seeded_household):
    login(client, "alice@example.com")
    r = client.post(
        "/recipes",
        data={
            "name": "Simple Dish",
            "instructions": "Do it.",
            "base_servings": "1",
            "calories": "400",
            "protein": "20",
            "carbs": "40",
            "fat": "10",
            "ingredient_name": ["Rice", ""],
            "ingredient_quantity": ["100", ""],
            "ingredient_unit": ["g", ""],
        },
    )
    assert r.status_code == 200
    assert "Rice" in r.text


def test_user_cannot_access_another_households_recipe(client, seeded_household, db_session):
    from datetime import datetime

    from app.models import Household, Recipe
    from app.security import generate_invite_code

    other_household = Household(
        Name="Other", InviteCode=generate_invite_code(), CreatedAt=datetime.utcnow()
    )
    db_session.add(other_household)
    db_session.flush()
    other_recipe = Recipe(
        HouseholdId=other_household.Id,
        CreatedByUserId=seeded_household["alice"].Id,
        Name="Not Yours",
        Instructions="Secret",
        BaseServings=1,
        CaloriesPerBaseServing=500,
        ProteinGramsPerBaseServing=30,
        CarbGramsPerBaseServing=50,
        FatGramsPerBaseServing=15,
        CreatedAt=datetime.utcnow(),
    )
    db_session.add(other_recipe)
    db_session.commit()

    login(client, "alice@example.com")
    r = client.get(f"/recipes/{other_recipe.Id}")
    assert r.status_code == 404
