"""
Personalized Career Roadmap and Progress Tracking Service.
Generates 100% deterministic, DAG-ordered learning milestones and practical projects
based on skill gap analysis, explicit taxonomy prerequisites, experience gaps, and education levels.

Guarantees:
1. Strict prerequisite ordering (prerequisites strictly appear before dependent skills).
2. Four structured stages (Stage 1: Core Prerequisites & Must-Haves, Stage 2: Secondary & Transferable,
   Stage 3: Preferred Skills, Stage 4: Capstone Experience & Education Milestones).
3. Dynamic progress tracking without schema alterations.
4. Optional Gemini enhancement with guaranteed deterministic fallback.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.core.logging import logger
from app.models.job import Job, JobSkill
from app.models.profile import CandidateProfile, CandidateSkill, Education, Experience
from app.models.roadmap import Roadmap, RoadmapItem
from app.models.skill import Skill, SkillAlias, SkillPrerequisite, SkillRelationship
from app.schemas.gap import SkillGapResponse
from app.schemas.roadmap import (
    RoadmapDetailResponse,
    RoadmapItemResponse,
    RoadmapProgressResponse,
    RoadmapResponse,
)
from app.services.gap_service import derive_skill_gaps


def _estimate_hours(proficiency: str) -> int:
    """Estimates deterministic learning hours based on required target proficiency."""
    p = (proficiency or "intermediate").lower().strip()
    if p == "expert":
        return 45
    elif p == "advanced":
        return 35
    elif p == "intermediate":
        return 25
    elif p == "beginner":
        return 15
    return 20


def _get_skill_templates(skill_name: str, category: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Returns deterministic (title, recommended_action, suggested_project)
    tailored to the skill's technical domain.
    """
    name_lower = skill_name.lower().strip()

    # Front-End
    if any(k in name_lower for k in ["react", "vue", "angular", "next.js", "frontend", "html", "css", "tailwind", "javascript", "typescript"]):
        return (
            f"Master {skill_name} for Front-End Architecture",
            f"Study modern component patterns, reactive state management, and accessibility standards with {skill_name}.",
            f"Build a production-ready web application demonstrating responsive layouts, state management, and real-time UI with {skill_name}.",
        )
    # Back-End
    if any(k in name_lower for k in ["python", "fastapi", "django", "flask", "node.js", "express", "go", "java", "spring", "backend", "c++", "c#", ".net"]):
        return (
            f"Master {skill_name} Service Architecture",
            f"Learn RESTful/gRPC API design, asynchronous execution, database transactions, and service reliability in {skill_name}.",
            f"Develop and deploy a high-throughput microservice in {skill_name} with automated tests, OpenAPI docs, and authentication.",
        )
    # Databases
    if any(k in name_lower for k in ["sql", "postgresql", "mysql", "mongodb", "redis", "database", "nosql"]):
        return (
            f"Advance Database Modeling & Queries in {skill_name}",
            f"Practice relational schema normalization, indexing strategies, complex query tuning, and transactional safety in {skill_name}.",
            f"Design an analytics database schema in {skill_name} with optimized indexes, views, and benchmarked query execution plans.",
        )
    # DevOps & Infrastructure
    if any(k in name_lower for k in ["docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "git", "linux", "devops", "terraform"]):
        return (
            f"Containerization & Cloud Infrastructure with {skill_name}",
            f"Implement declarative infrastructure, container orchestration, and continuous integration pipelines using {skill_name}.",
            f"Configure automated CI/CD deployment pipelines with container security scanning and staging environments using {skill_name}.",
        )
    # AI & Data
    if any(k in name_lower for k in ["machine learning", "deep learning", "pytorch", "tensorflow", "pandas", "numpy", "scikit-learn", "data science"]):
        return (
            f"Applied Data Science & Machine Learning with {skill_name}",
            f"Master feature engineering, cross-validation, hyperparameter tuning, and model evaluation metrics with {skill_name}.",
            f"Build an end-to-end predictive pipeline using {skill_name} featuring data preprocessing, model evaluation, and an inference API.",
        )
    # General fallback
    return (
        f"Master Core Competencies in {skill_name}",
        f"Complete structured tutorials and practice exercises mastering foundational and advanced capabilities of {skill_name}.",
        f"Develop a focused portfolio project showcasing real-world application of {skill_name}.",
    )


async def _personalize_roadmap_with_gemini(
    items: List[Dict[str, Any]],
    target_role: str,
    job_description: str,
    candidate_summary: str,
) -> List[Dict[str, Any]]:
    """
    Optionally personalizes descriptions and suggested projects using Gemini.
    Deterministic scores, ordering, priorities, and stages remain untouched.
    Silently falls back to deterministic items on any exception.
    """
    if not settings.GEMINI_API_KEY:
        return items

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt_items = [
            {
                "title": it["title"],
                "stage_phase": it["stage_phase"],
                "priority": it["priority"],
                "recommended_action": it["recommended_action"],
                "suggested_project": it.get("suggested_project"),
            }
            for it in items
        ]

        prompt = (
            f"You are an expert career mentor. Personalize the learning actions and projects for a candidate targeting '{target_role}'.\n"
            f"Job Description Excerpt: {job_description[:600]}\n"
            f"Candidate Background: {candidate_summary[:400]}\n\n"
            f"Return ONLY valid JSON: an array of objects matching the input array length, with updated 'description', 'recommended_action', and 'suggested_project'.\n"
            f"Input items:\n{json.dumps(prompt_items)}"
        )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        cleaned_text = (response.text or "").strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        enhanced = json.loads(cleaned_text)
        if isinstance(enhanced, list) and len(enhanced) == len(items):
            for i, enh in enumerate(enhanced):
                if isinstance(enh, dict):
                    if enh.get("description"):
                        items[i]["description"] = str(enh["description"])
                    if enh.get("recommended_action"):
                        items[i]["recommended_action"] = str(enh["recommended_action"])
                    if enh.get("suggested_project"):
                        items[i]["suggested_project"] = str(enh["suggested_project"])
    except Exception as exc:
        logger.warning(f"Gemini roadmap personalization skipped: {exc}")

    return items


def compute_roadmap_progress(
    items: List[Any],
) -> RoadmapProgressResponse:
    """Computes dynamic progress percentages and status tallies for roadmap items."""
    total_items = len(items)
    completed = sum(1 for it in items if getattr(it, "status", None) == "completed")
    in_progress = sum(1 for it in items if getattr(it, "status", None) == "in_progress")
    not_started = sum(1 for it in items if getattr(it, "status", None) == "not_started")
    pct = round((completed / total_items) * 100.0, 1) if total_items > 0 else 0.0

    return RoadmapProgressResponse(
        total_items=total_items,
        completed_items=completed,
        in_progress_items=in_progress,
        not_started_items=not_started,
        progress_percentage=pct,
    )


async def generate_career_roadmap(
    profile: CandidateProfile,
    job: Job,
    db: AsyncSession,
) -> Roadmap:
    """
    Deterministic Roadmap Generator.
    Derives gaps, pulls prerequisites, builds topological DAG ordering,
    structures into 4 progressive stages, and persists/updates the Roadmap.
    """
    # 1. Load taxonomy maps
    target_skill_alias = aliased(Skill)
    stmt_rel = (
        select(
            Skill.name.label("source_name"),
            target_skill_alias.name.label("target_name"),
            SkillRelationship.similarity_weight,
        )
        .join(Skill, SkillRelationship.source_skill_id == Skill.id)
        .join(target_skill_alias, SkillRelationship.target_skill_id == target_skill_alias.id)
    )
    res_rel = await db.execute(stmt_rel)
    rel_map: Dict[str, Dict[str, float]] = {}
    for src, tgt, weight in res_rel.all():
        if src not in rel_map:
            rel_map[src] = {}
        rel_map[src][tgt] = float(weight)

    alias_stmt = (
        select(SkillAlias.alias, Skill.name)
        .join(Skill, SkillAlias.skill_id == Skill.id)
    )
    alias_res = await db.execute(alias_stmt)
    alias_map: Dict[str, str] = {}
    for a, c_name in alias_res.all():
        clean_alias = a.strip().lower().replace(" ", "").replace(".", "")
        alias_map[clean_alias] = c_name

    # 2. Derive skill gaps
    gap_analysis: SkillGapResponse = derive_skill_gaps(profile, job, rel_map, alias_map)

    # 3. Load full skill catalog & prerequisites
    all_skills_res = await db.execute(select(Skill))
    all_skills = all_skills_res.scalars().all()
    skill_by_norm: Dict[str, Skill] = {s.normalized_name: s for s in all_skills}
    skill_by_name: Dict[str, Skill] = {s.name.lower(): s for s in all_skills}

    prereq_stmt = (
        select(
            Skill.name.label("skill_name"),
            Skill.id.label("skill_id"),
            SkillPrerequisite.prerequisite_skill_id,
            target_skill_alias.name.label("prereq_name"),
            SkillPrerequisite.difficulty_tier,
        )
        .select_from(SkillPrerequisite)
        .join(Skill, SkillPrerequisite.skill_id == Skill.id)
        .join(target_skill_alias, SkillPrerequisite.prerequisite_skill_id == target_skill_alias.id)
    )
    prereq_res = await db.execute(prereq_stmt)
    prereqs_by_skill: Dict[str, List[Tuple[str, UUID, int]]] = {}
    for sk_name, sk_id, prereq_id, prereq_name, tier in prereq_res.all():
        key = sk_name.lower()
        if key not in prereqs_by_skill:
            prereqs_by_skill[key] = []
        prereqs_by_skill[key].append((prereq_name, prereq_id, int(tier)))

    # 4. Gather candidate's known skills
    candidate_known_skills: Set[str] = set()
    for cs in getattr(profile, "skills", []) or []:
        s_name = (
            getattr(getattr(cs, "skill", None), "name", None)
            or getattr(cs, "name", None)
            or getattr(cs, "skill_name", "")
        )
        if s_name:
            norm = s_name.strip().lower()
            candidate_known_skills.add(norm)
            canon = alias_map.get(norm.replace(" ", "").replace(".", ""))
            if canon:
                candidate_known_skills.add(canon.lower())

    # 5. Build raw roadmap items map keyed by normalized skill name
    items_map: Dict[str, Dict[str, Any]] = {}

    def get_skill_obj(name: str) -> Optional[Skill]:
        clean = name.strip().lower()
        if clean in skill_by_name:
            return skill_by_name[clean]
        norm = clean.replace(" ", "").replace(".", "")
        if norm in skill_by_norm:
            return skill_by_norm[norm]
        canon = alias_map.get(norm)
        if canon and canon.lower() in skill_by_name:
            return skill_by_name[canon.lower()]
        return None

    # Helper to add foundational prerequisite if missing
    def ensure_prerequisites(skill_name: str) -> None:
        p_list = prereqs_by_skill.get(skill_name.lower(), [])
        for p_name, p_id, tier in p_list:
            p_clean = p_name.lower()
            if p_clean not in candidate_known_skills and p_clean not in items_map:
                # Add as Stage 1 foundational prerequisite
                p_obj = get_skill_obj(p_name)
                title, action, project = _get_skill_templates(p_name, getattr(p_obj, "category", None))
                items_map[p_clean] = {
                    "skill_id": p_id if p_id else (p_obj.id if p_obj else None),
                    "skill_name": p_name,
                    "title": f"Foundational Prerequisite: {title}",
                    "description": f"{p_name} is a required foundational prerequisite before advancing to {skill_name}.",
                    "stage_phase": 1,
                    "priority": "critical",
                    "estimated_hours": max(15, tier * 10),
                    "recommended_action": action,
                    "suggested_project": project,
                    "importance": 2.0,
                    "prerequisites": [p[0] for p in prereqs_by_skill.get(p_clean, [])],
                }
                # Recursively ensure prerequisites of prerequisite
                ensure_prerequisites(p_name)

    # 5a. Missing Required Skills
    for mr in gap_analysis.missing_required_skills:
        ensure_prerequisites(mr.name)
        s_clean = mr.name.lower()
        if s_clean not in items_map:
            s_obj = get_skill_obj(mr.name)
            title, action, project = _get_skill_templates(mr.name, getattr(s_obj, "category", None))
            stage = 1 if mr.importance_weight >= 1.0 else 2
            priority = "critical" if mr.importance_weight >= 1.0 else "high"
            hours = _estimate_hours(mr.required_proficiency)
            items_map[s_clean] = {
                "skill_id": s_obj.id if s_obj else None,
                "skill_name": mr.name,
                "title": title,
                "description": f"Target required proficiency of '{mr.required_proficiency}' in {mr.name} to fulfill core role requirements.",
                "stage_phase": stage,
                "priority": priority,
                "estimated_hours": hours,
                "recommended_action": action,
                "suggested_project": project,
                "importance": float(mr.importance_weight),
                "prerequisites": [p[0] for p in prereqs_by_skill.get(s_clean, [])],
            }

    # 5b. Partial Required Skills (transferable matches)
    for pr in gap_analysis.partial_required_skills:
        ensure_prerequisites(pr.job_skill_name)
        s_clean = pr.job_skill_name.lower()
        if s_clean not in items_map:
            s_obj = get_skill_obj(pr.job_skill_name)
            title, action, project = _get_skill_templates(pr.job_skill_name, getattr(s_obj, "category", None))
            # 50% hours because candidate has transferable background
            hours = max(10, int(_estimate_hours(pr.required_proficiency) * 0.5))
            items_map[s_clean] = {
                "skill_id": s_obj.id if s_obj else None,
                "skill_name": pr.job_skill_name,
                "title": f"Bridge {title}",
                "description": (
                    f"Bridge knowledge from your existing skill '{pr.candidate_skill_name}' "
                    f"to full '{pr.required_proficiency}' proficiency in '{pr.job_skill_name}'."
                ),
                "stage_phase": 2,
                "priority": "high",
                "estimated_hours": hours,
                "recommended_action": f"Focus on delta concepts and syntax differences between {pr.candidate_skill_name} and {pr.job_skill_name}.",
                "suggested_project": project,
                "importance": 1.2,
                "prerequisites": [p[0] for p in prereqs_by_skill.get(s_clean, [])],
            }

    # 5c. Missing Preferred Skills
    for mp in gap_analysis.missing_preferred_skills:
        ensure_prerequisites(mp.name)
        s_clean = mp.name.lower()
        if s_clean not in items_map:
            s_obj = get_skill_obj(mp.name)
            title, action, project = _get_skill_templates(mp.name, getattr(s_obj, "category", None))
            hours = _estimate_hours(mp.required_proficiency)
            items_map[s_clean] = {
                "skill_id": s_obj.id if s_obj else None,
                "skill_name": mp.name,
                "title": f"Preferred Skill: {title}",
                "description": f"Gain preferred competency in {mp.name} to stand out from other candidates.",
                "stage_phase": 3,
                "priority": "medium",
                "estimated_hours": hours,
                "recommended_action": action,
                "suggested_project": project,
                "importance": float(mp.importance_weight),
                "prerequisites": [p[0] for p in prereqs_by_skill.get(s_clean, [])],
            }

    # 5d. Partial Preferred Skills
    for pp in gap_analysis.partial_preferred_skills:
        ensure_prerequisites(pp.job_skill_name)
        s_clean = pp.job_skill_name.lower()
        if s_clean not in items_map:
            s_obj = get_skill_obj(pp.job_skill_name)
            title, action, project = _get_skill_templates(pp.job_skill_name, getattr(s_obj, "category", None))
            hours = max(10, int(_estimate_hours(pp.required_proficiency) * 0.5))
            items_map[s_clean] = {
                "skill_id": s_obj.id if s_obj else None,
                "skill_name": pp.job_skill_name,
                "title": f"Preferred Skill: Bridge {title}",
                "description": f"Transfer your background in {pp.candidate_skill_name} to master preferred skill {pp.job_skill_name}.",
                "stage_phase": 3,
                "priority": "low",
                "estimated_hours": hours,
                "recommended_action": action,
                "suggested_project": project,
                "importance": 0.8,
                "prerequisites": [p[0] for p in prereqs_by_skill.get(s_clean, [])],
            }

    # 6. Stage 4 Milestones (Experience & Education)
    milestone_items: List[Dict[str, Any]] = []

    # Experience gap milestone
    if gap_analysis.experience_gap.experience_gap > 0:
        req_exp = gap_analysis.experience_gap.job_min_experience_years
        cand_exp = gap_analysis.experience_gap.candidate_experience_years
        exp_gap = gap_analysis.experience_gap.experience_gap
        priority = "high" if exp_gap >= 2.0 else "medium"
        milestone_items.append({
            "skill_id": None,
            "skill_name": None,
            "title": f"Production Experience Milestone ({exp_gap:.1f} yr gap)",
            "description": (
                f"Close the experience gap ({req_exp:.1f} yrs required vs {cand_exp:.1f} yrs current). "
                f"Develop end-to-end production applications, contribute to open source, or lead technical deliverables."
            ),
            "stage_phase": 4,
            "priority": priority,
            "estimated_hours": min(60, max(30, int(exp_gap * 20))),
            "recommended_action": "Engage in end-to-end production-grade implementations and document architecture decisions.",
            "suggested_project": f"Deliver a comprehensive capstone application showcasing production-grade workflows for {job.title}.",
            "importance": 1.5,
            "prerequisites": [],
        })

    # Education compatibility milestone
    if not gap_analysis.education_compatibility.meets_requirement:
        req_edu = gap_analysis.education_compatibility.required_level
        cand_edu = gap_analysis.education_compatibility.candidate_highest_level
        milestone_items.append({
            "skill_id": None,
            "skill_name": None,
            "title": f"Education & Credential Milestone ({req_edu} preferred)",
            "description": (
                f"The target role prefers {req_edu} (your current level: {cand_edu}). "
                f"Pursue recognized industry certifications or accredited coursework to bridge credential expectations."
            ),
            "stage_phase": 4,
            "priority": "medium",
            "estimated_hours": 30,
            "recommended_action": "Enroll in accredited online technical specialization programs or professional cloud/engineering certifications.",
            "suggested_project": f"Obtain an official domain certification aligning with {job.title}.",
            "importance": 1.0,
            "prerequisites": [],
        })

    # Fallback if candidate already has 100% match across everything
    if not items_map and not milestone_items:
        milestone_items.append({
            "skill_id": None,
            "skill_name": None,
            "title": f"Mastery & Interview Preparation for {job.title}",
            "description": f"You already match the core requirements for {job.title}! Focus on interview preparation and portfolio presentation.",
            "stage_phase": 1,
            "priority": "high",
            "estimated_hours": 15,
            "recommended_action": "Conduct mock technical interviews, system design reviews, and behavioral question preparation.",
            "suggested_project": f"Create an executive portfolio showcase highlighting achievements relevant to {job.company}.",
            "importance": 1.0,
            "prerequisites": [],
        })

    # 7. Deterministic DAG Topological Sort
    priority_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    # Identify dependencies among roadmap items
    skill_keys = list(items_map.keys())
    # in_degree[key] = number of prereqs for key that are currently in items_map
    in_degree: Dict[str, int] = {k: 0 for k in skill_keys}
    dependents: Dict[str, List[str]] = {k: [] for k in skill_keys}

    for k in skill_keys:
        prereq_tuples = prereqs_by_skill.get(k, [])
        for p_name, _, _ in prereq_tuples:
            p_clean = p_name.lower()
            if p_clean in items_map:
                in_degree[k] += 1
                dependents[p_clean].append(k)

    # Kahn's algorithm with deterministic tie-breaking:
    # Key sorting: (stage_phase asc, priority_weight desc, importance desc, title asc)
    available = [k for k in skill_keys if in_degree[k] == 0]
    available.sort(
        key=lambda k: (
            items_map[k]["stage_phase"],
            -priority_weights.get(items_map[k]["priority"], 1),
            -items_map[k]["importance"],
            items_map[k]["title"],
        )
    )

    ordered_skill_items: List[Dict[str, Any]] = []
    visited: Set[str] = set()

    while available:
        curr_key = available.pop(0)
        visited.add(curr_key)
        ordered_skill_items.append(items_map[curr_key])

        for dep in dependents.get(curr_key, []):
            in_degree[dep] -= 1
            if in_degree[dep] == 0 and dep not in visited and dep not in available:
                available.append(dep)

        # Re-sort available pool
        available.sort(
            key=lambda k: (
                items_map[k]["stage_phase"],
                -priority_weights.get(items_map[k]["priority"], 1),
                -items_map[k]["importance"],
                items_map[k]["title"],
            )
        )

    # Any items caught in cycle (if any)
    for k in skill_keys:
        if k not in visited:
            ordered_skill_items.append(items_map[k])

    # Combine skill items and stage 4 milestones
    all_ordered_items = ordered_skill_items + milestone_items

    # 8. Optional Gemini Personalization
    try:
        candidate_summary = f"{profile.target_role} with {float(profile.total_experience_years)} years experience."
        all_ordered_items = await _personalize_roadmap_with_gemini(
            items=all_ordered_items,
            target_role=job.title,
            job_description=job.description,
            candidate_summary=candidate_summary,
        )
    except Exception as exc:
        logger.warning(f"Gemini personalization skipped: {exc}")

    # Assign final sequence numbers
    for idx, it in enumerate(all_ordered_items, start=1):
        it["sequence_order"] = idx

    # 9. Persist / Update Roadmap & Items
    existing_stmt = (
        select(Roadmap)
        .where(
            Roadmap.profile_id == profile.id,
            Roadmap.target_job_id == job.id,
        )
        .options(selectinload(Roadmap.items))
    )
    existing_res = await db.execute(existing_stmt)
    existing_roadmap = existing_res.scalar_one_or_none()

    if existing_roadmap:
        # Clear previous items
        await db.execute(
            delete(RoadmapItem).where(RoadmapItem.roadmap_id == existing_roadmap.id)
        )
        existing_roadmap.target_role = job.title
        existing_roadmap.total_items = len(all_ordered_items)
        existing_roadmap.completed_items = 0
        existing_roadmap.updated_at = datetime.now(timezone.utc)
        roadmap = existing_roadmap
    else:
        roadmap = Roadmap(
            profile_id=profile.id,
            target_role=job.title,
            target_job_id=job.id,
            total_items=len(all_ordered_items),
            completed_items=0,
        )
        db.add(roadmap)
        await db.flush()

    # Insert items
    for it in all_ordered_items:
        db_item = RoadmapItem(
            roadmap_id=roadmap.id,
            skill_id=it.get("skill_id"),
            title=it["title"][:255],
            description=it["description"],
            stage_phase=it["stage_phase"],
            priority=it["priority"],
            estimated_hours=it["estimated_hours"],
            recommended_action=it["recommended_action"],
            suggested_project=it.get("suggested_project"),
            status="not_started",
            sequence_order=it["sequence_order"],
            completed_at=None,
        )
        db.add(db_item)

    await db.commit()

    # Reload roadmap with complete relationships
    reload_stmt = (
        select(Roadmap)
        .where(Roadmap.id == roadmap.id)
        .options(
            selectinload(Roadmap.target_job),
            selectinload(Roadmap.items).selectinload(RoadmapItem.skill),
        )
    )
    reload_res = await db.execute(reload_stmt)
    refreshed_roadmap = reload_res.scalar_one()
    return refreshed_roadmap


async def get_user_roadmaps(
    user_id: UUID,
    db: AsyncSession,
) -> List[RoadmapResponse]:
    """Retrieves all career roadmaps for the authenticated candidate."""
    # Find candidate profile
    prof_stmt = select(CandidateProfile.id).where(CandidateProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile_id = prof_res.scalar_one_or_none()
    if not profile_id:
        return []

    stmt = (
        select(Roadmap)
        .where(Roadmap.profile_id == profile_id)
        .options(
            selectinload(Roadmap.target_job),
            selectinload(Roadmap.items),
        )
        .order_by(Roadmap.updated_at.desc())
    )
    res = await db.execute(stmt)
    roadmaps = res.scalars().all()

    output: List[RoadmapResponse] = []
    for r in roadmaps:
        progress = compute_roadmap_progress(r.items)
        output.append(
            RoadmapResponse(
                id=r.id,
                profile_id=r.profile_id,
                target_role=r.target_role,
                target_job_id=r.target_job_id,
                target_job_title=r.target_job.title if r.target_job else None,
                target_job_company=r.target_job.company if r.target_job else None,
                total_items=progress.total_items,
                completed_items=progress.completed_items,
                progress=progress,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return output


async def get_roadmap_detail(
    roadmap_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> RoadmapDetailResponse:
    """Retrieves single roadmap details with full items, prerequisites, and progress."""
    prof_stmt = select(CandidateProfile.id).where(CandidateProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile_id = prof_res.scalar_one_or_none()
    if not profile_id:
        raise NotFoundError(message="Roadmap not found.", code="ROADMAP_NOT_FOUND")

    stmt = (
        select(Roadmap)
        .where(Roadmap.id == roadmap_id, Roadmap.profile_id == profile_id)
        .options(
            selectinload(Roadmap.target_job),
            selectinload(Roadmap.items).selectinload(RoadmapItem.skill),
        )
    )
    res = await db.execute(stmt)
    roadmap = res.scalar_one_or_none()
    if not roadmap:
        raise NotFoundError(message=f"Roadmap '{roadmap_id}' not found.", code="ROADMAP_NOT_FOUND")

    # Load prerequisites map
    target_skill_alias = aliased(Skill)
    prereq_stmt = (
        select(
            Skill.id.label("skill_id"),
            target_skill_alias.name.label("prereq_name"),
        )
        .select_from(SkillPrerequisite)
        .join(Skill, SkillPrerequisite.skill_id == Skill.id)
        .join(target_skill_alias, SkillPrerequisite.prerequisite_skill_id == target_skill_alias.id)
    )
    prereq_res = await db.execute(prereq_stmt)
    prereqs_map: Dict[UUID, List[str]] = {}
    for sk_id, p_name in prereq_res.all():
        if sk_id not in prereqs_map:
            prereqs_map[sk_id] = []
        prereqs_map[sk_id].append(p_name)

    items_response: List[RoadmapItemResponse] = []
    for it in roadmap.items:
        s_name = it.skill.name if it.skill else None
        p_list = prereqs_map.get(it.skill_id, []) if it.skill_id else []
        items_response.append(
            RoadmapItemResponse(
                id=it.id,
                roadmap_id=it.roadmap_id,
                skill_id=it.skill_id,
                skill_name=s_name,
                title=it.title,
                description=it.description,
                stage_phase=it.stage_phase,
                priority=it.priority,
                estimated_hours=it.estimated_hours,
                recommended_action=it.recommended_action,
                suggested_project=it.suggested_project,
                status=it.status,
                sequence_order=it.sequence_order,
                completed_at=it.completed_at,
                prerequisites=p_list,
            )
        )

    progress = compute_roadmap_progress(roadmap.items)
    return RoadmapDetailResponse(
        id=roadmap.id,
        profile_id=roadmap.profile_id,
        target_role=roadmap.target_role,
        target_job_id=roadmap.target_job_id,
        target_job_title=roadmap.target_job.title if roadmap.target_job else None,
        target_job_company=roadmap.target_job.company if roadmap.target_job else None,
        total_items=progress.total_items,
        completed_items=progress.completed_items,
        progress=progress,
        items=items_response,
        created_at=roadmap.created_at,
        updated_at=roadmap.updated_at,
    )


async def update_roadmap_item_status(
    roadmap_id: UUID,
    item_id: UUID,
    new_status: str,
    user_id: UUID,
    db: AsyncSession,
) -> Tuple[RoadmapItemResponse, RoadmapProgressResponse]:
    """
    Updates the completion status of a roadmap item.
    Enforces user isolation, updates timestamps, and recalculates roadmap completion tallies.
    """
    prof_stmt = select(CandidateProfile.id).where(CandidateProfile.user_id == user_id)
    prof_res = await db.execute(prof_stmt)
    profile_id = prof_res.scalar_one_or_none()
    if not profile_id:
        raise NotFoundError(message="Roadmap not found.", code="ROADMAP_NOT_FOUND")

    stmt = (
        select(Roadmap)
        .where(Roadmap.id == roadmap_id, Roadmap.profile_id == profile_id)
        .options(
            selectinload(Roadmap.items).selectinload(RoadmapItem.skill),
        )
    )
    res = await db.execute(stmt)
    roadmap = res.scalar_one_or_none()
    if not roadmap:
        raise NotFoundError(message=f"Roadmap '{roadmap_id}' not found.", code="ROADMAP_NOT_FOUND")

    item = next((it for it in roadmap.items if it.id == item_id), None)
    if not item:
        raise NotFoundError(
            message=f"Roadmap item '{item_id}' not found in this roadmap.",
            code="ROADMAP_ITEM_NOT_FOUND",
        )

    # Update item status and completion timestamp
    item.status = new_status
    if new_status == "completed":
        item.completed_at = datetime.now(timezone.utc)
    else:
        item.completed_at = None

    # Recalculate and update roadmap counters
    progress = compute_roadmap_progress(roadmap.items)
    roadmap.completed_items = progress.completed_items
    roadmap.total_items = progress.total_items
    roadmap.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(item)

    # Load prerequisites for item
    p_list: List[str] = []
    if item.skill_id:
        target_skill_alias = aliased(Skill)
        prereq_stmt = (
            select(target_skill_alias.name)
            .select_from(SkillPrerequisite)
            .join(target_skill_alias, SkillPrerequisite.prerequisite_skill_id == target_skill_alias.id)
            .where(SkillPrerequisite.skill_id == item.skill_id)
        )
        p_res = await db.execute(prereq_stmt)
        p_list = p_res.scalars().all()

    item_resp = RoadmapItemResponse(
        id=item.id,
        roadmap_id=item.roadmap_id,
        skill_id=item.skill_id,
        skill_name=item.skill.name if item.skill else None,
        title=item.title,
        description=item.description,
        stage_phase=item.stage_phase,
        priority=item.priority,
        estimated_hours=item.estimated_hours,
        recommended_action=item.recommended_action,
        suggested_project=item.suggested_project,
        status=item.status,
        sequence_order=item.sequence_order,
        completed_at=item.completed_at,
        prerequisites=p_list,
    )
    return item_resp, progress
