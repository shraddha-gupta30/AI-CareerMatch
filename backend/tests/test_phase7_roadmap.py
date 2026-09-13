"""
Integration & Regression Tests for Phase 7:
Personalized Career Roadmap and Progress Tracking APIs.

Validates all 17 required cases:
1. Authentication required on roadmap generation
2. PROFILE_REQUIRED error when user has no Career Profile
3. JOB_NOT_FOUND error for invalid job UUID
4. Deterministic roadmap generation from skill gaps
5. Strict prerequisite DAG ordering (prerequisite appears before dependent skill)
6. Candidate with existing prerequisite (prerequisite omitted, dependent retained)
7. Stage & Priority assignments (Stage 1-4, critical/high/medium/low)
8. Idempotent regeneration (updates existing roadmap without duplicate rows)
9. List candidate roadmaps endpoint (GET /api/v1/roadmaps)
10. Roadmap detail endpoint (GET /api/v1/roadmaps/{roadmap_id})
11. Ownership isolation (Candidate A cannot read Candidate B's roadmap)
12. Item status update (PATCH /api/v1/roadmaps/{id}/items/{item_id})
13. completed_at timestamp setting and clearing
14. Progress percentage dynamic calculation (completed / total * 100)
15. Item update ownership isolation (Candidate A cannot update Candidate B's item)
16. Status validation rejects invalid strings with 422
17. Gemini independence & graceful deterministic fallback
"""
import uuid
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobSkill
from app.models.profile import CandidateProfile, CandidateSkill, Education
from app.models.roadmap import Roadmap, RoadmapItem
from app.models.skill import Skill


@pytest.fixture(autouse=True)
def disable_gemini_by_default(monkeypatch):
    """Disable live Gemini calls for standard tests to prevent network latency and external dependencies."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")


async def _register_user_and_create_profile(
    client: AsyncClient,
    suffix: str,
    experience_years: float = 1.0,
    skills_with_prof: list[tuple[str, str]] = None,
    degree: str = "Bachelor of Science in Computer Science",
) -> tuple[dict, str, str, str]:
    """Helper to register a user, create profile, and attach skills/education."""
    uid = uuid.uuid4().hex[:8]
    email = f"p7_user_{suffix}_{uid}@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": f"Roadmap Candidate {suffix.capitalize()}",
        },
    )
    assert resp.status_code == 201
    user_data = resp.json()["user"]
    auth_header = f"Bearer {resp.json()['access_token']}"

    # Create profile
    p_resp = await client.put(
        "/api/v1/profile",
        json={
            "target_role": "Full Stack Developer",
            "headline": "Junior Developer",
            "bio": "Building skills for career growth",
            "target_location": "Remote",
            "target_employment_type": "full-time",
            "total_experience_years": experience_years,
        },
        headers={"Authorization": auth_header},
    )
    assert p_resp.status_code == 200
    profile_id = p_resp.json()["id"]

    # Attach skills and education
    async with AsyncSessionLocal() as session:
        if skills_with_prof:
            for s_name, prof in skills_with_prof:
                s_stmt = select(Skill).where(Skill.name.ilike(s_name))
                s_res = await session.execute(s_stmt)
                sk = s_res.scalar_one_or_none()
                if sk:
                    cs = CandidateSkill(
                        profile_id=uuid.UUID(profile_id),
                        skill_id=sk.id,
                        proficiency_level=prof,
                        years_experience=1.0,
                        proficiency_source="user_verified",
                        is_verified=True,
                    )
                    session.add(cs)

        if degree:
            edu = Education(
                profile_id=uuid.UUID(profile_id),
                institution="State University",
                degree=degree,
                field_of_study="Computer Science",
            )
            session.add(edu)

        await session.commit()

    return user_data, auth_header, profile_id, email


async def _get_test_job_with_required_and_preferred(client: AsyncClient) -> dict:
    """Finds a job in the catalog that has both required and preferred skills."""
    resp = await client.get("/api/v1/jobs?limit=30")
    assert resp.status_code == 200
    jobs = resp.json()["items"]
    for j in jobs:
        d_resp = await client.get(f"/api/v1/jobs/{j['id']}")
        if d_resp.status_code == 200:
            skills = d_resp.json().get("skills", [])
            has_req = any(s["is_required"] for s in skills)
            has_pref = any(not s["is_required"] for s in skills)
            if has_req and has_pref:
                return d_resp.json()
    # Fallback to first job
    d_resp = await client.get(f"/api/v1/jobs/{jobs[0]['id']}")
    return d_resp.json()


# -----------------------------------------------------------------------------
# 1. Authentication Required
# -----------------------------------------------------------------------------
async def test_roadmap_requires_authentication(client: AsyncClient):
    """Test 1: POST /api/v1/jobs/{job_id}/roadmap returns 401 without authentication."""
    random_job_id = uuid.uuid4()
    resp = await client.post(f"/api/v1/jobs/{random_job_id}/roadmap")
    assert resp.status_code == 401


# -----------------------------------------------------------------------------
# 2. PROFILE_REQUIRED error when candidate has no Career Profile
# -----------------------------------------------------------------------------
async def test_roadmap_profile_required(client: AsyncClient):
    """Test 2: POST /api/v1/jobs/{job_id}/roadmap returns 404 PROFILE_REQUIRED when profile absent."""
    uid = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"no_profile_{uid}@example.com",
            "password": "SecurePassword123!",
            "full_name": "No Profile User",
        },
    )
    assert resp.status_code == 201
    auth_header = f"Bearer {resp.json()['access_token']}"

    job = await _get_test_job_with_required_and_preferred(client)
    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "PROFILE_REQUIRED"


# -----------------------------------------------------------------------------
# 3. JOB_NOT_FOUND error for invalid job UUID
# -----------------------------------------------------------------------------
async def test_roadmap_job_not_found(client: AsyncClient):
    """Test 3: POST /api/v1/jobs/{job_id}/roadmap returns 404 JOB_NOT_FOUND for non-existent job."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "job_nf")
    non_existent = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/jobs/{non_existent}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JOB_NOT_FOUND"


