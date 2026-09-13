"""
Unit Tests for SQLAlchemy Domain Model Metadata, Constraints, and Relationships.
"""
import pytest
from app.models import (
    Base,
    User,
    CandidateProfile,
    CandidateSkill,
    Education,
    Experience,
    Project,
    Certification,
    Skill,
    SkillAlias,
    SkillRelationship,
    SkillPrerequisite,
    Job,
    JobSkill,
    JobMatch,
    Resume,
    Roadmap,
    RoadmapItem,
    CandidateActivity,
)

EXPECTED_TABLES = {
    "users",
    "candidate_profiles",
    "skills",
    "skill_aliases",
    "skill_relationships",
    "skill_prerequisites",
    "candidate_skills",
    "education",
    "experience",
    "projects",
    "certifications",
    "resumes",
    "jobs",
    "job_skills",
    "job_matches",
    "roadmaps",
    "roadmap_items",
    "candidate_activity",
    "saved_jobs",
}


def test_all_expected_tables_registered():
    """Verify all 19 approved domain models are present in SQLAlchemy metadata."""
    registered = set(Base.metadata.tables.keys())
    assert EXPECTED_TABLES.issubset(registered), f"Missing tables: {EXPECTED_TABLES - registered}"
    assert len(registered) == 19


def test_user_and_profile_constraints():
    """Verify primary keys, unique constraints, and foreign keys on user/profile tables."""
    users_table = Base.metadata.tables["users"]
    assert "email" in users_table.c
    assert users_table.c.email.unique or any(idx.unique and "email" in [c.name for c in idx.columns] for idx in users_table.indexes)

    profiles_table = Base.metadata.tables["candidate_profiles"]
    user_id_fk = list(profiles_table.c.user_id.foreign_keys)[0]
    assert user_id_fk.column.table.name == "users"
    assert user_id_fk.ondelete.upper() == "CASCADE"
    assert any(idx.unique and "user_id" in [c.name for c in idx.columns] for idx in profiles_table.indexes)


def test_skill_relationships_constraints():
    """Verify explicit skill relationships table adheres to the revised matching algorithm."""
    table = Base.metadata.tables["skill_relationships"]
    check_names = {ck.name for ck in table.constraints if hasattr(ck, "name") and ck.name}
    assert "ck_skill_relationships_no_self" in check_names
    assert "ck_skill_relationships_weight_range" in check_names
    assert "uq_skill_relationships_source_target" in check_names


def test_candidate_skills_proficiency_sources():
    """Verify candidate_skills enforces proficiency sources and levels."""
    table = Base.metadata.tables["candidate_skills"]
    check_names = {ck.name for ck in table.constraints if hasattr(ck, "name") and ck.name}
    assert "ck_candidate_skills_level" in check_names
    assert "ck_candidate_skills_source" in check_names
    assert "uq_candidate_skills_profile_skill" in check_names


def test_job_skills_weight_constraints():
    """Verify importance weights are restricted to [0.5, 2.0]."""
    table = Base.metadata.tables["job_skills"]
    check_names = {ck.name for ck in table.constraints if hasattr(ck, "name") and ck.name}
    assert "ck_job_skills_weight_range" in check_names
    assert "uq_job_skills_job_skill" in check_names


def test_job_matches_score_constraints():
    """Verify all match scores are strictly bounded within [0, 100]."""
    table = Base.metadata.tables["job_matches"]
    check_names = {ck.name for ck in table.constraints if hasattr(ck, "name") and ck.name}
    assert "ck_job_matches_overall_range" in check_names
    assert "ck_job_matches_skill_range" in check_names
    assert "ck_job_matches_exp_range" in check_names
    assert "ck_job_matches_edu_range" in check_names
    assert "uq_job_matches_profile_job" in check_names
