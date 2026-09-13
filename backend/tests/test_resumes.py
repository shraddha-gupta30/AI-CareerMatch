"""
Integration Tests for Resume Upload, Text Extraction, Gemini Structured Parsing,
Skill Mapping, Staging Review, and Profile Application.
"""
import io
import uuid
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.schemas.resume import (
    ExtractedEducationItem,
    ExtractedExperienceItem,
    ExtractedSkillItem,
    StructuredResumeData,
)

SAMPLE_VALID_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R>> endobj\n"
    b"4 0 obj <</Font <</F1 <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>>>>> endobj\n"
    b"5 0 obj <</Length 185>> stream\n"
    b"BT\n"
    b"/F1 12 Tf\n"
    b"72 712 Td\n"
    b"(Grace Hopper - Experienced Senior Systems Engineer specialized in Python, PostgreSQL, and Docker containerization with over seven years building distributed computing platforms.) Tj\n"
    b"ET\n"
    b"endstream\n"
    b"endobj\n"
    b"xref\n"
    b"0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000222 00000 n \n"
    b"0000000305 00000 n \n"
    b"trailer <</Size 6 /Root 1 0 R>>\n"
    b"startxref\n"
    b"543\n"
    b"%%EOF\n"
)

SAMPLE_MOCK_STRUCTURED_DATA = StructuredResumeData(
    full_name="Grace Hopper",
    target_role="Senior Systems Engineer",
    headline="Distributed Systems & Database Architect",
    bio="Over 7 years architecting resilient microservices and distributed computing systems.",
    target_location="Remote, Global",
    target_employment_type="Full-time",
    total_experience_years=7.5,
    skills=[
        ExtractedSkillItem(name="Python", proficiency_level="expert", years_experience=7.0),
        ExtractedSkillItem(name="Postgres", proficiency_level="advanced", years_experience=5.0),
        ExtractedSkillItem(name="Docker", proficiency_level="advanced", years_experience=4.0),
        ExtractedSkillItem(name="ObscureCustomSkill999", proficiency_level="beginner", years_experience=1.0),
    ],
    education=[
        ExtractedEducationItem(
            institution="Yale University",
            degree="Ph.D. in Mathematics",
            field_of_study="Mathematics",
            start_date="1930",
            end_date="1934",
            grade_gpa="4.0",
        )
    ],
    experience=[
        ExtractedExperienceItem(
            company="US Navy Computing Laboratory",
            title="Director of Systems Development",
            location="Arlington, VA",
            start_date="2017-01",
            end_date="2024-05",
            is_current=False,
            description="Pioneered distributed systems architecture and compiler design.",
            technologies=["Python", "PostgreSQL", "Docker"],
        )
    ],
)


async def _register_user(client: AsyncClient, name_suffix: str) -> tuple[dict, str]:
    uid = uuid.uuid4().hex[:8]
    email = f"resume_cand_{name_suffix}_{uid}@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": f"Candidate {name_suffix.capitalize()}",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    return data["user"], f"Bearer {data['access_token']}"


