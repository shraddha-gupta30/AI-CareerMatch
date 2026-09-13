"""
Gemini AI Service for Structured Resume Extraction.
Utilizes the official Google GenAI SDK with strict JSON schema adherence.
"""
import json
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger
from app.schemas.resume import StructuredResumeData

RESUME_EXTRACTION_SYSTEM_INSTRUCTION = """
You are an expert technical resume parser and career data extraction engine.
Your mission is to accurately parse the provided raw resume text into structured JSON.

CRITICAL EXTRACTION RULES:
1. FACTUAL FIDELITY: Extract ONLY information explicitly stated or directly supported by the resume text.
2. NO FABRICATION: NEVER invent degrees, certifications, companies, dates, or technical skills not present in the text.
3. UNKNOWN FIELDS: If a field (such as GPA, end date, location, or bio) is not mentioned in the resume, leave it null/empty.
4. SKILLS: Extract individual technical skills, tools, programming languages, databases, and frameworks mentioned in the text. For each skill, assign an estimated proficiency level ('beginner', 'intermediate', 'advanced', 'expert') based on the candidate's years of usage or project context.
5. EXPERIENCE DURATION: Estimate total cumulative relevant work experience in years (decimal, e.g. 3.5) based on the employment history date ranges.
6. OUTPUT FORMAT: Return ONLY valid JSON matching the required schema. Do not enclose in markdown code fences.
"""

EXTRACTION_SCHEMA_PROMPT = """
Parse the following resume text into this exact JSON structure:
{
  "full_name": string or null,
  "headline": string or null,
  "bio": string or null,
  "target_role": string or null,
  "target_location": string or null,
  "target_employment_type": "Full-time" or other string,
  "total_experience_years": number (e.g. 3.5),
  "skills": [
    {
      "name": "Python",
      "proficiency_level": "advanced",
      "years_experience": 3.0
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "B.S. in Computer Science",
      "field_of_study": "Computer Science",
      "start_date": "YYYY-MM-DD" or "YYYY" or null,
      "end_date": "YYYY-MM-DD" or "YYYY" or null,
      "grade_gpa": "3.8/4.0" or null
    }
  ],
  "experience": [
    {
      "company": "Company Name",
      "title": "Software Engineer",
      "location": "City, State or Remote" or null,
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM" or null,
      "is_current": boolean,
      "description": "Key contributions...",
      "technologies": ["Python", "FastAPI", "Docker"]
    }
  ],
  "projects": [
    {
      "title": "Project Name",
      "description": "Project overview...",
      "repository_url": "https://github.com/..." or null,
      "live_url": "https://..." or null,
      "technologies": ["React", "TypeScript"]
    }
  ],
  "certifications": [
    {
      "name": "AWS Solutions Architect",
      "issuing_organization": "Amazon Web Services",
      "issue_date": "YYYY-MM-DD" or null,
      "credential_id": string or null,
      "credential_url": string or null
    }
  ]
}

RESUME TEXT TO PARSE:
"""


async def extract_structured_resume_with_gemini(
    resume_text: str,
    api_key_override: Optional[str] = None,
) -> StructuredResumeData:
    """
    Calls Google Gemini to convert raw extracted resume text into structured candidate data.
    Raises AppException if API key is missing or if extraction fails.
    """
    api_key = api_key_override or settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("Gemini extraction aborted: GEMINI_API_KEY is not configured in environment.")
        raise AppException(
            message=(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
                "to enable automated AI resume extraction."
            ),
            status_code=503,
            code="GEMINI_API_KEY_MISSING",
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt_content = f"{RESUME_EXTRACTION_SYSTEM_INSTRUCTION}\n{EXTRACTION_SCHEMA_PROMPT}\n{resume_text}"

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt_content,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        response_text = response.text or ""
        # Clean any accidental code block wraps
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        cleaned_text = cleaned_text.strip()

        parsed_dict = json.loads(cleaned_text)
        structured_data = StructuredResumeData.model_validate(parsed_dict)

        logger.info(
            f"Successfully parsed resume via Gemini: {len(structured_data.skills)} skills, "
            f"{len(structured_data.experience)} jobs, {len(structured_data.education)} degrees."
        )
        return structured_data

    except AppException:
        raise
    except Exception as exc:
        logger.error(f"Gemini structured extraction failed: {exc}")
        raise AppException(
            message=f"Gemini structured extraction encountered an error: {str(exc)}",
            status_code=502,
            code="GEMINI_EXTRACTION_ERROR",
        )
