from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PlannedBlock(Base):
    __tablename__ = "planned_blocks"

    Id: Mapped[int] = mapped_column(primary_key=True)
    HouseholdId: Mapped[int] = mapped_column(ForeignKey("households.Id"), nullable=False)
    StartDate: Mapped[date] = mapped_column(Date, nullable=False)
    EndDate: Mapped[date] = mapped_column(Date, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Household: Mapped["Household"] = relationship(back_populates="PlannedBlocks")
    Days: Mapped[list["PlannedDay"]] = relationship(
        back_populates="PlannedBlock", cascade="all, delete-orphan", order_by="PlannedDay.Date"
    )
    ShoppingList: Mapped["ShoppingList"] = relationship(
        back_populates="PlannedBlock", cascade="all, delete-orphan", uselist=False
    )


class PlannedDay(Base):
    __tablename__ = "planned_days"

    Id: Mapped[int] = mapped_column(primary_key=True)
    PlannedBlockId: Mapped[int] = mapped_column(ForeignKey("planned_blocks.Id"), nullable=False)
    Date: Mapped[date] = mapped_column(Date, nullable=False)
    DinnerRecipeId: Mapped[int] = mapped_column(ForeignKey("recipes.Id"), nullable=False)
    # Cooked twice (dinner + next day's lunch) for every block day except the
    # last, which is cooked as a single portion (PRD §5.4).
    PortionsCooked: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    # Set when no recipe fit every member's scale bound and the closest-fit
    # fallback was used instead (PRD §5.5).
    IsFlagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    PlannedBlock: Mapped["PlannedBlock"] = relationship(back_populates="Days")
    DinnerRecipe: Mapped["Recipe"] = relationship()
    Portions: Mapped[list["PlannedPortion"]] = relationship(
        back_populates="PlannedDay", cascade="all, delete-orphan"
    )
    MealLogs: Mapped[list["MealLog"]] = relationship(
        back_populates="PlannedDay", cascade="all, delete-orphan"
    )


class PlannedPortion(Base):
    __tablename__ = "planned_portions"

    Id: Mapped[int] = mapped_column(primary_key=True)
    PlannedDayId: Mapped[int] = mapped_column(ForeignKey("planned_days.Id"), nullable=False)
    UserId: Mapped[int] = mapped_column(ForeignKey("users.Id"), nullable=False)
    ScaleFactor: Mapped[float] = mapped_column(Float, nullable=False)
    Calories: Mapped[float] = mapped_column(Float, nullable=False)
    ProteinGrams: Mapped[float] = mapped_column(Float, nullable=False)
    CarbGrams: Mapped[float] = mapped_column(Float, nullable=False)
    FatGrams: Mapped[float] = mapped_column(Float, nullable=False)

    PlannedDay: Mapped["PlannedDay"] = relationship(back_populates="Portions")
    User: Mapped["User"] = relationship()
