"""
Unit Tests for Alembic Migration Script Integrity.
"""
from pathlib import Path

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def test_initial_migration_exists():
    """Verify initial migration file exists and defines upgrade and downgrade."""
    migration_files = list(VERSIONS_DIR.glob("*.py"))
    assert len(migration_files) >= 1, "No Alembic migration files found in alembic/versions"

    initial_mig = migration_files[0]
    content = initial_mig.read_text(encoding="utf-8")
    assert "def upgrade()" in content
    assert "def downgrade()" in content
    assert "create_table('users'" in content or 'create_table(\n        "users"' in content
    assert "create_table('skills'" in content or 'create_table(\n        "skills"' in content
    assert "create_table('skill_relationships'" in content or 'create_table(\n        "skill_relationships"' in content
    assert "create_table('jobs'" in content or 'create_table(\n        "jobs"' in content
