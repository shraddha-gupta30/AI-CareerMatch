"""
User Entity Model.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
    profile: Mapped["CandidateProfile"] = relationship(  # noqa: F821
        "CandidateProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    resumes: Mapped[list["Resume"]] = relationship(  # noqa: F821
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activities: Mapped[list["CandidateActivity"]] = relationship(  # noqa: F821
        "CandidateActivity",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_jobs: Mapped[list["SavedJob"]] = relationship(  # noqa: F821
        "SavedJob",
        back_populates="user",
        cascade="all, delete-orphan",
    )
