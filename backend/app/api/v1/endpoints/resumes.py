"""
Resume Management API Endpoints: Upload, Text Extraction, Gemini Structured Parsing,
Staging Review, and Profile Application.
"""
from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.config import settings, PROJECT_ROOT
from app.core.exceptions import AppException, NotFoundError
from app.core.logging import logger
from app.db.session import get_db
from app.models.profile import (
    CandidateProfile,
    CandidateSkill,
    Certification,
    Education,
    Experience,
    Project,
)
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import (
    ResumeDetailResponse,
    ResumeResponse,
    StructuredResumeData,
)
from app.services.gemini_service import extract_structured_resume_with_gemini
from app.services.pdf_service import extract_text_from_pdf
from app.services.skill_matcher import match_extracted_skills

router = APIRouter()


def _sanitize_filename(name: str) -> str:
    """Sanitizes user-provided filename to prevent path traversal."""
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
    return cleaned[:100]


def _parse_date_safe(val: Optional[str]) -> Optional[date]:
    """Parses date string (YYYY-MM-DD or YYYY-MM or YYYY) safely."""
    if not val or not isinstance(val, str):
        return None
    val = val.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


@router.post(
    "",
    response_model=ResumeDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process PDF resume",
    description="Uploads a PDF resume, extracts text, calls Gemini AI for structured extraction, and maps skills.",
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeDetailResponse:
    # 1. Validate File Extension and MIME Type
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise AppException(
            message="Invalid file type. Only PDF documents (.pdf) are supported.",
            status_code=400,
            code="INVALID_FILE_TYPE",
        )

    # 2. Read File Bytes and Enforce Size Limits
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise AppException(
            message="Uploaded file is empty (0 bytes).",
            status_code=400,
            code="EMPTY_FILE",
        )

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise AppException(
            message=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.",
            status_code=413,
            code="FILE_TOO_LARGE",
        )

    # 3. Validate PDF Magic Bytes (%PDF-)
    if not content.startswith(b"%PDF"):
        raise AppException(
            message="Uploaded file is not a valid PDF document (missing PDF header signature).",
            status_code=400,
            code="INVALID_PDF_HEADER",
        )

    # 4. Save file safely inside project-controlled upload directory
    resume_id = uuid.uuid4()
    safe_name = _sanitize_filename(filename)
    stored_filename = f"{resume_id}_{safe_name}"

    upload_dir = settings.upload_path
    dest_path = (upload_dir / stored_filename).resolve()

    # Prevent directory traversal attacks
    if not str(dest_path).startswith(str(upload_dir.resolve())):
        raise AppException(
            message="Invalid destination path.",
            status_code=400,
            code="PATH_TRAVERSAL_DETECTED",
        )

    with open(dest_path, "wb") as f:
        f.write(content)

    # Store relative path relative to PROJECT_ROOT
    rel_path = str(dest_path.relative_to(PROJECT_ROOT)).replace("\\", "/")

    # 5. Create database record in 'uploaded' state
    resume = Resume(
        id=resume_id,
        user_id=current_user.id,
        file_name=safe_name,
        file_path=rel_path,
        file_size_bytes=file_size,
        status="uploaded",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    logger.info(f"Resume saved to disk: id={resume_id}, user={current_user.id}, size={file_size} bytes")

    # 6. Extract PDF text
    try:
        extracted_text = extract_text_from_pdf(dest_path)
        resume.raw_extracted_text = extracted_text
        resume.status = "processing"
        await db.commit()
    except AppException as exc:
        resume.status = "failed"
        resume.error_message = exc.message
        await db.commit()
        await db.refresh(resume)
        return ResumeDetailResponse.model_validate(resume)
    except Exception as exc:
        resume.status = "failed"
        resume.error_message = f"PDF extraction failed: {str(exc)}"
        await db.commit()
        await db.refresh(resume)
        return ResumeDetailResponse.model_validate(resume)

    # 7. Gemini Structured AI Extraction
    if not settings.GEMINI_API_KEY:
        resume.status = "failed"
        resume.error_message = (
            "Gemini API key is not configured in backend/.env. "
            "Text was extracted, but live AI structured parsing is pending configuration."
        )
        await db.commit()
        await db.refresh(resume)
        return ResumeDetailResponse.model_validate(resume)

    try:
        structured_data = await extract_structured_resume_with_gemini(extracted_text)

        # 8. Deterministic Skill Mapping against Master Taxonomy & Aliases
        if structured_data.skills:
            mapped_skills = await match_extracted_skills(structured_data.skills, db)
            structured_data.skills = mapped_skills

        # 9. Store in parsed_staging_json and set to pending_review
        resume.parsed_staging_json = structured_data.model_dump(mode="json")
        resume.status = "pending_review"
        resume.error_message = None
        await db.commit()
        await db.refresh(resume)

        logger.info(f"Resume {resume_id} processed successfully: pending candidate review.")
        return ResumeDetailResponse.model_validate(resume)

    except AppException as exc:
        resume.status = "failed"
        resume.error_message = exc.message
        await db.commit()
        await db.refresh(resume)
        return ResumeDetailResponse.model_validate(resume)
    except Exception as exc:
        logger.error(f"Unexpected error during resume processing: {exc}")
        resume.status = "failed"
        resume.error_message = f"AI structured extraction failed: {str(exc)}"
        await db.commit()
        await db.refresh(resume)
        return ResumeDetailResponse.model_validate(resume)


@router.get(
    "",
    response_model=List[ResumeResponse],
    summary="List current user's resumes",
    description="Returns a list of all resumes uploaded by the authenticated user.",
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ResumeResponse]:
    stmt = (
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    result = await db.execute(stmt)
    resumes = result.scalars().all()
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.get(
    "/{resume_id}",
    response_model=ResumeDetailResponse,
    summary="Get resume details and staging review draft",
    description="Retrieves a specific resume including its parsed staging data. Strictly user-isolated.",
)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeDetailResponse:
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()

    if resume is None:
        raise NotFoundError(
            message=f"Resume with ID '{resume_id}' not found.",
            code="RESUME_NOT_FOUND",
        )

    return ResumeDetailResponse.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a resume",
    description="Deletes a resume record and removes the physical file from disk. Strictly user-isolated.",
)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()

    if resume is None:
        raise NotFoundError(
            message=f"Resume with ID '{resume_id}' not found.",
            code="RESUME_NOT_FOUND",
        )

    # Safely remove physical file from disk
    try:
        physical_path = PROJECT_ROOT / resume.file_path
        if physical_path.exists():
            physical_path.unlink()
            logger.info(f"Deleted physical resume file: {physical_path}")
    except Exception as exc:
        logger.warning(f"Could not delete physical resume file: {exc}")

    await db.delete(resume)
    await db.commit()

    return {"message": "Resume deleted successfully."}


@router.post(
    "/{resume_id}/apply",
    status_code=status.HTTP_200_OK,
    summary="Apply reviewed staging data to candidate profile",
    description="Applies confirmed and reviewed resume data into the candidate's career profile and related entities.",
)
async def apply_resume_to_profile(
    resume_id: uuid.UUID,
    reviewed_data: Optional[StructuredResumeData] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    # 1. Fetch Resume and verify ownership
    stmt = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()

    if resume is None:
        raise NotFoundError(
            message=f"Resume with ID '{resume_id}' not found.",
            code="RESUME_NOT_FOUND",
        )

    # 2. Resolve data to apply (use provided reviewed_data or fallback to parsed_staging_json)
    if reviewed_data is not None:
        draft = reviewed_data
    elif resume.parsed_staging_json is not None:
        draft = StructuredResumeData.model_validate(resume.parsed_staging_json)
    else:
        raise AppException(
            message="No structured staging data available to apply for this resume.",
            status_code=400,
            code="NO_STAGING_DATA",
        )

    # 3. Retrieve or Create CandidateProfile
    prof_stmt = select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    prof_result = await db.execute(prof_stmt)
    profile = prof_result.scalar_one_or_none()

    exp_years = Decimal(str(round(draft.total_experience_years or 0.0, 1)))

    if profile is None:
        profile = CandidateProfile(
            user_id=current_user.id,
            target_role=draft.target_role or "Software Professional",
            headline=draft.headline,
            bio=draft.bio,
            target_location=draft.target_location,
            target_employment_type=draft.target_employment_type or "Full-time",
            total_experience_years=exp_years,
        )
        db.add(profile)
        await db.flush()  # assign profile.id
    else:
        if draft.target_role:
            profile.target_role = draft.target_role
        if draft.headline:
            profile.headline = draft.headline
        if draft.bio:
            profile.bio = draft.bio
        if draft.target_location:
            profile.target_location = draft.target_location
        if draft.target_employment_type:
            profile.target_employment_type = draft.target_employment_type
        if draft.total_experience_years > 0:
            profile.total_experience_years = exp_years

    # 4. Apply Skills (CandidateSkill)
    if draft.skills:
        for sk in draft.skills:
            if sk.canonical_skill_id:
                # Check for existing skill link
                cs_stmt = select(CandidateSkill).where(
                    CandidateSkill.profile_id == profile.id,
                    CandidateSkill.skill_id == sk.canonical_skill_id,
                )
                cs_res = await db.execute(cs_stmt)
                existing_cs = cs_res.scalar_one_or_none()

                if existing_cs:
                    existing_cs.proficiency_level = sk.proficiency_level or "intermediate"
                    existing_cs.years_experience = Decimal(str(round(sk.years_experience or 1.0, 1)))
                    existing_cs.is_verified = True
                    existing_cs.proficiency_source = "user_verified"
                else:
                    new_cs = CandidateSkill(
                        profile_id=profile.id,
                        skill_id=sk.canonical_skill_id,
                        proficiency_level=sk.proficiency_level or "intermediate",
                        years_experience=Decimal(str(round(sk.years_experience or 1.0, 1))),
                        is_verified=True,
                        proficiency_source="user_verified",
                    )
                    db.add(new_cs)

    # 5. Apply Education
    if draft.education:
        for edu in draft.education:
            new_edu = Education(
                profile_id=profile.id,
                institution=edu.institution or "Unknown Institution",
                degree=edu.degree or "Degree",
                field_of_study=edu.field_of_study or "General Studies",
                start_date=_parse_date_safe(edu.start_date),
                end_date=_parse_date_safe(edu.end_date),
                grade_gpa=edu.grade_gpa,
            )
            db.add(new_edu)

    # 6. Apply Experience
    if draft.experience:
        for exp in draft.experience:
            start_d = _parse_date_safe(exp.start_date) or date(2020, 1, 1)
            new_exp = Experience(
                profile_id=profile.id,
                company=exp.company or "Company",
                title=exp.title or "Role",
                location=exp.location,
                start_date=start_d,
                end_date=_parse_date_safe(exp.end_date),
                is_current=exp.is_current,
                description=exp.description,
                technologies=exp.technologies or [],
            )
            db.add(new_exp)

    # 7. Apply Projects
    if draft.projects:
        for proj in draft.projects:
            new_proj = Project(
                profile_id=profile.id,
                title=proj.title or "Project",
                description=proj.description or "Project description",
                repository_url=proj.repository_url,
                live_url=proj.live_url,
                technologies=proj.technologies or [],
            )
            db.add(new_proj)

    # 8. Apply Certifications
    if draft.certifications:
        for cert in draft.certifications:
            new_cert = Certification(
                profile_id=profile.id,
                name=cert.name or "Certification",
                issuing_organization=cert.issuing_organization or "Organization",
                issue_date=_parse_date_safe(cert.issue_date),
                credential_id=cert.credential_id,
                credential_url=cert.credential_url,
            )
            db.add(new_cert)

    # 9. Mark Resume as Applied
    resume.status = "applied"
    await db.commit()

    logger.info(f"Staged resume {resume_id} successfully applied to profile {profile.id}")
    return {
        "message": "Resume data applied to career profile successfully.",
        "profile_id": str(profile.id),
        "status": "applied",
        "skills_applied": len(draft.skills) if draft.skills else 0,
        "experience_records": len(draft.experience) if draft.experience else 0,
        "education_records": len(draft.education) if draft.education else 0,
        "project_records": len(draft.projects) if draft.projects else 0,
        "certification_records": len(draft.certifications) if draft.certifications else 0,
    }
