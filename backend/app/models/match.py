"""
Job Matches Evaluation Model.
Persists deterministic scoring results, itemized breakdown, and AI explainability narrative.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import (
    DateTime,
    Numeric,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint("profile_id", "job_id", name="uq_job_matches_profile_job"),
        CheckConstraint("overall_score >= 0.0 AND overall_score <= 100.0", name="ck_job_matches_overall_range"),
        CheckConstraint("skill_score >= 0.0 AND skill_score <= 100.0", name="ck_job_matches_skill_range"),
        CheckConstraint("experience_score >= 0.0 AND experience_score <= 100.0", name="ck_job_matches_exp_range"),
        CheckConstraint("education_score >= 0.0 AND education_score <= 100.0", name="ck_job_matches_edu_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    skill_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    experience_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    education_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    breakdown_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    ai_explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="matches")  # noqa: F821
    job: Mapped["Job"] = relationship("Job", back_populates="matches")  # noqa: F821
