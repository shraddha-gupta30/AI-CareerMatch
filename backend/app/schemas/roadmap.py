"""
Pydantic Schemas for Personalized Career Roadmap and Progress Tracking.
Supports deterministic roadmap items, stage phases, priorities, status tracking,
and dynamic progress percentage calculations.
"""
from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class RoadmapItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roadmap_id: UUID
    skill_id: Optional[UUID] = None
    skill_name: Optional[str] = None
    title: str
    description: str
    stage_phase: int
    priority: str
    estimated_hours: int
    recommended_action: str
    suggested_project: Optional[str] = None
    status: str
    sequence_order: int
    completed_at: Optional[datetime] = None
    prerequisites: List[str] = Field(default_factory=list)


class RoadmapProgressResponse(BaseModel):
    total_items: int
    completed_items: int
    in_progress_items: int
    not_started_items: int
    progress_percentage: float = Field(..., ge=0.0, le=100.0)


class RoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    target_role: str
    target_job_id: Optional[UUID] = None
    target_job_title: Optional[str] = None
    target_job_company: Optional[str] = None
    total_items: int
    completed_items: int
    progress: RoadmapProgressResponse
    created_at: datetime
    updated_at: datetime


class RoadmapDetailResponse(RoadmapResponse):
    items: List[RoadmapItemResponse] = Field(default_factory=list)


# Alias for roadmap generation endpoint response
JobRoadmapGenerateResponse = RoadmapDetailResponse


class RoadmapItemStatusUpdate(BaseModel):
    status: Literal["not_started", "in_progress", "completed"]


class RoadmapItemUpdateResponse(BaseModel):
    item: RoadmapItemResponse
    roadmap_progress: RoadmapProgressResponse
