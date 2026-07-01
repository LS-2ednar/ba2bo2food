from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    Id: Mapped[int] = mapped_column(primary_key=True)
    HouseholdId: Mapped[int] = mapped_column(ForeignKey("households.Id"), nullable=False)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    PasswordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    DOB: Mapped[date] = mapped_column(Date, nullable=False)
    IsBornMale: Mapped[bool] = mapped_column(Boolean, nullable=False)
    Height: Mapped[float] = mapped_column(Float, nullable=False)
    Weight: Mapped[float] = mapped_column(Float, nullable=False)
    GoalWeight: Mapped[float] = mapped_column(Float, nullable=False)
    GoalDate: Mapped[date] = mapped_column(Date, nullable=False)
    TrainingsPerWeek: Mapped[int] = mapped_column(Integer, nullable=False)
    Locale: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Household: Mapped["Household"] = relationship(back_populates="Users")
    WeightCheckIns: Mapped[list["WeightCheckIn"]] = relationship(
        back_populates="User", cascade="all, delete-orphan", order_by="WeightCheckIn.RecordedAt"
    )
