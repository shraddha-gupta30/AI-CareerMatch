"""
Pydantic Schemas for Authentication and User Identity.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name of candidate")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def clean_full_name(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if len(cleaned) < 2:
                raise ValueError("Full name must contain at least 2 non-whitespace characters.")
            return cleaned
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
