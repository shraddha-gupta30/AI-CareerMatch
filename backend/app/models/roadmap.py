"""
Personalized Career Roadmap and Milestone Items Models.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"
    __table_args__ = (
        CheckConstraint("total_items >= 0", name="ck_roadmaps_total_items_positive"),
        CheckConstraint("completed_items >= 0", name="ck_roadmaps_completed_items_positive"),
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
    target_role: Mapped[str] = mapped_column(String(150), nullable=False)
    target_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="roadmaps")  # noqa: F821
    target_job: Mapped[Optional["Job"]] = relationship("Job", back_populates="roadmaps")  # noqa: F821
    items: Mapped[list["RoadmapItem"]] = relationship(
        "RoadmapItem",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapItem.sequence_order",
    )


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    __table_args__ = (
        CheckConstraint("estimated_hours > 0", name="ck_roadmap_items_hours_positive"),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_roadmap_items_status",
        ),
        CheckConstraint(
            "priority IN ('critical', 'high', 'medium', 'low')",
            name="ck_roadmap_items_priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    stage_phase: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    priority: Mapped[str] = mapped_column(String(30), default="high", nullable=False)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_project: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="not_started", nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="items")
    skill: Mapped[Optional["Skill"]] = relationship("Skill", back_populates="roadmap_items")  # noqa: F821
