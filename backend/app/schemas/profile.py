"""
Pydantic Schemas for Candidate Career Profile.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.auth import UserResponse


class ProfileUpdateRequest(BaseModel):
    target_role: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Target job title or career objective (e.g. 'Backend Engineer')",
    )
    headline: Optional[str] = Field(
        None,
        max_length=255,
        description="Professional headline (e.g. 'Senior Python & Cloud Architect')",
    )
    bio: Optional[str] = Field(
        None,
        max_length=5000,
        description="Professional summary or career background",
    )
    target_location: Optional[str] = Field(
        None,
        max_length=150,
        description="Preferred job location (e.g. 'Remote', 'Bengaluru, India')",
    )
    target_employment_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Desired employment type: Full-time, Part-time, Contract, Internship",
    )
    total_experience_years: float = Field(
        default=0.0,
        ge=0.0,
        le=60.0,
        description="Total relevant work experience in years",
    )

    @field_validator("target_role", mode="before")
    @classmethod
    def clean_target_role(cls, v: str) -> str:
        if isinstance(v, str):
            cleaned = v.strip()
            if len(cleaned) < 2:
                raise ValueError("Target role must be at least 2 characters.")
            return cleaned
        return v


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    headline: Optional[str] = None
    bio: Optional[str] = None
    target_role: str
    target_location: Optional[str] = None
    target_employment_type: Optional[str] = None
    total_experience_years: float
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    @field_validator("total_experience_years", mode="before")
    @classmethod
    def convert_decimal_to_float(cls, v: Any) -> float:
        if isinstance(v, Decimal):
            return float(v)
        return float(v) if v is not None else 0.0
