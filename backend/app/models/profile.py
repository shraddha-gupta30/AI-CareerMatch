"""
Candidate Profile, Skills, Education, Experience, Projects, and Certifications Models.
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (
        CheckConstraint("total_experience_years >= 0.0", name="ck_candidate_profiles_exp_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_role: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    target_location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    target_employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    total_experience_years: Mapped[Decimal] = mapped_column(
        Numeric(4, 1),
        default=Decimal("0.0"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")  # noqa: F821
    skills: Mapped[list["CandidateSkill"]] = relationship(
        "CandidateSkill",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    education: Mapped[list["Education"]] = relationship(
        "Education",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    experience: Mapped[list["Experience"]] = relationship(
        "Experience",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    certifications: Mapped[list["Certification"]] = relationship(
        "Certification",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    matches: Mapped[list["JobMatch"]] = relationship(  # noqa: F821
        "JobMatch",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    roadmaps: Mapped[list["Roadmap"]] = relationship(  # noqa: F821
        "Roadmap",
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        UniqueConstraint("profile_id", "skill_id", name="uq_candidate_skills_profile_skill"),
        CheckConstraint("years_experience >= 0.0", name="ck_candidate_skills_exp_positive"),
        CheckConstraint("proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')", name="ck_candidate_skills_level"),
        CheckConstraint("proficiency_source IN ('user_verified', 'resume_inferred', 'unknown')", name="ck_candidate_skills_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
    )
    proficiency_level: Mapped[str] = mapped_column(
        String(30),
        default="intermediate",
        nullable=False,
    )
    years_experience: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        default=Decimal("1.0"),
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    proficiency_source: Mapped[str] = mapped_column(
        String(30),
        default="user_verified",
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="candidate_skills")  # noqa: F821


class Education(Base):
    __tablename__ = "education"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(150), nullable=False)
    field_of_study: Mapped[str] = mapped_column(String(150), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    grade_gpa: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="education")


class Experience(Base):
    __tablename__ = "experience"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    technologies: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="experience")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    technologies: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="projects")


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credential_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="certifications")
