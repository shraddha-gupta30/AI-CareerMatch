"""
Domain Database Models Registry.
Exposes all models for Alembic migrations and application usage.
"""
from app.db.base import Base
from app.models.user import User
from app.models.profile import (
    CandidateProfile,
    CandidateSkill,
    Education,
    Experience,
    Project,
    Certification,
)
from app.models.skill import (
    Skill,
    SkillAlias,
    SkillRelationship,
    SkillPrerequisite,
)
from app.models.job import Job, JobSkill, SavedJob
from app.models.match import JobMatch
from app.models.resume import Resume
from app.models.roadmap import Roadmap, RoadmapItem
from app.models.activity import CandidateActivity

__all__ = [
    "Base",
    "User",
    "CandidateProfile",
    "CandidateSkill",
    "Education",
    "Experience",
    "Project",
    "Certification",
    "Skill",
    "SkillAlias",
    "SkillRelationship",
    "SkillPrerequisite",
    "Job",
    "JobSkill",
    "SavedJob",
    "JobMatch",
    "Resume",
    "Roadmap",
    "RoadmapItem",
    "CandidateActivity",
]
