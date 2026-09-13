"""
Personalized Career Roadmap and Progress Tracking Endpoints.
Provides endpoints for retrieving user roadmaps, inspecting milestone items,
and updating item completion status.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.roadmap import (
    RoadmapDetailResponse,
    RoadmapItemStatusUpdate,
    RoadmapItemUpdateResponse,
    RoadmapResponse,
)
from app.services.roadmap_service import (
    get_roadmap_detail,
    get_user_roadmaps,
    update_roadmap_item_status,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[RoadmapResponse],
    summary="List Candidate Roadmaps",
    description="Returns all personalized career roadmaps generated for the authenticated candidate.",
)
async def list_candidate_roadmaps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[RoadmapResponse]:
    return await get_user_roadmaps(user_id=current_user.id, db=db)


@router.get(
    "/{roadmap_id}",
    response_model=RoadmapDetailResponse,
    summary="Get Roadmap Details",
    description="Returns complete details, sequenced items, prerequisites, and dynamic progress for a roadmap.",
)
async def get_candidate_roadmap_detail(
    roadmap_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapDetailResponse:
    return await get_roadmap_detail(
        roadmap_id=roadmap_id,
        user_id=current_user.id,
        db=db,
    )


@router.patch(
    "/{roadmap_id}/items/{item_id}",
    response_model=RoadmapItemUpdateResponse,
    summary="Update Roadmap Item Status",
    description="Updates the completion status of a roadmap milestone item and recalculates overall roadmap progress.",
)
async def update_item_status(
    roadmap_id: UUID,
    item_id: UUID,
    payload: RoadmapItemStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapItemUpdateResponse:
    item, progress = await update_roadmap_item_status(
        roadmap_id=roadmap_id,
        item_id=item_id,
        new_status=payload.status,
        user_id=current_user.id,
        db=db,
    )
    return RoadmapItemUpdateResponse(
        item=item,
        roadmap_progress=progress,
    )
