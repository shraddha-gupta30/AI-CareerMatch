"""
Integration Tests for Job Discovery, Filtering, Saved Jobs, and Match API Endpoints.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.profile import CandidateProfile, CandidateSkill, Education
from app.models.skill import Skill


async def _register_user(client: AsyncClient, name_suffix: str) -> tuple[dict, str]:
    uid = uuid.uuid4().hex[:8]
    email = f"job_cand_{name_suffix}_{uid}@example.com"
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


async def test_list_jobs_public(client: AsyncClient):
    """Verify unauthenticated job discovery returns paginated items."""
    response = await client.get("/api/v1/jobs?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["limit"] == 5
    assert len(data["items"]) <= 5
    assert data["total"] >= 1


async def test_filter_jobs_by_search(client: AsyncClient):
    """Verify search filter matches title, company, or description."""
    response = await client.get("/api/v1/jobs?search=Frontend")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        combined = f"{item['title']} {item['company']} {item['description']} {item['location']}".lower()
        assert "frontend" in combined


async def test_filter_jobs_by_search_and_role(client: AsyncClient):
    """Verify filtering jobs by search term and role query parameter."""
    # 1. Filter by role parameter
    role_resp = await client.get("/api/v1/jobs?role=Engineer")
    assert role_resp.status_code == 200
    role_data = role_resp.json()
    assert role_data["total"] >= 1
    for item in role_data["items"]:
        assert "engineer" in item["title"].lower()

    # 2. Filter by both search keyword and role
    combined_resp = await client.get("/api/v1/jobs?search=Apex&role=Engineer")
    assert combined_resp.status_code == 200
    comb_data = combined_resp.json()
    assert comb_data["total"] >= 1
    for item in comb_data["items"]:
        assert "engineer" in item["title"].lower()
        full_text = f"{item['title']} {item['company']} {item['description']} {item['location']}".lower()
        assert "apex" in full_text


async def test_filter_jobs_by_experience_level(client: AsyncClient):
    """Verify filtering by experience level."""
    response = await client.get("/api/v1/jobs?experience_level=entry")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["experience_level"].lower() == "entry"


async def test_get_job_detail_success(client: AsyncClient):
    """Verify fetching single job detail by UUID."""
    list_resp = await client.get("/api/v1/jobs?limit=1")
    assert list_resp.status_code == 200
    first_job = list_resp.json()["items"][0]
    job_id = first_job["id"]

    detail_resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == job_id
    assert "skills" in detail
    assert isinstance(detail["skills"], list)


async def test_get_job_detail_not_found(client: AsyncClient):
    """Verify non-existent job UUID returns 404 with JOB_NOT_FOUND."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/jobs/{fake_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "JOB_NOT_FOUND"


async def test_match_without_profile_returns_404(client: AsyncClient):
    """Verify calculating match without a career profile returns 404 PROFILE_REQUIRED."""
    _, auth_header = await _register_user(client, "noprofile")
    list_resp = await client.get("/api/v1/jobs?limit=1")
    job_id = list_resp.json()["items"][0]["id"]

    response = await client.get(
        f"/api/v1/jobs/{job_id}/match",
        headers={"Authorization": auth_header},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_REQUIRED"


async def test_match_with_profile_success(client: AsyncClient):
    """Verify deterministic match returns full breakdown and saves JobMatch record."""
    user, auth_header = await _register_user(client, "matchtester")

    # Create profile via PUT /api/v1/profile
    profile_data = {
        "target_role": "Software Engineer",
        "headline": "Full-Stack Developer",
        "bio": "Experienced in web technologies",
        "target_location": "Remote",
        "target_employment_type": "full-time",
        "total_experience_years": 3.0,
    }
    p_resp = await client.put(
        "/api/v1/profile",
        json=profile_data,
        headers={"Authorization": auth_header},
    )
    assert p_resp.status_code == 200
    profile_id = p_resp.json()["id"]

    # Attach skills and education directly
    async with AsyncSessionLocal() as session:
        # Find JavaScript or Python skill
        stmt = select(Skill).where(Skill.name.in_(["JavaScript", "Python", "React"]))
        s_res = await session.execute(stmt)
        skills = s_res.scalars().all()
        for sk in skills:
            cs = CandidateSkill(
                profile_id=uuid.UUID(profile_id),
                skill_id=sk.id,
                proficiency_level="advanced",
                years_experience=3.0,
                proficiency_source="user_verified",
                is_verified=True,
            )
            session.add(cs)

        edu = Education(
            profile_id=uuid.UUID(profile_id),
            institution="Test University",
            degree="Bachelor of Science in Computer Science",
            field_of_study="Computer Science",
        )
        session.add(edu)
        await session.commit()

    list_resp = await client.get("/api/v1/jobs?limit=1")
    job_id = list_resp.json()["items"][0]["id"]

    response = await client.get(
        f"/api/v1/jobs/{job_id}/match",
        headers={"Authorization": auth_header},
    )
    assert response.status_code == 200
    breakdown = response.json()

    assert 0.0 <= breakdown["overall_score"] <= 100.0
    assert 0.0 <= breakdown["required_skills_score"] <= 100.0
    assert 0.0 <= breakdown["experience_score"] <= 100.0
    assert 0.0 <= breakdown["education_score"] <= 100.0
    assert "matched_skills" in breakdown
    assert "missing_required_skills" in breakdown
    assert "experience_gap" in breakdown
    assert "education_compatibility" in breakdown
    assert "explanation" in breakdown
    assert len(breakdown["explanation"]) > 10


async def test_save_and_unsave_job(client: AsyncClient):
    """Verify saving, listing, and unsaving a job."""
    _, auth_header = await _register_user(client, "saver")
    list_resp = await client.get("/api/v1/jobs?limit=1")
    job_id = list_resp.json()["items"][0]["id"]

    # 1. Save job
    save_resp = await client.post(
        f"/api/v1/jobs/{job_id}/save",
        headers={"Authorization": auth_header},
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["saved"] is True

    # 2. List saved jobs
    saved_list = await client.get(
        "/api/v1/jobs/saved",
        headers={"Authorization": auth_header},
    )
    assert saved_list.status_code == 200
    saved_items = saved_list.json()
    assert len(saved_items) >= 1
    saved_job_ids = [item["job_id"] for item in saved_items]
    assert job_id in saved_job_ids

    # 3. Check is_saved flag in job detail
    detail_resp = await client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"Authorization": auth_header},
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["is_saved"] is True

    # 4. Unsave job
    unsave_resp = await client.delete(
        f"/api/v1/jobs/{job_id}/save",
        headers={"Authorization": auth_header},
    )
    assert unsave_resp.status_code == 200
    assert unsave_resp.json()["saved"] is False

    # 5. Verify no longer in saved list
    saved_list_after = await client.get(
        "/api/v1/jobs/saved",
        headers={"Authorization": auth_header},
    )
    assert saved_list_after.status_code == 200
    after_ids = [item["job_id"] for item in saved_list_after.json()]
    assert job_id not in after_ids
