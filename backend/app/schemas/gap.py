"""
Pydantic Schemas for Skill Gap Analysis and What-If Career Simulator.
Provides request and response models for gap identification, experience analysis,
education compatibility, and in-memory simulation scenarios.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.job import EducationCompatibilityResponse, JobMatchBreakdownResponse


class MatchedSkillItem(BaseModel):
    name: str
    candidate_proficiency: str
    required_proficiency: str
    importance_weight: float
    credit: float
    is_exact: bool = True
    confidence: float = 1.0
    is_required: bool = True


class PartialSkillItem(BaseModel):
    job_skill_name: str
    candidate_skill_name: str
    similarity_weight: float
    credit: float
    candidate_proficiency: str
    required_proficiency: str
    is_required: bool = True


class MissingSkillItem(BaseModel):
    name: str
    required_proficiency: str
    importance_weight: float
    is_required: bool = True


class ExperienceGapDetail(BaseModel):
    candidate_experience_years: float
    job_min_experience_years: float
    experience_gap: float
    experience_gap_text: str
    experience_score: float


class SkillGapResponse(BaseModel):
    job_id: UUID
    overall_score: float = Field(..., ge=0.0, le=100.0)
    required_skills_score: float = Field(..., ge=0.0, le=100.0)
    preferred_skills_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    experience_score: float = Field(..., ge=0.0, le=100.0)
    education_score: float = Field(..., ge=0.0, le=100.0)

    # Required skills breakdown
    matched_required_skills: List[MatchedSkillItem] = Field(default_factory=list)
    partial_required_skills: List[PartialSkillItem] = Field(default_factory=list)
    missing_required_skills: List[MissingSkillItem] = Field(default_factory=list)

    # Preferred skills breakdown
    matched_preferred_skills: List[MatchedSkillItem] = Field(default_factory=list)
    partial_preferred_skills: List[PartialSkillItem] = Field(default_factory=list)
    missing_preferred_skills: List[MissingSkillItem] = Field(default_factory=list)

    # Dimension details
    experience_gap: ExperienceGapDetail
    education_compatibility: EducationCompatibilityResponse

    # Counts and weights
    total_required_skills_count: int
    matched_required_skills_count: int
    total_preferred_skills_count: int
    matched_preferred_skills_count: int
    active_weights: Dict[str, float]
    explanation: str


class SimulatedSkillInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    proficiency_level: str = Field(
        default="intermediate",
        description="Proficiency level: beginner, intermediate, advanced, expert",
    )
    proficiency_source: Optional[str] = Field(
        default="user_verified",
        description="Proficiency source: user_verified, resume_inferred, unknown",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Skill name cannot be empty or whitespace.")
        return s

    @field_validator("proficiency_level")
    @classmethod
    def validate_proficiency_level(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"beginner", "intermediate", "advanced", "expert"}:
            raise ValueError(f"Invalid proficiency level '{v}'. Allowed: beginner, intermediate, advanced, expert.")
        return s

    @field_validator("proficiency_source")
    @classmethod
    def validate_proficiency_source(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "user_verified"
        s = v.strip().lower()
        if s not in {"user_verified", "resume_inferred", "unknown"}:
            raise ValueError(f"Invalid proficiency source '{v}'. Allowed: user_verified, resume_inferred, unknown.")
        return s


class SimulationRequest(BaseModel):
    add_skills: Optional[List[SimulatedSkillInput]] = Field(
        default=None,
        description="Skills to add to candidate's simulated profile",
    )
    modify_skills: Optional[List[SimulatedSkillInput]] = Field(
        default=None,
        description="Existing skills to modify proficiency level in simulation",
    )
    remove_skills: Optional[List[str]] = Field(
        default=None,
        description="Skill names to remove from candidate's simulated profile",
    )
    experience_years: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=60.0,
        description="Simulated total experience years (must be non-negative)",
    )

    @field_validator("remove_skills")
    @classmethod
    def validate_remove_skills(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        cleaned = []
        for s in v:
            c = s.strip()
            if c:
                cleaned.append(c)
        return cleaned


class SimulationResponse(BaseModel):
    job_id: UUID
    current_score: float = Field(..., ge=0.0, le=100.0)
    simulated_score: float = Field(..., ge=0.0, le=100.0)
    score_delta: float
    current_match: JobMatchBreakdownResponse
    simulated_match: JobMatchBreakdownResponse
    changed_factors: List[str] = Field(default_factory=list)