async def test_unauthenticated_upload_rejection(client: AsyncClient):
    """Verify unauthenticated resume upload is rejected with HTTP 401."""
    files = {"file": ("resume.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
    resp = await client.post("/api/v1/resumes", files=files)
    assert resp.status_code == 401


async def test_invalid_file_type_rejection(client: AsyncClient):
    """Verify non-PDF file extension is rejected with HTTP 400."""
    _, auth_header = await _register_user(client, "txtuser")
    files = {"file": ("document.txt", b"plain text content", "text/plain")}
    resp = await client.post(
        "/api/v1/resumes",
        files=files,
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_FILE_TYPE"


async def test_invalid_pdf_header_rejection(client: AsyncClient):
    """Verify file with .pdf extension but missing %PDF magic header is rejected."""
    _, auth_header = await _register_user(client, "fake_pdf")
    files = {"file": ("corrupt.pdf", b"NOT A VALID PDF FILE", "application/pdf")}
    resp = await client.post(
        "/api/v1/resumes",
        files=files,
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "INVALID_PDF_HEADER"


async def test_empty_file_rejection(client: AsyncClient):
    """Verify empty 0-byte file is rejected."""
    _, auth_header = await _register_user(client, "empty_file")
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    resp = await client.post(
        "/api/v1/resumes",
        files=files,
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "EMPTY_FILE"


async def test_oversized_file_rejection(client: AsyncClient):
    """Verify file exceeding MAX_UPLOAD_SIZE_BYTES is rejected with HTTP 413."""
    _, auth_header = await _register_user(client, "huge_file")
    large_content = b"%PDF" + (b"0" * (settings.MAX_UPLOAD_SIZE_BYTES + 1024))
    files = {"file": ("huge.pdf", large_content, "application/pdf")}
    resp = await client.post(
        "/api/v1/resumes",
        files=files,
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "FILE_TOO_LARGE"


async def test_authenticated_upload_and_extraction_with_gemini_mock(client: AsyncClient):
    """
    Verify complete upload workflow with mocked Gemini structured extraction.
    Validates text extraction, skill normalization against canonical taxonomy/aliases,
    and status transition to 'pending_review'.
    """
    user, auth_header = await _register_user(client, "hopper")

    with patch(
        "app.api.v1.endpoints.resumes.extract_structured_resume_with_gemini",
        return_value=SAMPLE_MOCK_STRUCTURED_DATA,
    ), patch.object(settings, "GEMINI_API_KEY", "mock_gemini_key_for_testing"):
        files = {"file": ("hopper_resume.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
        resp = await client.post(
            "/api/v1/resumes",
            files=files,
            headers={"Authorization": auth_header},
        )
        assert resp.status_code == 201
        data = resp.json()

        assert data["status"] == "pending_review"
        assert data["file_name"] == "hopper_resume.pdf"
        assert data["user_id"] == user["id"]
        assert data["parsed_staging_json"] is not None

        staging = data["parsed_staging_json"]
        assert staging["full_name"] == "Grace Hopper"
        assert staging["total_experience_years"] == 7.5

        # Verify Skill Normalization
        skills = staging["skills"]
        skill_dict = {s["name"]: s for s in skills}

        # Python -> Exact canonical match
        assert "Python" in skill_dict
        assert skill_dict["Python"]["matched"] is True
        assert skill_dict["Python"]["canonical_name"] == "Python"
        assert skill_dict["Python"]["category"] is not None

        # Postgres -> Alias match resolving to PostgreSQL
        assert "Postgres" in skill_dict
        assert skill_dict["Postgres"]["matched"] is True
        assert skill_dict["Postgres"]["canonical_name"] == "PostgreSQL"
        assert skill_dict["Postgres"]["category"] is not None

        # Docker -> Exact canonical match
        assert "Docker" in skill_dict
        assert skill_dict["Docker"]["matched"] is True

        # ObscureCustomSkill999 -> Unmatched, unknown source, no arbitrary category
        assert "ObscureCustomSkill999" in skill_dict
        assert skill_dict["ObscureCustomSkill999"]["matched"] is False
        assert skill_dict["ObscureCustomSkill999"]["proficiency_source"] == "unknown"


async def test_missing_gemini_api_key_handled_safely(client: AsyncClient):
    """
    Verify that when GEMINI_API_KEY is not configured, the endpoint handles it gracefully:
    stores extracted text, sets status to 'failed' with helpful error, does NOT crash or hallucinate.
    """
    user, auth_header = await _register_user(client, "nokey")

    with patch.object(settings, "GEMINI_API_KEY", ""):
        files = {"file": ("valid.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
        resp = await client.post(
            "/api/v1/resumes",
            files=files,
            headers={"Authorization": auth_header},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "failed"
        assert "Gemini API key is not configured" in data["error_message"]


async def test_resume_listing_and_retrieval(client: AsyncClient):
    """Verify listing and retrieving specific resume details."""
    user, auth_header = await _register_user(client, "listuser")

    with patch(
        "app.api.v1.endpoints.resumes.extract_structured_resume_with_gemini",
        return_value=SAMPLE_MOCK_STRUCTURED_DATA,
    ), patch.object(settings, "GEMINI_API_KEY", "mock_key"):
        files = {"file": ("my_resume.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
        upload_resp = await client.post(
            "/api/v1/resumes",
            files=files,
            headers={"Authorization": auth_header},
        )
        resume_id = upload_resp.json()["id"]

        # List resumes
        list_resp = await client.get("/api/v1/resumes", headers={"Authorization": auth_header})
        assert list_resp.status_code == 200
        resumes = list_resp.json()
        assert len(resumes) >= 1
        assert any(r["id"] == resume_id for r in resumes)

        # Retrieve specific resume
        get_resp = await client.get(
            f"/api/v1/resumes/{resume_id}",
            headers={"Authorization": auth_header},
        )
        assert get_resp.status_code == 200
        detail = get_resp.json()
        assert detail["id"] == resume_id
        assert detail["parsed_staging_json"] is not None


async def test_user_ownership_isolation(client: AsyncClient):
    """
    CRITICAL SECURITY INVARIANT:
    User A's resume cannot be retrieved, deleted, or applied by User B.
    """
    user_a, auth_a = await _register_user(client, "alice_resume")
    user_b, auth_b = await _register_user(client, "bob_resume")

    with patch(
        "app.api.v1.endpoints.resumes.extract_structured_resume_with_gemini",
        return_value=SAMPLE_MOCK_STRUCTURED_DATA,
    ), patch.object(settings, "GEMINI_API_KEY", "mock_key"):
        files = {"file": ("alice_cv.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
        upload_resp = await client.post(
            "/api/v1/resumes",
            files=files,
            headers={"Authorization": auth_a},
        )
        resume_id = upload_resp.json()["id"]

        # User B attempts to view Alice's resume -> 404
        get_resp = await client.get(
            f"/api/v1/resumes/{resume_id}",
            headers={"Authorization": auth_b},
        )
        assert get_resp.status_code == 404

        # User B attempts to delete Alice's resume -> 404
        del_resp = await client.delete(
            f"/api/v1/resumes/{resume_id}",
            headers={"Authorization": auth_b},
        )
        assert del_resp.status_code == 404

        # User B attempts to apply Alice's resume -> 404
        apply_resp = await client.post(
            f"/api/v1/resumes/{resume_id}/apply",
            headers={"Authorization": auth_b},
        )
        assert apply_resp.status_code == 404


async def test_apply_staged_resume_to_profile(client: AsyncClient):
    """
    Verify that applying staged resume data commits skills, education, and experience
    to the candidate's career profile and sets resume status to 'applied'.
    """
    user, auth_header = await _register_user(client, "applier")

    with patch(
        "app.api.v1.endpoints.resumes.extract_structured_resume_with_gemini",
        return_value=SAMPLE_MOCK_STRUCTURED_DATA,
    ), patch.object(settings, "GEMINI_API_KEY", "mock_key"):
        files = {"file": ("applier_cv.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
        upload_resp = await client.post(
            "/api/v1/resumes",
            files=files,
            headers={"Authorization": auth_header},
        )
        resume_id = upload_resp.json()["id"]

        # Apply staged data
        apply_resp = await client.post(
            f"/api/v1/resumes/{resume_id}/apply",
            headers={"Authorization": auth_header},
        )
        assert apply_resp.status_code == 200
        assert apply_resp.json()["status"] == "applied"

        # Verify profile updated
        profile_resp = await client.get("/api/v1/profile", headers={"Authorization": auth_header})
        assert profile_resp.status_code == 200
        prof_data = profile_resp.json()
        assert prof_data["target_role"] == "Senior Systems Engineer"
        assert prof_data["headline"] == "Distributed Systems & Database Architect"
        assert prof_data["total_experience_years"] == 7.5


async def test_delete_resume(client: AsyncClient):
    """Verify owner can delete their resume and that subsequent queries return 404."""
    user, auth_header = await _register_user(client, "deleter")

    with patch(
        "app.api.v1.endpoints.resumes.extract_structured_resume_with_gemini",
        return_value=SAMPLE_MOCK_STRUCTURED_DATA,
    ), patch.object(settings, "GEMINI_API_KEY", "mock_key"):
        files = {"file": ("delete_me.pdf", SAMPLE_VALID_PDF_BYTES, "application/pdf")}
        upload_resp = await client.post(
            "/api/v1/resumes",
            files=files,
            headers={"Authorization": auth_header},
        )
        resume_id = upload_resp.json()["id"]

        # Delete resume
        del_resp = await client.delete(
            f"/api/v1/resumes/{resume_id}",
            headers={"Authorization": auth_header},
        )
        assert del_resp.status_code == 200

        # Verify 404 on subsequent get
        get_resp = await client.get(
            f"/api/v1/resumes/{resume_id}",
            headers={"Authorization": auth_header},
        )
        assert get_resp.status_code == 404
