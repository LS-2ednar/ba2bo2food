import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MealSlot(str, enum.Enum):
    DINNER = "dinner"
    LUNCH = "lunch"


class MealLogStatus(str, enum.Enum):
    EATEN = "eaten"
    SKIPPED = "skipped"
    SWAPPED = "swapped"


class MealLog(Base):
    __tablename__ = "meal_logs"

    Id: Mapped[int] = mapped_column(primary_key=True)
    UserId: Mapped[int] = mapped_column(ForeignKey("users.Id"), nullable=False)
    PlannedDayId: Mapped[int] = mapped_column(ForeignKey("planned_days.Id"), nullable=False)
    MealType: Mapped[MealSlot] = mapped_column(Enum(MealSlot), nullable=False)
    Status: Mapped[MealLogStatus] = mapped_column(Enum(MealLogStatus), nullable=False)
    Note: Mapped[str | None] = mapped_column(Text, nullable=True)
    LoggedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    User: Mapped["User"] = relationship()
    PlannedDay: Mapped["PlannedDay"] = relationship(back_populates="MealLogs")
