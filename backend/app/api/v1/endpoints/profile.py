"""
Candidate Career Profile API Endpoints: Retrieval and Update.
"""
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.logging import logger
from app.db.session import get_db
from app.models.profile import CandidateProfile
from app.models.user import User
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter()


@router.get(
    "",
    response_model=Optional[ProfileResponse],
    summary="Get current user's career profile",
    description="Retrieves the career profile of the authenticated user. Returns null if no profile has been created yet.",
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[ProfileResponse]:
    stmt = select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        return None

    # Attach current_user reference to satisfy nested user response schema
    profile.user = current_user
    return ProfileResponse.model_validate(profile)


@router.put(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update current user's career profile",
    description="Upserts the career profile for the authenticated candidate.",
)
@router.patch(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update current user's career profile",
    description="Partially updates or creates the career profile for the authenticated candidate.",
)
async def upsert_my_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    stmt = select(CandidateProfile).where(CandidateProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    exp_decimal = Decimal(str(round(payload.total_experience_years, 1)))

    if profile is None:
        profile = CandidateProfile(
            user_id=current_user.id,
            target_role=payload.target_role,
            headline=payload.headline,
            bio=payload.bio,
            target_location=payload.target_location,
            target_employment_type=payload.target_employment_type,
            total_experience_years=exp_decimal,
        )
        db.add(profile)
        logger.info(f"Created new profile for user_id={current_user.id}")
    else:
        profile.target_role = payload.target_role
        profile.headline = payload.headline
        profile.bio = payload.bio
        profile.target_location = payload.target_location
        profile.target_employment_type = payload.target_employment_type
        profile.total_experience_years = exp_decimal
        logger.info(f"Updated profile for user_id={current_user.id}")

    await db.commit()
    await db.refresh(profile)

    profile.user = current_user
    return ProfileResponse.model_validate(profile)
