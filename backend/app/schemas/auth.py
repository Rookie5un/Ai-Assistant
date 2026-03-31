from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    role: str
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    display_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

