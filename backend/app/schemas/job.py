"""
Pydantic Schemas for Job Postings, Saved Jobs, Discovery Filters, and Match Evaluation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class JobSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    skill_id: UUID
    name: str
    category: Optional[str] = None
    is_required: bool
    importance_weight: float
    min_proficiency: str


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str
    location: str
    employment_type: str
    experience_level: str
    min_experience_years: float
    target_education_level: str
    description: str
    salary_range: Optional[str] = None
    is_active: bool
    created_at: datetime
    skills: List[JobSkillResponse] = Field(default_factory=list)
    is_saved: bool = False
    match_score: Optional[float] = None


class JobDetailResponse(JobResponse):
    cached_match: Optional[Dict[str, Any]] = None


class PaginatedJobsResponse(BaseModel):
    items: List[JobResponse]
    total: int
    page: int
    limit: int
    pages: int


class SavedJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    created_at: datetime
    job: JobResponse


class EducationCompatibilityResponse(BaseModel):
    candidate_highest_level: str
    required_level: str
    meets_requirement: bool
    score: float
    explanation: str


class JobMatchBreakdownResponse(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    required_skills_score: float = Field(..., ge=0.0, le=100.0)
    preferred_skills_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    experience_score: float = Field(..., ge=0.0, le=100.0)
    education_score: float = Field(..., ge=0.0, le=100.0)
    matched_skills: List[Dict[str, Any]] = Field(default_factory=list)
    partial_skills: List[Dict[str, Any]] = Field(default_factory=list)
    missing_required_skills: List[Dict[str, Any]] = Field(default_factory=list)
    missing_preferred_skills: List[Dict[str, Any]] = Field(default_factory=list)
    experience_gap: float
    experience_gap_text: str
    education_compatibility: EducationCompatibilityResponse
    total_required_skills_count: int
    matched_required_skills_count: int
    total_preferred_skills_count: int
    matched_preferred_skills_count: int
    active_weights: Dict[str, float]
    explanation: str
