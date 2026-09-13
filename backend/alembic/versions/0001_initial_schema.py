"""Initial database schema for AI CareerMatch domain entities.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-12 23:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. candidate_profiles
    op.create_table(
        "candidate_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("target_role", sa.String(length=150), nullable=False),
        sa.Column("target_location", sa.String(length=150), nullable=True),
        sa.Column("target_employment_type", sa.String(length=50), nullable=True),
        sa.Column("total_experience_years", sa.Numeric(precision=4, scale=1), server_default=sa.text("0.0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("total_experience_years >= 0.0", name="ck_candidate_profiles_exp_positive"),
    )
    op.create_index("ix_candidate_profiles_user_id", "candidate_profiles", ["user_id"], unique=True)
    op.create_index("ix_candidate_profiles_target_role", "candidate_profiles", ["target_role"], unique=False)

    # 3. skills
    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )
    op.create_index("ix_skills_normalized_name", "skills", ["normalized_name"], unique=True)
    op.create_index("ix_skills_category", "skills", ["category"], unique=False)

    # 4. skill_aliases
    op.create_table(
        "skill_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(length=100), nullable=False),
    )
    op.create_index("ix_skill_aliases_alias", "skill_aliases", ["alias"], unique=True)

    # 5. skill_relationships
    op.create_table(
        "skill_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), server_default="transferable", nullable=False),
        sa.Column("similarity_weight", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_skill_id", "target_skill_id", name="uq_skill_relationships_source_target"),
        sa.CheckConstraint("source_skill_id != target_skill_id", name="ck_skill_relationships_no_self"),
        sa.CheckConstraint("similarity_weight > 0.0 AND similarity_weight <= 1.0", name="ck_skill_relationships_weight_range"),
    )

    # 6. skill_prerequisites
    op.create_table(
        "skill_prerequisites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prerequisite_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("difficulty_tier", sa.Integer(), server_default="1", nullable=False),
        sa.UniqueConstraint("skill_id", "prerequisite_skill_id", name="uq_skill_prerequisites_skill_prereq"),
        sa.CheckConstraint("skill_id != prerequisite_skill_id", name="ck_skill_prerequisites_no_self"),
        sa.CheckConstraint("difficulty_tier >= 1 AND difficulty_tier <= 5", name="ck_skill_prerequisites_tier_range"),
    )

    # 7. candidate_skills
    op.create_table(
        "candidate_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("proficiency_level", sa.String(length=30), server_default="intermediate", nullable=False),
        sa.Column("years_experience", sa.Numeric(precision=3, scale=1), server_default="1.0", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("proficiency_source", sa.String(length=30), server_default="user_verified", nullable=False),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_candidate_skills_profile_skill"),
        sa.CheckConstraint("years_experience >= 0.0", name="ck_candidate_skills_exp_positive"),
        sa.CheckConstraint("proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')", name="ck_candidate_skills_level"),
        sa.CheckConstraint("proficiency_source IN ('user_verified', 'resume_inferred', 'unknown')", name="ck_candidate_skills_source"),
    )

    # 8. education
    op.create_table(
        "education",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution", sa.String(length=255), nullable=False),
        sa.Column("degree", sa.String(length=150), nullable=False),
        sa.Column("field_of_study", sa.String(length=150), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("grade_gpa", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 9. experience
    op.create_table(
        "experience",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 10. projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("repository_url", sa.String(length=500), nullable=True),
        sa.Column("live_url", sa.String(length=500), nullable=True),
        sa.Column("technologies", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 11. certifications
    op.create_table(
        "certifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("issuing_organization", sa.String(length=255), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("credential_id", sa.String(length=150), nullable=True),
        sa.Column("credential_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 12. resumes
    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("raw_extracted_text", sa.Text(), nullable=True),
        sa.Column("parsed_staging_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="uploaded", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('uploaded', 'processing', 'pending_review', 'applied', 'failed')",
            name="ck_resumes_status",
        ),
    )

    # 13. jobs
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=False),
        sa.Column("employment_type", sa.String(length=50), server_default="full-time", nullable=False),
        sa.Column("experience_level", sa.String(length=50), server_default="entry", nullable=False),
        sa.Column("min_experience_years", sa.Numeric(precision=3, scale=1), server_default="0.0", nullable=False),
        sa.Column("target_education_level", sa.String(length=100), server_default="Bachelor", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("min_experience_years >= 0.0", name="ck_jobs_exp_positive"),
    )
    op.create_index("ix_jobs_title", "jobs", ["title"], unique=False)
    op.create_index("ix_jobs_is_active", "jobs", ["is_active"], unique=False)

    # 14. job_skills
    op.create_table(
        "job_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("importance_weight", sa.Numeric(precision=3, scale=2), server_default="1.00", nullable=False),
        sa.Column("min_proficiency", sa.String(length=30), server_default="intermediate", nullable=False),
        sa.UniqueConstraint("job_id", "skill_id", name="uq_job_skills_job_skill"),
        sa.CheckConstraint("importance_weight >= 0.5 AND importance_weight <= 2.0", name="ck_job_skills_weight_range"),
        sa.CheckConstraint("min_proficiency IN ('beginner', 'intermediate', 'advanced', 'expert')", name="ck_job_skills_min_proficiency"),
    )

    # 15. job_matches
    op.create_table(
        "job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("skill_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("experience_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("education_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("breakdown_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("profile_id", "job_id", name="uq_job_matches_profile_job"),
        sa.CheckConstraint("overall_score >= 0.0 AND overall_score <= 100.0", name="ck_job_matches_overall_range"),
        sa.CheckConstraint("skill_score >= 0.0 AND skill_score <= 100.0", name="ck_job_matches_skill_range"),
        sa.CheckConstraint("experience_score >= 0.0 AND experience_score <= 100.0", name="ck_job_matches_exp_range"),
        sa.CheckConstraint("education_score >= 0.0 AND education_score <= 100.0", name="ck_job_matches_edu_range"),
    )
    op.create_index("ix_job_matches_profile_id", "job_matches", ["profile_id"], unique=False)
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"], unique=False)

    # 16. roadmaps
    op.create_table(
        "roadmaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_role", sa.String(length=150), nullable=False),
        sa.Column("target_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("total_items", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed_items", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("total_items >= 0", name="ck_roadmaps_total_items_positive"),
        sa.CheckConstraint("completed_items >= 0", name="ck_roadmaps_completed_items_positive"),
    )

    # 17. roadmap_items
    op.create_table(
        "roadmap_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("roadmap_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("stage_phase", sa.Integer(), server_default="1", nullable=False),
        sa.Column("priority", sa.String(length=30), server_default="high", nullable=False),
        sa.Column("estimated_hours", sa.Integer(), server_default="10", nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("suggested_project", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="not_started", nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("estimated_hours > 0", name="ck_roadmap_items_hours_positive"),
        sa.CheckConstraint("status IN ('not_started', 'in_progress', 'completed')", name="ck_roadmap_items_status"),
        sa.CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name="ck_roadmap_items_priority"),
    )

    # 18. candidate_activity
    op.create_table(
        "candidate_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_candidate_activity_user_id", "candidate_activity", ["user_id"], unique=False)
    op.create_index("ix_candidate_activity_created_at", "candidate_activity", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("candidate_activity")
    op.drop_table("roadmap_items")
    op.drop_table("roadmaps")
    op.drop_table("job_matches")
    op.drop_table("job_skills")
    op.drop_table("jobs")
    op.drop_table("resumes")
    op.drop_table("certifications")
    op.drop_table("projects")
    op.drop_table("experience")
    op.drop_table("education")
    op.drop_table("candidate_skills")
    op.drop_table("skill_prerequisites")
    op.drop_table("skill_relationships")
    op.drop_table("skill_aliases")
    op.drop_table("skills")
    op.drop_table("candidate_profiles")
    op.drop_table("users")
