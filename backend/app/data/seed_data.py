"""
Idempotent Database Seeding Script.
Populates standardized skills taxonomy, aliases, explicit relationships,
prerequisites, and 40+ curated internal job postings.
Safe to execute repeatedly without generating duplicate records.
"""
import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.db.session import AsyncSessionLocal
from app.models import (
    Skill,
    SkillAlias,
    SkillRelationship,
    SkillPrerequisite,
    Job,
    JobSkill,
)

DATA_DIR = Path(__file__).resolve().parent
SKILLS_JSON_PATH = DATA_DIR / "seed_skills.json"
JOBS_JSON_PATH = DATA_DIR / "seed_jobs.json"


async def seed_skills(session: AsyncSession) -> Dict[str, Skill]:
    """Idempotently seeds skills, aliases, relationships, and prerequisites."""
    with open(SKILLS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info("Seeding skills taxonomy...")
    skill_map: Dict[str, Skill] = {}

    # 1. Skills
    for item in data["skills"]:
        stmt = select(Skill).where(Skill.normalized_name == item["normalized_name"])
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            new_skill = Skill(
                name=item["name"],
                normalized_name=item["normalized_name"],
                category=item["category"],
            )
            session.add(new_skill)
            await session.flush()
            skill_map[item["name"]] = new_skill
        else:
            skill_map[item["name"]] = existing

    # 2. Aliases
    for item in data.get("aliases", []):
        target_skill = skill_map.get(item["skill_name"])
        if not target_skill:
            continue
        stmt = select(SkillAlias).where(SkillAlias.alias == item["alias"].lower())
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            alias_entry = SkillAlias(
                skill_id=target_skill.id,
                alias=item["alias"].lower(),
            )
            session.add(alias_entry)

    # 3. Explicit Transferable & Related Relationships
    for item in data.get("relationships", []):
        source = skill_map.get(item["source_skill"])
        target = skill_map.get(item["target_skill"])
        if not source or not target or source.id == target.id:
            continue

        stmt = select(SkillRelationship).where(
            SkillRelationship.source_skill_id == source.id,
            SkillRelationship.target_skill_id == target.id,
        )
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            rel = SkillRelationship(
                source_skill_id=source.id,
                target_skill_id=target.id,
                relationship_type=item.get("relationship_type", "transferable"),
                similarity_weight=Decimal(str(item["similarity_weight"])),
            )
            session.add(rel)

    # 4. Prerequisites
    for item in data.get("prerequisites", []):
        target = skill_map.get(item["skill"])
        prereq = skill_map.get(item["prerequisite"])
        if not target or not prereq or target.id == prereq.id:
            continue

        stmt = select(SkillPrerequisite).where(
            SkillPrerequisite.skill_id == target.id,
            SkillPrerequisite.prerequisite_skill_id == prereq.id,
        )
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            p_entry = SkillPrerequisite(
                skill_id=target.id,
                prerequisite_skill_id=prereq.id,
                difficulty_tier=item.get("difficulty_tier", 1),
            )
            session.add(p_entry)

    await session.commit()
    logger.info(f"Skills seeding complete. Total verified skills in memory: {len(skill_map)}")
    return skill_map


async def seed_jobs(session: AsyncSession, skill_map: Dict[str, Skill]) -> int:
    """Idempotently seeds curated job postings and their associated job_skills."""
    with open(JOBS_JSON_PATH, "r", encoding="utf-8") as f:
        jobs_data = json.load(f)

    logger.info(f"Seeding {len(jobs_data)} curated internal jobs...")
    seeded_count = 0

    for item in jobs_data:
        # Check by unique title and company
        stmt = select(Job).where(Job.title == item["title"], Job.company == item["company"])
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            job = Job(
                title=item["title"],
                company=item["company"],
                location=item["location"],
                employment_type=item["employment_type"],
                experience_level=item["experience_level"],
                min_experience_years=Decimal(str(item["min_experience_years"])),
                target_education_level=item["target_education_level"],
                description=item["description"],
                salary_range=item.get("salary_range"),
                is_active=True,
            )
            session.add(job)
            await session.flush()
            seeded_count += 1

        # Seed JobSkills
        for s_spec in item.get("skills", []):
            skill_obj = skill_map.get(s_spec["skill_name"])
            if not skill_obj:
                continue

            js_stmt = select(JobSkill).where(
                JobSkill.job_id == job.id,
                JobSkill.skill_id == skill_obj.id,
            )
            js_res = await session.execute(js_stmt)
            if not js_res.scalar_one_or_none():
                job_skill = JobSkill(
                    job_id=job.id,
                    skill_id=skill_obj.id,
                    is_required=s_spec.get("is_required", True),
                    importance_weight=Decimal(str(s_spec.get("importance_weight", 1.0))),
                    min_proficiency=s_spec.get("min_proficiency", "intermediate"),
                )
                session.add(job_skill)

    await session.commit()
    logger.info(f"Jobs seeding complete. Total jobs in dataset: {len(jobs_data)} (Newly inserted: {seeded_count})")
    return len(jobs_data)


async def run_seed() -> None:
    """Master seeding entrypoint with bounded retry."""
    max_retries = 15
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Connecting to database for seeding...")
            async with AsyncSessionLocal() as session:
                skill_map = await seed_skills(session)
                total_jobs = await seed_jobs(session, skill_map)
                logger.info(f"Seeding completed successfully: {len(skill_map)} skills, {total_jobs} jobs verified.")
            break
        except Exception as exc:
            if attempt == max_retries:
                logger.error(f"Seeding connection failed after {max_retries} attempts: {exc}")
                raise
            logger.warning(
                f"Database not ready for seeding (attempt {attempt}/{max_retries}). Retrying in 2s... Error: {exc}"
            )
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run_seed())