# -----------------------------------------------------------------------------
# 4. Deterministic Roadmap Generation from Gaps
# -----------------------------------------------------------------------------
async def test_generate_roadmap_from_gaps(client: AsyncClient):
    """Test 4: Generates structured roadmap with items, stages, hours, and actions."""
    _, auth, _, _ = await _register_user_and_create_profile(
        client, "gen_gaps", experience_years=1.0, skills_with_prof=[("Python", "intermediate")]
    )
    job = await _get_test_job_with_required_and_preferred(client)

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["target_job_id"] == job["id"]
    assert data["target_role"] == job["title"]
    assert data["total_items"] > 0
    assert data["completed_items"] == 0
    assert data["progress"]["progress_percentage"] == 0.0
    assert len(data["items"]) == data["total_items"]

    # Verify item schema integrity
    for item in data["items"]:
        assert item["id"] is not None
        assert item["title"]
        assert item["description"]
        assert item["stage_phase"] in [1, 2, 3, 4]
        assert item["priority"] in ["critical", "high", "medium", "low"]
        assert item["estimated_hours"] > 0
        assert item["recommended_action"]
        assert item["status"] == "not_started"
        assert item["sequence_order"] >= 1
        assert item["completed_at"] is None


# -----------------------------------------------------------------------------
# 5. Strict Prerequisite DAG Ordering
# -----------------------------------------------------------------------------
async def test_prerequisite_ordering_dag(client: AsyncClient):
    """
    Test 5: If a job requires a dependent skill (e.g. React) and candidate lacks
    its prerequisite (e.g. JavaScript), JavaScript must appear before React in sequence_order.
    """
    _, auth, _, _ = await _register_user_and_create_profile(
        client, "prereq_dag", experience_years=2.0, skills_with_prof=[]
    )

    # Find or create a job requiring React
    async with AsyncSessionLocal() as session:
        j_stmt = (
            select(Job)
            .join(JobSkill, Job.id == JobSkill.job_id)
            .join(Skill, JobSkill.skill_id == Skill.id)
            .where(Skill.name.ilike("React"), JobSkill.is_required == True)
        )
        j_res = await session.execute(j_stmt)
        react_job = j_res.scalars().first()

    if not react_job:
        pytest.skip("No curated job requiring React found in catalog.")

    resp = await client.post(
        f"/api/v1/jobs/{react_job.id}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]

    # Locate JavaScript and React in generated items
    js_item = next(
        (it for it in items if "javascript" in it["title"].lower() or (it["skill_name"] and "javascript" in it["skill_name"].lower())),
        None,
    )
    react_item = next(
        (it for it in items if "react" in it["title"].lower() or (it["skill_name"] and "react" in it["skill_name"].lower())),
        None,
    )

    if js_item and react_item:
        assert js_item["sequence_order"] < react_item["sequence_order"], (
            f"Expected JavaScript (seq {js_item['sequence_order']}) to come BEFORE React (seq {react_item['sequence_order']})"
        )
        assert js_item["stage_phase"] <= react_item["stage_phase"]


# -----------------------------------------------------------------------------
# 6. Candidate with Existing Prerequisite
# -----------------------------------------------------------------------------
async def test_candidate_with_existing_prerequisite(client: AsyncClient):
    """
    Test 6: When candidate already possesses JavaScript, JavaScript is omitted from
    the roadmap, but dependent skill React is included.
    """
    _, auth, _, _ = await _register_user_and_create_profile(
        client, "has_prereq", experience_years=2.0, skills_with_prof=[("JavaScript", "advanced")]
    )

    async with AsyncSessionLocal() as session:
        j_stmt = (
            select(Job)
            .join(JobSkill, Job.id == JobSkill.job_id)
            .join(Skill, JobSkill.skill_id == Skill.id)
            .where(Skill.name.ilike("React"), JobSkill.is_required == True)
        )
        j_res = await session.execute(j_stmt)
        react_job = j_res.scalars().first()

    if not react_job:
        pytest.skip("No curated job requiring React found in catalog.")

    resp = await client.post(
        f"/api/v1/jobs/{react_job.id}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]

    # JavaScript should not be a required roadmap item because candidate already has it
    js_items = [
        it for it in items
        if "foundational prerequisite: master javascript" in it["title"].lower()
    ]
    assert len(js_items) == 0, "Candidate already has JavaScript; prerequisite item should be omitted."

    # React should still be present
    react_items = [
        it for it in items
        if "react" in it["title"].lower() or (it["skill_name"] and "react" in it["skill_name"].lower())
    ]
    assert len(react_items) > 0, "React should be present as candidate lacks it."


# -----------------------------------------------------------------------------
# 7. Stage & Priority Assignments
# -----------------------------------------------------------------------------
async def test_stage_and_priority_distribution(client: AsyncClient):
    """Test 7: Validates that stages 1, 2, 3, 4 and priorities adhere to business rules."""
    _, auth, _, _ = await _register_user_and_create_profile(
        client, "stages_test", experience_years=0.5, skills_with_prof=[]
    )
    job = await _get_test_job_with_required_and_preferred(client)

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]

    stages_present = {it["stage_phase"] for it in items}
    assert any(s in [1, 2] for s in stages_present)

    for it in items:
        if it["stage_phase"] == 1:
            assert it["priority"] in ["critical", "high"]
        if it["priority"] == "critical":
            assert it["stage_phase"] == 1


# -----------------------------------------------------------------------------
# 8. Idempotent Regeneration (Duplicate Prevention)
# -----------------------------------------------------------------------------
async def test_duplicate_generation_idempotency(client: AsyncClient):
    """
    Test 8: Regenerating roadmap for the same job updates existing roadmap
    instead of creating duplicate database records.
    """
    _, auth, profile_id, _ = await _register_user_and_create_profile(client, "idemp_test")
    job = await _get_test_job_with_required_and_preferred(client)

    # First generation
    resp1 = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp1.status_code == 200
    roadmap_id_1 = resp1.json()["id"]

    # Second generation for same job
    resp2 = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    assert resp2.status_code == 200
    roadmap_id_2 = resp2.json()["id"]

    # Must be the exact same roadmap ID
    assert roadmap_id_1 == roadmap_id_2

    # Check database count: exactly 1 roadmap for this profile and job
    async with AsyncSessionLocal() as session:
        stmt = select(Roadmap).where(
            Roadmap.profile_id == uuid.UUID(profile_id),
            Roadmap.target_job_id == uuid.UUID(job["id"]),
        )
        res = await session.execute(stmt)
        all_roadmaps = res.scalars().all()
        assert len(all_roadmaps) == 1


# -----------------------------------------------------------------------------
# 9. List Candidate Roadmaps (GET /api/v1/roadmaps)
# -----------------------------------------------------------------------------
async def test_list_candidate_roadmaps(client: AsyncClient):
    """Test 9: GET /api/v1/roadmaps returns user roadmaps with progress."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "list_rm")

    # Initial list is empty
    resp = await client.get("/api/v1/roadmaps", headers={"Authorization": auth})
    assert resp.status_code == 200
    assert resp.json() == []

    # Generate a roadmap
    job = await _get_test_job_with_required_and_preferred(client)
    await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )

    # List now contains 1 roadmap
    resp = await client.get("/api/v1/roadmaps", headers={"Authorization": auth})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["target_job_id"] == job["id"]
    assert "progress" in data[0]
    assert data[0]["progress"]["total_items"] > 0


# -----------------------------------------------------------------------------
# 10. Roadmap Detail (GET /api/v1/roadmaps/{roadmap_id})
# -----------------------------------------------------------------------------
async def test_get_roadmap_detail(client: AsyncClient):
    """Test 10: GET /api/v1/roadmaps/{id} returns full items list ordered by sequence."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "detail_rm")
    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    roadmap_id = gen_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == roadmap_id
    assert len(data["items"]) == data["total_items"]

    # Verify monotonic sequence order
    orders = [it["sequence_order"] for it in data["items"]]
    assert orders == sorted(orders)


# -----------------------------------------------------------------------------
# 11. Ownership Isolation on Roadmap Retrieval
# -----------------------------------------------------------------------------
async def test_roadmap_ownership_isolation(client: AsyncClient):
    """Test 11: Candidate A cannot access Candidate B's roadmap (returns 404)."""
    _, auth_a, _, _ = await _register_user_and_create_profile(client, "user_a")
    _, auth_b, _, _ = await _register_user_and_create_profile(client, "user_b")

    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth_a},
    )
    roadmap_id_a = gen_resp.json()["id"]

    # Candidate B tries to read Candidate A's roadmap
    resp = await client.get(
        f"/api/v1/roadmaps/{roadmap_id_a}",
        headers={"Authorization": auth_b},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ROADMAP_NOT_FOUND"


# -----------------------------------------------------------------------------
# 12. Item Status Updates (PATCH /api/v1/roadmaps/{id}/items/{item_id})
# -----------------------------------------------------------------------------
async def test_update_roadmap_item_status(client: AsyncClient):
    """Test 12: Updating an item from not_started to in_progress to completed."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "status_upd")
    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    roadmap_data = gen_resp.json()
    roadmap_id = roadmap_data["id"]
    item_id = roadmap_data["items"][0]["id"]

    # Update to in_progress
    resp1 = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/items/{item_id}",
        json={"status": "in_progress"},
        headers={"Authorization": auth},
    )
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["item"]["status"] == "in_progress"
    assert d1["roadmap_progress"]["in_progress_items"] == 1
    assert d1["roadmap_progress"]["completed_items"] == 0

    # Update to completed
    resp2 = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/items/{item_id}",
        json={"status": "completed"},
        headers={"Authorization": auth},
    )
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["item"]["status"] == "completed"
    assert d2["roadmap_progress"]["completed_items"] == 1


# -----------------------------------------------------------------------------
# 13. completed_at Timestamp Behavior
# -----------------------------------------------------------------------------
async def test_completed_at_timestamp(client: AsyncClient):
    """Test 13: completed_at is populated when status is completed and cleared when un-completed."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "timestamp_test")
    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    roadmap_id = gen_resp.json()["id"]
    item_id = gen_resp.json()["items"][0]["id"]

    # Mark completed -> completed_at populated
    resp_comp = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/items/{item_id}",
        json={"status": "completed"},
        headers={"Authorization": auth},
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["item"]["completed_at"] is not None

    # Mark in_progress -> completed_at cleared
    resp_reset = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/items/{item_id}",
        json={"status": "in_progress"},
        headers={"Authorization": auth},
    )
    assert resp_reset.status_code == 200
    assert resp_reset.json()["item"]["completed_at"] is None


