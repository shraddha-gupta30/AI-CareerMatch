"""
Unit Tests for Seed Data Files: Taxonomy, Relationships, Prerequisites, and Jobs.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
SKILLS_FILE = DATA_DIR / "seed_skills.json"
JOBS_FILE = DATA_DIR / "seed_jobs.json"


def test_skills_seed_file_integrity():
    """Verify seed_skills.json structure, consistency, and constraints."""
    assert SKILLS_FILE.exists(), f"{SKILLS_FILE} does not exist"
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "skills" in data
    assert "aliases" in data
    assert "relationships" in data
    assert "prerequisites" in data

    skills = data["skills"]
    assert len(skills) >= 35, f"Expected at least 35 skills, got {len(skills)}"

    skill_names = {s["name"] for s in skills}
    normalized_names = {s["normalized_name"] for s in skills}
    assert len(skill_names) == len(skills), "Duplicate skill names detected in seed data"
    assert len(normalized_names) == len(skills), "Duplicate normalized names detected"

    # Verify Aliases reference existing skills
    for alias in data["aliases"]:
        assert alias["skill_name"] in skill_names, f"Alias {alias['alias']} references unknown skill {alias['skill_name']}"

    # Verify Relationships reference existing skills and have valid weights
    for rel in data["relationships"]:
        assert rel["source_skill"] in skill_names, f"Unknown source skill {rel['source_skill']}"
        assert rel["target_skill"] in skill_names, f"Unknown target skill {rel['target_skill']}"
        assert rel["source_skill"] != rel["target_skill"], "Self-referencing relationship"
        assert 0.0 < rel["similarity_weight"] <= 1.0, f"Invalid similarity weight: {rel['similarity_weight']}"

    # Verify Prerequisites reference existing skills and have valid difficulty tier
    for prereq in data["prerequisites"]:
        assert prereq["skill"] in skill_names, f"Unknown skill {prereq['skill']}"
        assert prereq["prerequisite"] in skill_names, f"Unknown prerequisite {prereq['prerequisite']}"
        assert prereq["skill"] != prereq["prerequisite"], "Self-prerequisite detected"
        assert 1 <= prereq["difficulty_tier"] <= 5, f"Invalid tier: {prereq['difficulty_tier']}"


def test_jobs_seed_file_integrity():
    """Verify seed_jobs.json has at least 40 jobs with valid schema and skill references."""
    assert JOBS_FILE.exists(), f"{JOBS_FILE} does not exist"
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    assert len(jobs) >= 40, f"Expected at least 40 jobs, got {len(jobs)}"

    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        skills_data = json.load(f)
    valid_skill_names = {s["name"] for s in skills_data["skills"]}

    seen_jobs = set()
    for job in jobs:
        # Check uniqueness of (title, company)
        job_key = (job["title"], job["company"])
        assert job_key not in seen_jobs, f"Duplicate job: {job_key}"
        seen_jobs.add(job_key)

        assert job["title"], "Job must have a non-empty title"
        assert job["company"], "Job must have a non-empty company"
        assert job["location"], "Job must have a location"
        assert job["experience_level"] in {"entry", "mid", "senior", "lead", "internship"}
        assert job["min_experience_years"] >= 0.0
        assert len(job["skills"]) >= 2, f"Job {job['title']} has too few skills"

        # Check job skills
        job_skill_names = set()
        for s in job["skills"]:
            assert s["skill_name"] in valid_skill_names, f"Job {job['title']} demands unseeded skill: {s['skill_name']}"
            assert s["skill_name"] not in job_skill_names, f"Duplicate skill {s['skill_name']} in job {job['title']}"
            job_skill_names.add(s["skill_name"])

            assert 0.5 <= s["importance_weight"] <= 2.0, f"Importance weight out of bounds in {job['title']}: {s['importance_weight']}"
            assert s["min_proficiency"] in {"beginner", "intermediate", "advanced", "expert"}
