from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Household(Base):
    __tablename__ = "households"

    Id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    InviteCode: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    Users: Mapped[list["User"]] = relationship(back_populates="Household")
    Recipes: Mapped[list["Recipe"]] = relationship(back_populates="Household")
    PlannedBlocks: Mapped[list["PlannedBlock"]] = relationship(back_populates="Household")
