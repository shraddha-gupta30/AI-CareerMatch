"""
Skills Taxonomy, Aliases, Explicit Relationships, and Prerequisites Models.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    String,
    DateTime,
    Integer,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    normalized_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    aliases: Mapped[list["SkillAlias"]] = relationship(
        "SkillAlias",
        back_populates="skill",
        cascade="all, delete-orphan",
    )
    candidate_skills: Mapped[list["CandidateSkill"]] = relationship(  # noqa: F821
        "CandidateSkill",
        back_populates="skill",
    )
    job_skills: Mapped[list["JobSkill"]] = relationship(  # noqa: F821
        "JobSkill",
        back_populates="skill",
    )
    roadmap_items: Mapped[list["RoadmapItem"]] = relationship(  # noqa: F821
        "RoadmapItem",
        back_populates="skill",
    )


class SkillAlias(Base):
    __tablename__ = "skill_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    skill: Mapped["Skill"] = relationship("Skill", back_populates="aliases")


class SkillRelationship(Base):
    """
    Explicitly configured transferable/related skill relationships.
    Sole source for partial skill matching credit under the approved matching engine.
    """
    __tablename__ = "skill_relationships"
    __table_args__ = (
        UniqueConstraint("source_skill_id", "target_skill_id", name="uq_skill_relationships_source_target"),
        CheckConstraint("source_skill_id != target_skill_id", name="ck_skill_relationships_no_self"),
        CheckConstraint("similarity_weight > 0.0 AND similarity_weight <= 1.0", name="ck_skill_relationships_weight_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50),
        default="transferable",
        nullable=False,
    )
    similarity_weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    source_skill: Mapped["Skill"] = relationship("Skill", foreign_keys=[source_skill_id])
    target_skill: Mapped["Skill"] = relationship("Skill", foreign_keys=[target_skill_id])


class SkillPrerequisite(Base):
    """
    Skill dependency hierarchy for deterministic DAG-based roadmap ordering.
    """
    __tablename__ = "skill_prerequisites"
    __table_args__ = (
        UniqueConstraint("skill_id", "prerequisite_skill_id", name="uq_skill_prerequisites_skill_prereq"),
        CheckConstraint("skill_id != prerequisite_skill_id", name="ck_skill_prerequisites_no_self"),
        CheckConstraint("difficulty_tier >= 1 AND difficulty_tier <= 5", name="ck_skill_prerequisites_tier_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    prerequisite_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    difficulty_tier: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    skill: Mapped["Skill"] = relationship("Skill", foreign_keys=[skill_id])
    prerequisite_skill: Mapped["Skill"] = relationship("Skill", foreign_keys=[prerequisite_skill_id])
