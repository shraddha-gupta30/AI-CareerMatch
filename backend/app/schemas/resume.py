"""
Pydantic Schemas for Resume Upload, AI Structured Extraction, and Staging Review.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtractedSkillItem(BaseModel):
    name: str = Field(..., description="Skill name as extracted from resume")
    proficiency_level: str = Field(
        default="intermediate",
        description="Proficiency: beginner, intermediate, advanced, expert",
    )
    years_experience: Optional[float] = Field(
        default=1.0,
        description="Estimated years of experience with this skill",
    )

    @field_validator("years_experience", mode="before")
    @classmethod
    def _sanitize_years(cls, v):
        if v is None:
            return 1.0
        try:
            val = float(v)
            return max(0.0, val)
        except (TypeError, ValueError):
            return 1.0

    canonical_skill_id: Optional[UUID] = Field(
        default=None,
        description="UUID of matched skill in master taxonomy if found",
    )
    canonical_name: Optional[str] = Field(
        default=None,
        description="Canonical name in master taxonomy",
    )
    category: Optional[str] = Field(
        default=None,
        description="Taxonomy cluster/category (e.g. backend, database, cloud)",
    )
    matched: bool = Field(
        default=False,
        description="True if matched to existing platform taxonomy or alias",
    )
    proficiency_source: str = Field(
        default="resume_inferred",
        description="Source tracking: 'resume_inferred', 'user_verified', or 'unknown'",
    )
    is_verified: bool = Field(
        default=False,
        description="Set to True once confirmed by candidate in staging review",
    )


class ExtractedEducationItem(BaseModel):
    institution: Optional[str] = Field(default="Unknown Institution", description="University, College, or School")
    degree: Optional[str] = Field(default="Degree", description="Degree type (e.g. Bachelor of Science)")
    field_of_study: Optional[str] = Field(default="General Studies", description="Major or specialization")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD or YYYY)")
    end_date: Optional[str] = Field(None, description="End/Graduation date (YYYY-MM-DD or YYYY)")
    grade_gpa: Optional[str] = Field(None, description="GPA or grade honors")

    @field_validator("institution", mode="before")
    @classmethod
    def _sanitize_inst(cls, v):
        return str(v).strip() if v else "Unknown Institution"

    @field_validator("degree", mode="before")
    @classmethod
    def _sanitize_deg(cls, v):
        return str(v).strip() if v else "Degree"

    @field_validator("field_of_study", mode="before")
    @classmethod
    def _sanitize_fos(cls, v):
        return str(v).strip() if v else "General Studies"


class ExtractedExperienceItem(BaseModel):
    company: Optional[str] = Field(default="Company", description="Employer or organization name")
    title: Optional[str] = Field(default="Role", description="Job title")
    location: Optional[str] = Field(None, description="City, State, or Remote")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD or YYYY-MM)")
    end_date: Optional[str] = Field(None, description="End date (None if current)")
    is_current: bool = Field(default=False, description="True if currently employed")
    description: Optional[str] = Field(None, description="Role summary and accomplishments")
    technologies: List[str] = Field(
        default_factory=list,
        description="Key technologies and tools utilized in this role",
    )

    @field_validator("company", mode="before")
    @classmethod
    def _sanitize_comp(cls, v):
        return str(v).strip() if v else "Company"

    @field_validator("title", mode="before")
    @classmethod
    def _sanitize_tit(cls, v):
        return str(v).strip() if v else "Role"


class ExtractedProjectItem(BaseModel):
    title: Optional[str] = Field(default="Project", description="Project name")
    description: Optional[str] = Field(default="", description="Project overview and tech stack")
    repository_url: Optional[str] = Field(None, description="Git/GitHub repository URL")
    live_url: Optional[str] = Field(None, description="Live deployment or demo URL")
    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies utilized in the project",
    )

    @field_validator("title", mode="before")
    @classmethod
    def _sanitize_proj_title(cls, v):
        return str(v).strip() if v else "Project"

    @field_validator("description", mode="before")
    @classmethod
    def _sanitize_proj_desc(cls, v):
        return str(v).strip() if v else ""


class ExtractedCertificationItem(BaseModel):
    name: Optional[str] = Field(default="Certification", description="Certification name")
    issuing_organization: Optional[str] = Field(default="Organization", description="Issuing body (e.g. AWS, Microsoft, Google)")
    issue_date: Optional[str] = Field(None, description="Date issued (YYYY-MM-DD or YYYY)")
    credential_id: Optional[str] = Field(None, description="Credential ID")
    credential_url: Optional[str] = Field(None, description="Verification URL")

    @field_validator("name", mode="before")
    @classmethod
    def _sanitize_cert_name(cls, v):
        return str(v).strip() if v else "Certification"

    @field_validator("issuing_organization", mode="before")
    @classmethod
    def _sanitize_cert_org(cls, v):
        return str(v).strip() if v else "Organization"



class StructuredResumeData(BaseModel):
    """Structured candidate data extracted from resume for staging review."""
    full_name: Optional[str] = Field(None, description="Candidate name as parsed from resume")
    headline: Optional[str] = Field(None, description="Professional headline inferred from resume")
    bio: Optional[str] = Field(None, description="Professional summary or bio")
    target_role: Optional[str] = Field(None, description="Inferred target or recent role")
    target_location: Optional[str] = Field(None, description="Location or remote preference")
    target_employment_type: Optional[str] = Field("Full-time", description="Target employment type")
    total_experience_years: Optional[float] = Field(0.0, description="Calculated total experience in years")

    @field_validator("total_experience_years", mode="before")
    @classmethod
    def _sanitize_total_years(cls, v):
        if v is None:
            return 0.0
        try:
            val = float(v)
            return max(0.0, val)
        except (TypeError, ValueError):
            return 0.0

    skills: List[ExtractedSkillItem] = Field(default_factory=list)
    education: List[ExtractedEducationItem] = Field(default_factory=list)
    experience: List[ExtractedExperienceItem] = Field(default_factory=list)
    projects: List[ExtractedProjectItem] = Field(default_factory=list)
    certifications: List[ExtractedCertificationItem] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    file_name: str
    file_size_bytes: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime


class ResumeDetailResponse(ResumeResponse):
    parsed_staging_json: Optional[Dict[str, Any]] = None
