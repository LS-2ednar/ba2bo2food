from datetime import date

from sqlalchemy import Date, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WeightCheckIn(Base):
    __tablename__ = "weight_checkins"

    Id: Mapped[int] = mapped_column(primary_key=True)
    UserId: Mapped[int] = mapped_column(ForeignKey("users.Id"), nullable=False)
    Weight: Mapped[float] = mapped_column(Float, nullable=False)
    RecordedAt: Mapped[date] = mapped_column(Date, nullable=False)

    User: Mapped["User"] = relationship(back_populates="WeightCheckIns")
