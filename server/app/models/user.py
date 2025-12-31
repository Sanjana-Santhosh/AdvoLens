from sqlalchemy import Column, Integer, String, Enum
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"  # Can reassign, delete, manage users
    OFFICIAL = "official"        # Can only resolve issues in their dept


class Department(str, enum.Enum):
    MUNICIPALITY = "municipality"       # Garbage, Cleaning
    WATER_AUTHORITY = "water_authority"  # Pipe leaks, Sewage
    KSEB = "kseb"                        # Streetlights, Power lines
    PWD = "pwd"                          # Roads, Potholes
    OTHER = "other"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    # Use native_enum=True and values_callable to match lowercase DB values
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x], native_enum=True, create_constraint=False),
        default=UserRole.OFFICIAL
    )
    department = Column(
        Enum(Department, values_callable=lambda x: [e.value for e in x], native_enum=True, create_constraint=False),
        nullable=True
    )