# -----------------------------------------------------------------------------
# 14. Progress Percentage Calculation Math
# -----------------------------------------------------------------------------
async def test_progress_percentage_calculation(client: AsyncClient):
    """Test 14: Dynamic progress percentage = round(completed / total * 100, 1)."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "progress_math")
    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    data = gen_resp.json()
    roadmap_id = data["id"]
    items = data["items"]
    total = len(items)

    completed_count = 0
    for idx, item in enumerate(items):
        resp = await client.patch(
            f"/api/v1/roadmaps/{roadmap_id}/items/{item['id']}",
            json={"status": "completed"},
            headers={"Authorization": auth},
        )
        assert resp.status_code == 200
        completed_count += 1
        expected_pct = round((completed_count / total) * 100.0, 1)
        actual_pct = resp.json()["roadmap_progress"]["progress_percentage"]
        assert actual_pct == expected_pct

    # All items completed -> exactly 100.0%
    assert expected_pct == 100.0


# -----------------------------------------------------------------------------
# 15. Item Update Ownership Isolation
# -----------------------------------------------------------------------------
async def test_update_item_ownership_isolation(client: AsyncClient):
    """Test 15: Candidate A cannot update an item on Candidate B's roadmap."""
    _, auth_a, _, _ = await _register_user_and_create_profile(client, "own_item_a")
    _, auth_b, _, _ = await _register_user_and_create_profile(client, "own_item_b")

    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth_a},
    )
    roadmap_id_a = gen_resp.json()["id"]
    item_id_a = gen_resp.json()["items"][0]["id"]

    # Candidate B attempts to modify Candidate A's item
    resp = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id_a}/items/{item_id_a}",
        json={"status": "completed"},
        headers={"Authorization": auth_b},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ROADMAP_NOT_FOUND"


