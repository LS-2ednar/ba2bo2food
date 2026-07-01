from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    Id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class Recipe(Base):
    __tablename__ = "recipes"

    Id: Mapped[int] = mapped_column(primary_key=True)
    HouseholdId: Mapped[int] = mapped_column(ForeignKey("households.Id"), nullable=False)
    CreatedByUserId: Mapped[int] = mapped_column(ForeignKey("users.Id"), nullable=False)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Instructions: Mapped[str] = mapped_column(Text, nullable=False)
    BaseServings: Mapped[int] = mapped_column(Integer, nullable=False)
    CaloriesPerBaseServing: Mapped[float] = mapped_column(Float, nullable=False)
    ProteinGramsPerBaseServing: Mapped[float] = mapped_column(Float, nullable=False)
    CarbGramsPerBaseServing: Mapped[float] = mapped_column(Float, nullable=False)
    FatGramsPerBaseServing: Mapped[float] = mapped_column(Float, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Household: Mapped["Household"] = relationship(back_populates="Recipes")
    CreatedByUser: Mapped["User"] = relationship()
    Ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="Recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    Id: Mapped[int] = mapped_column(primary_key=True)
    RecipeId: Mapped[int] = mapped_column(ForeignKey("recipes.Id"), nullable=False)
    IngredientId: Mapped[int] = mapped_column(ForeignKey("ingredients.Id"), nullable=False)
    Quantity: Mapped[float] = mapped_column(Float, nullable=False)
    Unit: Mapped[str] = mapped_column(String(32), nullable=False)

    Recipe: Mapped["Recipe"] = relationship(back_populates="Ingredients")
    Ingredient: Mapped["Ingredient"] = relationship()
