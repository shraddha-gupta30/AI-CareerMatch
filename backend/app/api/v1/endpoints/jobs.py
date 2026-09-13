"""
Job Discovery and Deterministic Matching API Endpoints.
Provides controlled internal job catalog discovery, filtering, pagination,
saved jobs management, and explainable match score evaluations.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_optional_current_user
from app.core.exceptions import AppException, NotFoundError
from app.core.logging import logger
from app.db.session import get_db
from app.models.activity import CandidateActivity
from app.models.job import Job, JobSkill, SavedJob
from app.models.match import JobMatch
from app.models.profile import CandidateProfile
from app.models.skill import Skill, SkillAlias, SkillRelationship
from app.models.user import User
from app.schemas.job import (
    JobDetailResponse,
    JobMatchBreakdownResponse,
    JobResponse,
    JobSkillResponse,
    PaginatedJobsResponse,
    SavedJobResponse,
)
from app.services.matching_engine import calculate_job_match

router = APIRouter()


async def _get_skill_taxonomy_maps(db: AsyncSession) -> tuple[Dict[str, Dict[str, float]], Dict[str, str]]:
    """Loads explicit skill relationships and aliases into in-memory lookup maps."""
    # 1. Relationships map: source_canonical -> { target_canonical: weight }
    rel_stmt = select(
        SkillRelationship.similarity_weight,
        Skill.name.label("source_name"),
    ).join(Skill, SkillRelationship.source_skill_id == Skill.id)

    rel_query = (
        select(
            SkillRelationship.similarity_weight,
            Skill.name.label("source_name"),
        )
    )
    # Full select with both source and target skill names
    source_skill = Skill
    from sqlalchemy.orm import aliased
    target_skill_alias = aliased(Skill)

    stmt = (
        select(
            Skill.name.label("source_name"),
            target_skill_alias.name.label("target_name"),
            SkillRelationship.similarity_weight,
        )
        .join(Skill, SkillRelationship.source_skill_id == Skill.id)
        .join(target_skill_alias, SkillRelationship.target_skill_id == target_skill_alias.id)
    )
    res = await db.execute(stmt)
    rel_map: Dict[str, Dict[str, float]] = {}
    for src, tgt, weight in res.all():
        if src not in rel_map:
            rel_map[src] = {}
        rel_map[src][tgt] = float(weight)

    # 2. Alias map: normalized_alias -> canonical_name
    alias_stmt = (
        select(SkillAlias.alias, Skill.name)
        .join(Skill, SkillAlias.skill_id == Skill.id)
    )
    alias_res = await db.execute(alias_stmt)
    alias_map: Dict[str, str] = {}
    for a, c_name in alias_res.all():
        clean_alias = a.strip().lower().replace(" ", "").replace(".", "")
        alias_map[clean_alias] = c_name

    return rel_map, alias_map


def _serialize_job(job: Job, is_saved: bool = False, match_score: Optional[float] = None) -> JobResponse:
    skills_list = []
    for js in getattr(job, "job_skills", []) or []:
        s_obj = getattr(js, "skill", None)
        s_name = getattr(s_obj, "name", "Skill") if s_obj else "Skill"
        s_cat = getattr(s_obj, "category", None) if s_obj else None
        skills_list.append(
            JobSkillResponse(
                id=js.id,
                skill_id=js.skill_id,
                name=s_name,
                category=s_cat,
                is_required=js.is_required,
                importance_weight=float(js.importance_weight),
                min_proficiency=js.min_proficiency,
            )
        )
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        min_experience_years=float(job.min_experience_years),
        target_education_level=job.target_education_level,
        description=job.description,
        salary_range=job.salary_range,
        is_active=job.is_active,
        created_at=job.created_at,
        skills=skills_list,
        is_saved=is_saved,
        match_score=match_score,
    )


@router.get(
    "",
    response_model=PaginatedJobsResponse,
    summary="List and filter curated jobs",
    description="Discovers controlled job postings with search, multi-faceted filtering, pagination, and optional match evaluation.",
)
async def list_jobs(
    search: Optional[str] = Query(None, description="Search term in title, company, or description"),
    role: Optional[str] = Query(None, description="Filter by title / role"),
    location: Optional[str] = Query(None, description="Filter by location (e.g. Remote, City)"),
    employment_type: Optional[str] = Query(None, description="Filter by employment type (full-time, part-time, contract)"),
    experience_level: Optional[str] = Query(None, description="Filter by level (entry, mid, senior)"),
    skill: Optional[str] = Query(None, description="Filter by required or preferred skill name"),
    saved_only: bool = Query(False, description="Filter only jobs bookmarked by current authenticated user"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=50, description="Items per page"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedJobsResponse:
    # 1. Base Query with Eager Loading of job_skills and skills
    query = (
        select(Job)
        .where(Job.is_active == True)
        .options(
            selectinload(Job.job_skills).selectinload(JobSkill.skill),
        )
    )

    # 2. Apply Filters
    if search:
        s_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Job.title.ilike(s_term),
                Job.company.ilike(s_term),
                Job.location.ilike(s_term),
                Job.description.ilike(s_term),
            )
        )

    if role:
        query = query.where(Job.title.ilike(f"%{role.strip()}%"))

    if location:
        query = query.where(Job.location.ilike(f"%{location.strip()}%"))

    if employment_type:
        query = query.where(Job.employment_type.ilike(f"%{employment_type.strip()}%"))

    if experience_level:
        query = query.where(Job.experience_level.ilike(f"%{experience_level.strip()}%"))

    if skill:
        skill_term = f"%{skill.strip()}%"
        query = query.join(Job.job_skills).join(JobSkill.skill).where(Skill.name.ilike(skill_term))

    # Saved only filter
    saved_job_ids: Set[uuid.UUID] = set()
    if current_user:
        saved_stmt = select(SavedJob.job_id).where(SavedJob.user_id == current_user.id)
        saved_res = await db.execute(saved_stmt)
        saved_job_ids = set(saved_res.scalars().all())

        if saved_only:
            query = query.where(Job.id.in_(saved_job_ids))
    elif saved_only:
        # Unauthenticated user asked for saved only -> empty result
        return PaginatedJobsResponse(items=[], total=0, page=page, limit=limit, pages=0)

    # 3. Count Total Items
    count_subq = query.order_by(None).subquery()
    count_stmt = select(func.count()).select_from(count_subq)
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # 4. Apply Pagination
    offset = (page - 1) * limit
    paged_query = query.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    res = await db.execute(paged_query)
    jobs = res.scalars().all()

    # 5. Calculate Match Scores if candidate has an active profile
    profile: Optional[CandidateProfile] = None
    rel_map: Dict[str, Dict[str, float]] = {}
    alias_map: Dict[str, str] = {}

    if current_user:
        prof_stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.user_id == current_user.id)
            .options(
                selectinload(CandidateProfile.skills).selectinload(CandidateProfile.skills.property.mapper.class_.skill),
                selectinload(CandidateProfile.education),
                selectinload(CandidateProfile.experience),
            )
        )
        p_res = await db.execute(prof_stmt)
        profile = p_res.scalar_one_or_none()

        if profile:
            rel_map, alias_map = await _get_skill_taxonomy_maps(db)

    # 6. Format Items
    items = []
    for j in jobs:
        is_saved = j.id in saved_job_ids
        match_score: Optional[float] = None

        if profile:
            match_res = calculate_job_match(profile, j, rel_map, alias_map)
            match_score = match_res.overall_score

        items.append(_serialize_job(j, is_saved=is_saved, match_score=match_score))

    pages = (total + limit - 1) // limit if total > 0 else 0
    return PaginatedJobsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get(
    "/saved",
    response_model=List[SavedJobResponse],
    summary="List candidate's bookmarked jobs",
    description="Returns all jobs bookmarked by the authenticated candidate.",
)
async def list_saved_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SavedJobResponse]:
    stmt = (
        select(SavedJob)
        .where(SavedJob.user_id == current_user.id)
        .options(
            selectinload(SavedJob.job)
            .selectinload(Job.job_skills)
            .selectinload(JobSkill.skill)
        )
        .order_by(SavedJob.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    response_items = []
    for r in records:
        serialized_job = _serialize_job(r.job, is_saved=True)
        response_items.append(
            SavedJobResponse(
                id=r.id,
                job_id=r.job_id,
                created_at=r.created_at,
                job=serialized_job,
            )
        )
    return response_items


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get single job details",
    description="Retrieves a single job posting by UUID, including required and preferred skills.",
)
async def get_job(
    job_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobDetailResponse:
    stmt = (
        select(Job)
        .where(Job.id == job_id, Job.is_active == True)
        .options(
            selectinload(Job.job_skills).selectinload(JobSkill.skill),
        )
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise NotFoundError(message=f"Job posting '{job_id}' not found or inactive.", code="JOB_NOT_FOUND")

    is_saved = False
    cached_match_dict: Optional[Dict[str, Any]] = None
    match_score: Optional[float] = None

    if current_user:
        # Check saved
        s_stmt = select(SavedJob).where(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id)
        s_res = await db.execute(s_stmt)
        is_saved = s_res.scalar_one_or_none() is not None

        # Check existing match cache
        prof_stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.user_id == current_user.id)
            .options(
                selectinload(CandidateProfile.skills).selectinload(CandidateProfile.skills.property.mapper.class_.skill),
                selectinload(CandidateProfile.education),
                selectinload(CandidateProfile.experience),
            )
        )
        p_res = await db.execute(prof_stmt)
        profile = p_res.scalar_one_or_none()

        if profile:
            rel_map, alias_map = await _get_skill_taxonomy_maps(db)
            match_res = calculate_job_match(profile, job, rel_map, alias_map)
            match_score = match_res.overall_score
            cached_match_dict = match_res.to_dict()

    base_job = _serialize_job(job, is_saved=is_saved, match_score=match_score)
    return JobDetailResponse(
        **base_job.model_dump(),
        cached_match=cached_match_dict,
    )


@router.get(
    "/{job_id}/match",
    response_model=JobMatchBreakdownResponse,
    summary="Evaluate deterministic match against candidate profile",
    description="Calculates a 100% reproducible, explainable match breakdown against the authenticated candidate's Career Profile.",
)
async def evaluate_job_match(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobMatchBreakdownResponse:
    # 1. Fetch Job
    j_stmt = (
        select(Job)
        .where(Job.id == job_id, Job.is_active == True)
        .options(
            selectinload(Job.job_skills).selectinload(JobSkill.skill),
        )
    )
    j_res = await db.execute(j_stmt)
    job = j_res.scalar_one_or_none()
    if not job:
        raise NotFoundError(message=f"Job posting '{job_id}' not found.", code="JOB_NOT_FOUND")

    # 2. Fetch Profile
    prof_stmt = (
        select(CandidateProfile)
        .where(CandidateProfile.user_id == current_user.id)
        .options(
            selectinload(CandidateProfile.skills).selectinload(CandidateProfile.skills.property.mapper.class_.skill),
            selectinload(CandidateProfile.education),
            selectinload(CandidateProfile.experience),
        )
    )
    p_res = await db.execute(prof_stmt)
    profile = p_res.scalar_one_or_none()

    if not profile:
        raise AppException(
            message="Career Profile is required to evaluate job match. Please complete your profile first.",
            status_code=404,
            code="PROFILE_REQUIRED",
        )

    # 3. Load Taxonomy Relationships & Aliases
    rel_map, alias_map = await _get_skill_taxonomy_maps(db)

    # 4. Pure Deterministic Calculation
    result = calculate_job_match(profile, job, rel_map, alias_map)

    # 5. Persist/Cache Match Result in PostgreSQL
    m_stmt = select(JobMatch).where(
        JobMatch.profile_id == profile.id,
        JobMatch.job_id == job.id,
    )
    m_res = await db.execute(m_stmt)
    existing_match = m_res.scalar_one_or_none()

    breakdown_data = result.to_dict()

    if existing_match:
        existing_match.overall_score = Decimal(str(result.overall_score))
        existing_match.skill_score = Decimal(str(result.required_skills_score))
        existing_match.experience_score = Decimal(str(result.experience_score))
        existing_match.education_score = Decimal(str(result.education_score))
        existing_match.breakdown_json = breakdown_data
        existing_match.ai_explanation = result.explanation
    else:
        new_match = JobMatch(
            profile_id=profile.id,
            job_id=job.id,
            overall_score=Decimal(str(result.overall_score)),
            skill_score=Decimal(str(result.required_skills_score)),
            experience_score=Decimal(str(result.experience_score)),
            education_score=Decimal(str(result.education_score)),
            breakdown_json=breakdown_data,
            ai_explanation=result.explanation,
        )
        db.add(new_match)

    await db.commit()
    logger.info(f"Evaluated job match: user={current_user.id}, job={job.id}, score={result.overall_score}%")

    return JobMatchBreakdownResponse.model_validate(breakdown_data)


@router.post(
    "/{job_id}/save",
    status_code=status.HTTP_200_OK,
    summary="Bookmark a job",
    description="Saves a job posting for the authenticated user and logs candidate activity.",
)
async def save_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    # Check job exists
    j_stmt = select(Job).where(Job.id == job_id, Job.is_active == True)
    j_res = await db.execute(j_stmt)
    job = j_res.scalar_one_or_none()
    if not job:
        raise NotFoundError(message=f"Job posting '{job_id}' not found.", code="JOB_NOT_FOUND")

    # Check if already saved
    s_stmt = select(SavedJob).where(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id,
    )
    s_res = await db.execute(s_stmt)
    existing = s_res.scalar_one_or_none()

    if not existing:
        saved_entry = SavedJob(
            user_id=current_user.id,
            job_id=job_id,
        )
        db.add(saved_entry)

        # Audit trail
        activity = CandidateActivity(
            user_id=current_user.id,
            activity_type="job_saved",
            description=f"Saved job '{job.title}' at {job.company}",
            activity_metadata={"job_id": str(job_id), "title": job.title, "company": job.company},
        )
        db.add(activity)
        await db.commit()

    return {"saved": True, "job_id": str(job_id)}


@router.delete(
    "/{job_id}/save",
    status_code=status.HTTP_200_OK,
    summary="Remove a saved job",
    description="Un-bookmarks a previously saved job and logs candidate activity.",
)
async def unsave_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    s_stmt = select(SavedJob).where(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id,
    )
    s_res = await db.execute(s_stmt)
    existing = s_res.scalar_one_or_none()

    if existing:
        await db.delete(existing)

        # Audit trail
        activity = CandidateActivity(
            user_id=current_user.id,
            activity_type="job_unsaved",
            description=f"Removed bookmark for job ID {job_id}",
            activity_metadata={"job_id": str(job_id)},
        )
        db.add(activity)
        await db.commit()

    return {"saved": False, "job_id": str(job_id)}
