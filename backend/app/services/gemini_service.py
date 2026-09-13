"""
Gemini Service Bridge: Re-exports implementation from app.ai.gemini_service.
"""
from app.ai.gemini_service import (
    RESUME_EXTRACTION_SYSTEM_INSTRUCTION,
    EXTRACTION_SCHEMA_PROMPT,
    extract_structured_resume_with_gemini,
)

__all__ = [
    "RESUME_EXTRACTION_SYSTEM_INSTRUCTION",
    "EXTRACTION_SCHEMA_PROMPT",
    "extract_structured_resume_with_gemini",
]
