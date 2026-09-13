"""
Job Postings and Required/Preferred Skills Models.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("min_experience_years >= 0.0", name="ck_jobs_exp_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(50), default="full-time", nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), default="entry", nullable=False)
    min_experience_years: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        default=Decimal("0.0"),
        nullable=False,
    )
    target_education_level: Mapped[str] = mapped_column(String(100), default="Bachelor", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    salary_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    job_skills: Mapped[list["JobSkill"]] = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    matches: Mapped[list["JobMatch"]] = relationship(  # noqa: F821
        "JobMatch",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    roadmaps: Mapped[list["Roadmap"]] = relationship(  # noqa: F821
        "Roadmap",
        back_populates="target_job",
    )
    saved_by: Mapped[list["SavedJob"]] = relationship(
        "SavedJob",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class JobSkill(Base):
    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        CheckConstraint("importance_weight >= 0.5 AND importance_weight <= 2.0", name="ck_job_skills_weight_range"),
        CheckConstraint("min_proficiency IN ('beginner', 'intermediate', 'advanced', 'expert')", name="ck_job_skills_min_proficiency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    importance_weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("1.00"),
        nullable=False,
    )
    min_proficiency: Mapped[str] = mapped_column(
        String(30),
        default="intermediate",
        nullable=False,
    )

    job: Mapped["Job"] = relationship("Job", back_populates="job_skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="job_skills")  # noqa: F821


class SavedJob(Base):
    """
    Persisted saved / bookmarked job records for authenticated candidates.
    Enforces user isolation and single-save idempotency via unique composite constraint.
    """
    __tablename__ = "saved_jobs"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="saved_jobs")  # noqa: F821
    job: Mapped["Job"] = relationship("Job", back_populates="saved_by")

