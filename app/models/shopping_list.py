from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    Id: Mapped[int] = mapped_column(primary_key=True)
    PlannedBlockId: Mapped[int] = mapped_column(
        ForeignKey("planned_blocks.Id"), unique=True, nullable=False
    )
    GeneratedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    PlannedBlock: Mapped["PlannedBlock"] = relationship(back_populates="ShoppingList")
    Items: Mapped[list["ShoppingListItem"]] = relationship(
        back_populates="ShoppingList", cascade="all, delete-orphan"
    )


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    Id: Mapped[int] = mapped_column(primary_key=True)
    ShoppingListId: Mapped[int] = mapped_column(ForeignKey("shopping_lists.Id"), nullable=False)
    IngredientId: Mapped[int] = mapped_column(ForeignKey("ingredients.Id"), nullable=False)
    TotalQuantity: Mapped[float] = mapped_column(Float, nullable=False)
    Unit: Mapped[str] = mapped_column(String(32), nullable=False)
    Checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    ShoppingList: Mapped["ShoppingList"] = relationship(back_populates="Items")
    Ingredient: Mapped["Ingredient"] = relationship()