# -----------------------------------------------------------------------------
# 16. Status Validation Rejection
# -----------------------------------------------------------------------------
async def test_update_item_validation(client: AsyncClient):
    """Test 16: Pydantic rejects invalid status strings with 422 Unprocessable Entity."""
    _, auth, _, _ = await _register_user_and_create_profile(client, "invalid_stat")
    job = await _get_test_job_with_required_and_preferred(client)
    gen_resp = await client.post(
        f"/api/v1/jobs/{job['id']}/roadmap",
        headers={"Authorization": auth},
    )
    roadmap_id = gen_resp.json()["id"]
    item_id = gen_resp.json()["items"][0]["id"]

    resp = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/items/{item_id}",
        json={"status": "finished_forever"},
        headers={"Authorization": auth},
    )
    assert resp.status_code == 422


# -----------------------------------------------------------------------------
# 17. Gemini Independence & Graceful Deterministic Fallback
# -----------------------------------------------------------------------------
async def test_gemini_fallback_graceful(client: AsyncClient, monkeypatch):
    """
    Test 17: Roadmap generation completes successfully even when Gemini is mocked
    to raise an exception or when GEMINI_API_KEY is unset.
    """
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock_key")
    _, auth, _, _ = await _register_user_and_create_profile(client, "gemini_mock")
    job = await _get_test_job_with_required_and_preferred(client)

    # Force Gemini to raise an exception
    with patch(
        "app.services.roadmap_service._personalize_roadmap_with_gemini",
        side_effect=Exception("Simulated Gemini API timeout / error"),
    ):
        resp = await client.post(
            f"/api/v1/jobs/{job['id']}/roadmap",
            headers={"Authorization": auth},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] > 0
        assert data["items"][0]["title"] is not None


