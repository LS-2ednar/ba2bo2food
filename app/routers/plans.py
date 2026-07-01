from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_user
from app.models import (
    MealLog,
    MealLogStatus,
    MealSlot,
    PlannedBlock,
    PlannedDay,
    PlannedPortion,
    Recipe,
    ShoppingList,
    ShoppingListItem,
    User,
)
from app.services.calorie_targets import calculate_calorie_target
from app.services.planning import (
    Diner,
    InsufficientRecipesError,
    PlannableRecipe,
    generate_block_plan,
)
from app.services.shopping_list import RecipeIngredientLine, build_shopping_list
from app.templating import render

router = APIRouter()


def _get_household_block(db: Session, block_id: int, user: User) -> PlannedBlock:
    block = db.get(PlannedBlock, block_id)
    if block is None or block.HouseholdId != user.HouseholdId:
        raise HTTPException(status_code=404)
    return block


@router.get("/plans")
def list_plans(
    request: Request, db: Session = Depends(get_db), user: User = Depends(require_user)
):
    blocks = (
        db.query(PlannedBlock)
        .filter(PlannedBlock.HouseholdId == user.HouseholdId)
        .order_by(PlannedBlock.StartDate.desc())
        .all()
    )
    return render(request, "plans/list.html", {"blocks": blocks}, user=user)


@router.get("/plans/new")
def new_plan_form(request: Request, user: User = Depends(require_user)):
    return render(request, "plans/form.html", user=user)


@router.post("/plans")
def create_plan(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    start_date: date = Form(...),
    length: int = Form(...),
):
    length = max(1, min(7, length))
    members = db.query(User).filter(User.HouseholdId == user.HouseholdId).all()
    recipes = db.query(Recipe).filter(Recipe.HouseholdId == user.HouseholdId).all()

    diners = []
    for member in members:
        target = calculate_calorie_target(
            weight_kg=member.Weight,
            height_cm=member.Height,
            dob=member.DOB,
            is_born_male=member.IsBornMale,
            trainings_per_week=member.TrainingsPerWeek,
            goal_weight_kg=member.GoalWeight,
            goal_date=member.GoalDate,
            today=start_date,
        )
        diners.append(Diner(user_id=member.Id, dinner_target_calories=target.daily_target / 2))

    library = [
        PlannableRecipe(recipe_id=r.Id, calories_per_base_serving=r.CaloriesPerBaseServing)
        for r in recipes
    ]

    try:
        assignments = generate_block_plan(diners, library, length)
    except InsufficientRecipesError:
        return render(
            request,
            "plans/form.html",
            {"error_key": "errors.insufficient_recipes"},
            user=user,
            status_code=400,
        )

    recipes_by_id = {r.Id: r for r in recipes}

    block = PlannedBlock(
        HouseholdId=user.HouseholdId,
        StartDate=start_date,
        EndDate=start_date + timedelta(days=length - 1),
        CreatedAt=datetime.utcnow(),
    )
    db.add(block)
    db.flush()

    for day_index, assignment in enumerate(assignments):
        recipe = recipes_by_id[assignment.recipe_id]
        planned_day = PlannedDay(
            PlannedBlockId=block.Id,
            Date=start_date + timedelta(days=day_index),
            DinnerRecipeId=assignment.recipe_id,
            PortionsCooked=assignment.portions_cooked,
            IsFlagged=assignment.is_flagged,
        )
        db.add(planned_day)
        db.flush()
        for portion in assignment.portions:
            db.add(
                PlannedPortion(
                    PlannedDayId=planned_day.Id,
                    UserId=portion.user_id,
                    ScaleFactor=portion.scale_factor,
                    Calories=portion.calories,
                    ProteinGrams=portion.scale_factor * recipe.ProteinGramsPerBaseServing,
                    CarbGrams=portion.scale_factor * recipe.CarbGramsPerBaseServing,
                    FatGrams=portion.scale_factor * recipe.FatGramsPerBaseServing,
                )
            )

    ingredient_lines_by_recipe = {
        recipe.Id: [
            RecipeIngredientLine(
                ingredient_id=ri.IngredientId,
                quantity_per_base_serving=ri.Quantity,
                unit=ri.Unit,
            )
            for ri in recipe.Ingredients
        ]
        for recipe in recipes
    }
    shopping_lines = build_shopping_list(assignments, ingredient_lines_by_recipe)

    shopping_list = ShoppingList(PlannedBlockId=block.Id, GeneratedAt=datetime.utcnow())
    db.add(shopping_list)
    db.flush()
    for line in shopping_lines:
        db.add(
            ShoppingListItem(
                ShoppingListId=shopping_list.Id,
                IngredientId=line.ingredient_id,
                TotalQuantity=line.total_quantity,
                Unit=line.unit,
            )
        )

    db.commit()
    return RedirectResponse(f"/plans/{block.Id}", status_code=303)


@router.get("/plans/{block_id}")
def plan_detail(
    request: Request,
    block_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    block = _get_household_block(db, block_id, user)
    my_logs = {
        (log.PlannedDayId, log.MealType.value): log
        for log in db.query(MealLog).filter(MealLog.UserId == user.Id).all()
    }
    return render(
        request, "plans/detail.html", {"block": block, "my_logs": my_logs}, user=user
    )


@router.post("/plans/{block_id}/days/{day_id}/meals/{meal_type}/log")
def log_meal(
    block_id: int,
    day_id: int,
    meal_type: MealSlot,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
    status: MealLogStatus = Form(...),
    note: str = Form(""),
):
    _get_household_block(db, block_id, user)
    day = db.get(PlannedDay, day_id)
    if day is None or day.PlannedBlockId != block_id:
        raise HTTPException(status_code=404)
    log = (
        db.query(MealLog)
        .filter(
            MealLog.PlannedDayId == day_id,
            MealLog.UserId == user.Id,
            MealLog.MealType == meal_type,
        )
        .first()
    )
    if log is None:
        log = MealLog(UserId=user.Id, PlannedDayId=day_id, MealType=meal_type)
        db.add(log)
    log.Status = status
    log.Note = note or None
    log.LoggedAt = datetime.utcnow()
    db.commit()
    return RedirectResponse(f"/plans/{block_id}", status_code=303)


@router.get("/plans/{block_id}/shopping-list")
def shopping_list_detail(
    request: Request,
    block_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    block = _get_household_block(db, block_id, user)
    return render(request, "plans/shopping_list.html", {"block": block}, user=user)


@router.post("/plans/{block_id}/shopping-list/items/{item_id}/check")
def toggle_shopping_list_item(
    request: Request,
    block_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    block = _get_household_block(db, block_id, user)
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.ShoppingListId != block.ShoppingList.Id:
        raise HTTPException(status_code=404)
    item.Checked = not item.Checked
    db.commit()
    return render(request, "plans/_shopping_list_item.html", {"item": item}, user=user)
