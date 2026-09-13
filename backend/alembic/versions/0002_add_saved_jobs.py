"""Add saved_jobs table for candidate bookmark persistence.

Revision ID: 0002_add_saved_jobs
Revises: 0001_initial_schema
Create Date: 2026-09-13 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_add_saved_jobs"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"], unique=False)
    op.create_index("ix_saved_jobs_job_id", "saved_jobs", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_saved_jobs_job_id", table_name="saved_jobs")
    op.drop_index("ix_saved_jobs_user_id", table_name="saved_jobs")
    op.drop_table("saved_jobs")
