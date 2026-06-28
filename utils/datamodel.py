from datetime import date
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, ConfigDict, Field, EmailStr

#SQLALCHEMY Setup

Base = declarative_base()

class User(Base):
    __tablename__ = 'Users'
    Id = sa.Column('Id', sa.Integer, primary_key=True)
    Name = sa.Column('Name', sa.String(255), nullable=False)
    Email = sa.Column('Email', sa.String(255),unique=True, nullable=False)
    DOB = sa.Column('DOB', sa.Date, nullable=False)
    isBornMale = sa.Column('isBornMale', sa.Boolean, nullable=False)
    Height = sa.Column('Height', sa.Float, nullable=False)
    Weight = sa.Column('Weight', sa.Float, nullable=False)
    GoalWeight = sa.Column('GoalWeight', sa.Float, nullable=False)
    GoalDate = sa.Column('GoalDate', sa.Date, nullable=True)
    TrainingsPerWeek = sa.Column('TraingsPerWeek', sa.Integer, nullable=False)
    metadata_ = sa.Column('metadata', sa.JSON)


#Pydantic Setup

class UserModel(BaseModel):
    Id: int
    Name: str
    Email: EmailStr
    DOB: date
    isBornMale: bool
    Height: float
    Weight: float
    GoalWeight: float
    GoalDate: date
    TrainingsPerWeek: int
