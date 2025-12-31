from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole, Department


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.OFFICIAL
    department: Optional[Department] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    department: Optional[Department] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