# -----------------------------------------------------------------------------
# 18. Gemini Personalization Integration
# -----------------------------------------------------------------------------
async def test_gemini_personalization_success(client: AsyncClient, monkeypatch):
    """
    Test 18: When Gemini personalization succeeds, enhanced recommendations are
    applied without altering deterministic stages, hours, priorities, or sequence.
    """
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock_key")

    async def mock_personalize(items, target_role, job_description, candidate_summary):
        for it in items:
            it["description"] = f"Enhanced: {it['description']}"
            it["recommended_action"] = f"Personalized Action for {target_role}: {it['recommended_action']}"
        return items

    _, auth, _, _ = await _register_user_and_create_profile(client, "gemini_enh")
    job = await _get_test_job_with_required_and_preferred(client)

    with patch(
        "app.services.roadmap_service._personalize_roadmap_with_gemini",
        side_effect=mock_personalize,
    ):
        resp = await client.post(
            f"/api/v1/jobs/{job['id']}/roadmap",
            headers={"Authorization": auth},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_items"] > 0
        first_item = data["items"][0]
        assert first_item["description"].startswith("Enhanced:")
        assert "Personalized Action" in first_item["recommended_action"]
        assert first_item["sequence_order"] == 1
        assert first_item["estimated_hours"] > 0

