"""
Health Check Schemas.
"""
from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
    connected: bool
    details: Optional[str] = None
