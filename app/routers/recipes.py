from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_user
from app.models import Ingredient, Recipe, RecipeIngredient, User
from app.templating import render

router = APIRouter()


def _get_household_recipe(db: Session, recipe_id: int, user: User) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.HouseholdId != user.HouseholdId:
        raise HTTPException(status_code=404)
    return recipe


def _get_or_create_ingredient(db: Session, name: str) -> Ingredient:
    name = name.strip()
    ingredient = db.query(Ingredient).filter(Ingredient.Name.ilike(name)).first()
    if ingredient is None:
        ingredient = Ingredient(Name=name)
        db.add(ingredient)
        db.flush()
    return ingredient


def _all_ingredient_names(db: Session) -> list[str]:
    return [name for (name,) in db.query(Ingredient.Name).order_by(Ingredient.Name).all()]


def _apply_ingredient_lines(
    db: Session,
    recipe: Recipe,
    names: list[str],
    quantities: list[str],
    units: list[str],
) -> None:
    recipe.Ingredients.clear()
    for name, quantity, unit in zip(names, quantities, units):
        if not name.strip() or not quantity.strip():
            continue
        try:
            quantity_value = float(quantity)
        except ValueError:
            continue
        ingredient = _get_or_create_ingredient(db, name)
        recipe.Ingredients.append(
            RecipeIngredient(IngredientId=ingredient.Id, Quantity=quantity_value, Unit=unit.strip())
        )


@router.get("/recipes")
def list_recipes(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    recipes = (
        db.query(Recipe)
        .filter(Recipe.HouseholdId == user.HouseholdId)
        .order_by(Recipe.Name)
        .all()
    )
    return render(request, "recipes/list.html", {"recipes": recipes}, user=user)


@router.get("/recipes/new")
def new_recipe_form(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    return render(
        request,
        "recipes/form.html",
        {"recipe": None, "ingredient_names": _all_ingredient_names(db)},
        user=user,
    )


@router.get("/recipes/ingredient-row")
def ingredient_row(request: Request, user: User = Depends(require_user)):
    return render(request, "recipes/_ingredient_row.html", user=user)


@router.post("/recipes")
def create_recipe(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    name: str = Form(...),
    instructions: str = Form(...),
    base_servings: int = Form(...),
    calories: float = Form(...),
    protein: float = Form(...),
    carbs: float = Form(...),
    fat: float = Form(...),
    ingredient_name: list[str] = Form(default=[]),
    ingredient_quantity: list[str] = Form(default=[]),
    ingredient_unit: list[str] = Form(default=[]),
):
    recipe = Recipe(
        HouseholdId=user.HouseholdId,
        CreatedByUserId=user.Id,
        Name=name,
        Instructions=instructions,
        BaseServings=base_servings,
        CaloriesPerBaseServing=calories,
        ProteinGramsPerBaseServing=protein,
        CarbGramsPerBaseServing=carbs,
        FatGramsPerBaseServing=fat,
        CreatedAt=datetime.utcnow(),
    )
    db.add(recipe)
    db.flush()
    _apply_ingredient_lines(db, recipe, ingredient_name, ingredient_quantity, ingredient_unit)
    db.commit()
    return RedirectResponse(f"/recipes/{recipe.Id}", status_code=303)


@router.get("/recipes/{recipe_id}")
def recipe_detail(
    request: Request,
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    recipe = _get_household_recipe(db, recipe_id, user)
    return render(request, "recipes/detail.html", {"recipe": recipe}, user=user)


@router.get("/recipes/{recipe_id}/edit")
def edit_recipe_form(
    request: Request,
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    recipe = _get_household_recipe(db, recipe_id, user)
    return render(
        request,
        "recipes/form.html",
        {"recipe": recipe, "ingredient_names": _all_ingredient_names(db)},
        user=user,
    )


@router.post("/recipes/{recipe_id}/edit")
def edit_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    name: str = Form(...),
    instructions: str = Form(...),
    base_servings: int = Form(...),
    calories: float = Form(...),
    protein: float = Form(...),
    carbs: float = Form(...),
    fat: float = Form(...),
    ingredient_name: list[str] = Form(default=[]),
    ingredient_quantity: list[str] = Form(default=[]),
    ingredient_unit: list[str] = Form(default=[]),
):
    recipe = _get_household_recipe(db, recipe_id, user)
    recipe.Name = name
    recipe.Instructions = instructions
    recipe.BaseServings = base_servings
    recipe.CaloriesPerBaseServing = calories
    recipe.ProteinGramsPerBaseServing = protein
    recipe.CarbGramsPerBaseServing = carbs
    recipe.FatGramsPerBaseServing = fat
    _apply_ingredient_lines(db, recipe, ingredient_name, ingredient_quantity, ingredient_unit)
    db.commit()
    return RedirectResponse(f"/recipes/{recipe.Id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete")
def delete_recipe(
    recipe_id: int, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    recipe = _get_household_recipe(db, recipe_id, user)
    db.delete(recipe)
    db.commit()
    return RedirectResponse("/recipes", status_code=303)
