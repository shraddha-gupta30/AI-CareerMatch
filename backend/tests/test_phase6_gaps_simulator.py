"""
Integration & Regression Tests for Phase 6A:
Skill Gap Analysis and What-If Career Simulator APIs.
Validates all 14 required cases:
1. Gap endpoint with valid profile
2. Missing required skill detection
3. Partial skill credit via explicit skill relationships
4. Missing preferred skill detection
5. Experience gap calculation & text
6. Education compatibility evaluation
7. PROFILE_REQUIRED error for unprofiled users
8. JOB_NOT_FOUND error for invalid job UUID
9. Simulator with added skill
10. Simulator with changed proficiency
11. Simulator with changed experience
12. Simulator score strictly matches calculate_job_match()
13. Simulator strictly does NOT persist any database mutations
14. Simulator rejects invalid inputs (negative experience, invalid proficiency, empty name)
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.job import Job, JobSkill
from app.models.profile import CandidateProfile, CandidateSkill, Education
from app.models.skill import Skill
from app.services.matching_engine import calculate_job_match
from app.api.v1.endpoints.jobs import _get_skill_taxonomy_maps


async def _register_user_and_create_profile(
    client: AsyncClient,
    suffix: str,
    experience_years: float = 1.0,
    skills_with_prof: list[tuple[str, str]] = None,
    degree: str = "Bachelor of Science in Computer Science",
) -> tuple[dict, str, str, str]:
    """Helper to register a user, create profile, and attach skills/education."""
    uid = uuid.uuid4().hex[:8]
    email = f"p6_user_{suffix}_{uid}@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": f"Candidate {suffix.capitalize()}",
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
            "bio": "Passionate developer",
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
                # Find skill in DB
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
    resp = await client.get("/api/v1/jobs?limit=20")
    assert resp.status_code == 200
    jobs = resp.json()["items"]
    for j in jobs:
        # Check detail
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
# 1. Gap endpoint with valid profile
# -----------------------------------------------------------------------------
async def test_gaps_endpoint_with_valid_profile(client: AsyncClient):
    """Test 1: Verify GET /api/v1/jobs/{job_id}/gaps returns complete structured gap breakdown."""
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "gap_valid", experience_years=2.0, skills_with_prof=[("Python", "advanced")]
    )
    job = await _get_test_job_with_required_and_preferred(client)
    job_id = job["id"]

    resp = await client.get(
        f"/api/v1/jobs/{job_id}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["job_id"] == job_id
    assert 0.0 <= data["overall_score"] <= 100.0
    assert 0.0 <= data["required_skills_score"] <= 100.0
    assert 0.0 <= data["experience_score"] <= 100.0
    assert 0.0 <= data["education_score"] <= 100.0

    # Collections
    assert isinstance(data["matched_required_skills"], list)
    assert isinstance(data["partial_required_skills"], list)
    assert isinstance(data["missing_required_skills"], list)
    assert isinstance(data["matched_preferred_skills"], list)
    assert isinstance(data["partial_preferred_skills"], list)
    assert isinstance(data["missing_preferred_skills"], list)

    # Sub-objects
    assert "experience_gap" in data
    assert "candidate_experience_years" in data["experience_gap"]
    assert "job_min_experience_years" in data["experience_gap"]
    assert "education_compatibility" in data
    assert "explanation" in data


# -----------------------------------------------------------------------------
# 2. Missing required skill detection
# -----------------------------------------------------------------------------
async def test_gaps_missing_required_skill(client: AsyncClient):
    """Test 2: Verify missing required skills are properly identified in missing_required_skills."""
    # Profile with no skills at all
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "gap_noskill", experience_years=2.0, skills_with_prof=[]
    )
    job = await _get_test_job_with_required_and_preferred(client)
    job_id = job["id"]

    resp = await client.get(
        f"/api/v1/jobs/{job_id}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Any required skill in job must appear in missing_required_skills
    req_job_skills = [s for s in job["skills"] if s["is_required"]]
    if req_job_skills:
        assert len(data["missing_required_skills"]) >= 1
        missing_names = [m["name"].lower() for m in data["missing_required_skills"]]
        for rjs in req_job_skills:
            assert rjs["name"].lower() in missing_names
        # Check structure of missing items
        first_missing = data["missing_required_skills"][0]
        assert "name" in first_missing
        assert "required_proficiency" in first_missing
        assert "importance_weight" in first_missing
        assert first_missing["is_required"] is True


# -----------------------------------------------------------------------------
# 3. Partial skill credit via explicit skill relationships
# -----------------------------------------------------------------------------
async def test_gaps_partial_skill_relationship(client: AsyncClient):
    """Test 3: Verify candidate with related skill receives partial credit governed by relationships."""
    # Find a job requiring TypeScript or React or Python
    list_resp = await client.get("/api/v1/jobs?limit=30")
    jobs = list_resp.json()["items"]
    target_job = None

    for j in jobs:
        d_resp = await client.get(f"/api/v1/jobs/{j['id']}")
        j_skills = d_resp.json().get("skills", [])
        # Look for job requiring TypeScript or React
        if any(s["name"] == "TypeScript" and s["is_required"] for s in j_skills):
            target_job = d_resp.json()
            cand_skill = "JavaScript"  # JavaScript -> TypeScript has 0.75 weight
            break
        if any(s["name"] == "React" and s["is_required"] for s in j_skills):
            target_job = d_resp.json()
            cand_skill = "Vue.js"  # Vue.js -> React has 0.60 weight
            break

    if not target_job:
        target_job = jobs[0]
        cand_skill = "JavaScript"

    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "gap_partial", experience_years=2.0, skills_with_prof=[(cand_skill, "advanced")]
    )

    resp = await client.get(
        f"/api/v1/jobs/{target_job['id']}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    # If target job has TypeScript/React, we should see partial credit in partial_required_skills
    all_partials = data["partial_required_skills"] + data["partial_preferred_skills"]
    if all_partials:
        first_partial = all_partials[0]
        assert first_partial["similarity_weight"] > 0.0
        assert "job_skill_name" in first_partial
        assert "candidate_skill_name" in first_partial
        assert first_partial["candidate_skill_name"].lower() == cand_skill.lower()
        assert first_partial["credit"] > 0.0


# -----------------------------------------------------------------------------
# 4. Missing preferred skill detection
# -----------------------------------------------------------------------------
async def test_gaps_missing_preferred_skill(client: AsyncClient):
    """Test 4: Verify preferred skills that candidate lacks appear in missing_preferred_skills."""
    job = await _get_test_job_with_required_and_preferred(client)
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "gap_pref", experience_years=2.0, skills_with_prof=[]
    )

    resp = await client.get(
        f"/api/v1/jobs/{job['id']}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    pref_job_skills = [s for s in job["skills"] if not s["is_required"]]
    if pref_job_skills:
        assert len(data["missing_preferred_skills"]) >= 1
        missing_pref_names = [m["name"].lower() for m in data["missing_preferred_skills"]]
        for pjs in pref_job_skills:
            assert pjs["name"].lower() in missing_pref_names
        assert data["missing_preferred_skills"][0]["is_required"] is False


# -----------------------------------------------------------------------------
# 5. Experience gap calculation & text
# -----------------------------------------------------------------------------
async def test_gaps_experience_gap_calculation(client: AsyncClient):
    """Test 5: Verify experience gap accurately calculates deficit, surplus, and text."""
    # Find a job requiring >= 3 years
    list_resp = await client.get("/api/v1/jobs?limit=20")
    job = next((j for j in list_resp.json()["items"] if j["min_experience_years"] >= 2.0), list_resp.json()["items"][0])

    # Candidate with 1.0 yr experience
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "gap_exp", experience_years=1.0, skills_with_prof=[]
    )

    resp = await client.get(
        f"/api/v1/jobs/{job['id']}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    exp_gap = resp.json()["experience_gap"]

    assert exp_gap["candidate_experience_years"] == 1.0
    assert exp_gap["job_min_experience_years"] == job["min_experience_years"]

    if job["min_experience_years"] > 1.0:
        expected_deficit = round(job["min_experience_years"] - 1.0, 1)
        assert exp_gap["experience_gap"] == expected_deficit
        assert "below requirement" in exp_gap["experience_gap_text"].lower()
        assert exp_gap["experience_score"] < 100.0


# -----------------------------------------------------------------------------
# 6. Education compatibility evaluation
# -----------------------------------------------------------------------------
async def test_gaps_education_compatibility(client: AsyncClient):
    """Test 6: Verify candidate education degree matches or reports tier difference."""
    job = await _get_test_job_with_required_and_preferred(client)
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "gap_edu", experience_years=2.0, degree="Bachelor of Technology in Information Technology"
    )

    resp = await client.get(
        f"/api/v1/jobs/{job['id']}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    edu_comp = resp.json()["education_compatibility"]

    assert edu_comp["candidate_highest_level"] == "Bachelor"
    assert "required_level" in edu_comp
    assert isinstance(edu_comp["meets_requirement"], bool)
    assert edu_comp["score"] >= 0.0
    assert len(edu_comp["explanation"]) > 5


# -----------------------------------------------------------------------------
# 7. PROFILE_REQUIRED error for unprofiled users
# -----------------------------------------------------------------------------
async def test_gaps_without_profile_returns_404(client: AsyncClient):
    """Test 7: Unprofiled candidate calling gaps returns 404 PROFILE_REQUIRED."""
    uid = uuid.uuid4().hex[:8]
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"unprofiled_gap_{uid}@example.com",
            "password": "SecurePassword123!",
            "full_name": "No Profile Gap",
        },
    )
    token = resp.json()["access_token"]
    list_resp = await client.get("/api/v1/jobs?limit=1")
    job_id = list_resp.json()["items"][0]["id"]

    gap_resp = await client.get(
        f"/api/v1/jobs/{job_id}/gaps",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gap_resp.status_code == 404
    assert gap_resp.json()["error"]["code"] == "PROFILE_REQUIRED"


# -----------------------------------------------------------------------------
# 8. JOB_NOT_FOUND error for invalid job UUID
# -----------------------------------------------------------------------------
async def test_gaps_invalid_job_returns_404(client: AsyncClient):
    """Test 8: Invalid job UUID returns 404 JOB_NOT_FOUND."""
    user, auth, _, _ = await _register_user_and_create_profile(client, "gap_fakejob")
    fake_id = uuid.uuid4()

    resp = await client.get(
        f"/api/v1/jobs/{fake_id}/gaps",
        headers={"Authorization": auth},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "JOB_NOT_FOUND"


# -----------------------------------------------------------------------------
# 9. Simulator with added skill
# -----------------------------------------------------------------------------
async def test_simulator_with_added_skill(client: AsyncClient):
    """Test 9: Adding a required skill increases score and explains factor."""
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "sim_add", experience_years=3.0, skills_with_prof=[]
    )
    job = await _get_test_job_with_required_and_preferred(client)
    req_skills = [s for s in job["skills"] if s["is_required"]]
    target_skill_name = req_skills[0]["name"] if req_skills else "Python"

    sim_payload = {
        "add_skills": [
            {"name": target_skill_name, "proficiency_level": "advanced"}
        ]
    }

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/simulate",
        json=sim_payload,
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["job_id"] == job["id"]
    assert data["simulated_score"] >= data["current_score"]
    assert data["score_delta"] >= 0.0
    assert len(data["changed_factors"]) >= 1
    # Check factor mentions added skill
    factors_text = " ".join(data["changed_factors"]).lower()
    assert target_skill_name.lower() in factors_text
    assert "added skill" in factors_text


# -----------------------------------------------------------------------------
# 10. Simulator with changed proficiency
# -----------------------------------------------------------------------------
async def test_simulator_with_changed_proficiency(client: AsyncClient):
    """Test 10: Upgrading skill proficiency from beginner to expert reflects in score/factors."""
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "sim_prof", experience_years=3.0, skills_with_prof=[("Python", "beginner")]
    )
    job = await _get_test_job_with_required_and_preferred(client)

    sim_payload = {
        "modify_skills": [
            {"name": "Python", "proficiency_level": "expert"}
        ]
    }

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/simulate",
        json=sim_payload,
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    factors_text = " ".join(data["changed_factors"]).lower()
    assert "modified skill 'python'" in factors_text
    assert "expert" in factors_text


# -----------------------------------------------------------------------------
# 11. Simulator with changed experience
# -----------------------------------------------------------------------------
async def test_simulator_with_changed_experience(client: AsyncClient):
    """Test 11: Adjusting experience years closes experience gap in simulator."""
    list_resp = await client.get("/api/v1/jobs?limit=20")
    job = next((j for j in list_resp.json()["items"] if j["min_experience_years"] >= 3.0), list_resp.json()["items"][0])

    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "sim_exp", experience_years=1.0, skills_with_prof=[]
    )

    sim_payload = {
        "experience_years": 5.0
    }

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/simulate",
        json=sim_payload,
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["simulated_match"]["experience_score"] == 100.0
    assert data["simulated_match"]["experience_gap"] == 0.0
    assert data["simulated_score"] >= data["current_score"]

    factors_text = " ".join(data["changed_factors"]).lower()
    assert "adjusted experience from 1.0 to 5.0 yrs" in factors_text


# -----------------------------------------------------------------------------
# 12. Simulator score matches calculate_job_match() directly
# -----------------------------------------------------------------------------
async def test_simulator_score_matches_calculate_job_match(client: AsyncClient):
    """Test 12: Verify simulator score exactly equals direct calculate_job_match() calculation."""
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "sim_direct", experience_years=2.0, skills_with_prof=[("Python", "intermediate")]
    )
    job = await _get_test_job_with_required_and_preferred(client)

    sim_payload = {
        "add_skills": [{"name": "Docker", "proficiency_level": "advanced"}],
        "experience_years": 4.0,
    }

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/simulate",
        json=sim_payload,
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Verify direct engine evaluation with same simulated parameters
    async with AsyncSessionLocal() as session:
        rel_map, alias_map = await _get_skill_taxonomy_maps(session)
        j_stmt = (
            select(Job)
            .where(Job.id == uuid.UUID(job["id"]))
            .options(selectinload(Job.job_skills).selectinload(JobSkill.skill))
        )
        j_res = await session.execute(j_stmt)
        job_orm = j_res.scalar_one()

        prof_stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.id == uuid.UUID(profile_id))
            .options(
                selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill),
                selectinload(CandidateProfile.education),
            )
        )
        p_res = await session.execute(prof_stmt)
        prof_orm = p_res.scalar_one()

        # Direct baseline
        base_direct = calculate_job_match(prof_orm, job_orm, rel_map, alias_map)
        assert base_direct.overall_score == data["current_score"]

        # Direct simulated profile
        class DirectSimProfile:
            def __init__(self):
                self.skills = [
                    {"name": "Python", "proficiency_level": "intermediate", "proficiency_source": "user_verified"},
                    {"name": "Docker", "proficiency_level": "advanced", "proficiency_source": "user_verified"},
                ]
                self.total_experience_years = 4.0
                self.education = prof_orm.education

        sim_direct = calculate_job_match(DirectSimProfile(), job_orm, rel_map, alias_map)
        assert sim_direct.overall_score == data["simulated_score"]
        assert round(sim_direct.overall_score - base_direct.overall_score, 2) == data["score_delta"]


# -----------------------------------------------------------------------------
# 13. Simulator strictly does NOT persist changes to DB
# -----------------------------------------------------------------------------
async def test_simulator_does_not_persist_changes_to_db(client: AsyncClient):
    """Test 13: Verify DB candidate_skills, profile experience, etc. remain unchanged after simulate call."""
    user, auth, profile_id, _ = await _register_user_and_create_profile(
        client, "sim_nopersist", experience_years=1.5, skills_with_prof=[("Python", "intermediate")]
    )
    job = await _get_test_job_with_required_and_preferred(client)

    # Initial DB verification
    async with AsyncSessionLocal() as session:
        p_stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.id == uuid.UUID(profile_id))
            .options(selectinload(CandidateProfile.skills))
        )
        p_res = await session.execute(p_stmt)
        initial_profile = p_res.scalar_one()
        assert float(initial_profile.total_experience_years) == 1.5
        assert len(initial_profile.skills) == 1

    # Run heavy simulation: add skills, remove skills, change experience
    sim_payload = {
        "add_skills": [
            {"name": "Kubernetes", "proficiency_level": "expert"},
            {"name": "AWS", "proficiency_level": "advanced"},
        ],
        "remove_skills": ["Python"],
        "experience_years": 10.0,
    }

    resp = await client.post(
        f"/api/v1/jobs/{job['id']}/simulate",
        json=sim_payload,
        headers={"Authorization": auth},
    )
    assert resp.status_code == 200

    # Post-simulation DB verification: strictly unchanged
    async with AsyncSessionLocal() as session:
        p_stmt = (
            select(CandidateProfile)
            .where(CandidateProfile.id == uuid.UUID(profile_id))
            .options(selectinload(CandidateProfile.skills))
        )
        p_res = await session.execute(p_stmt)
        post_profile = p_res.scalar_one()
        assert float(post_profile.total_experience_years) == 1.5
        assert len(post_profile.skills) == 1
        assert post_profile.skills[0].proficiency_level == "intermediate"


# -----------------------------------------------------------------------------
# 14. Simulator rejects invalid inputs
# -----------------------------------------------------------------------------
async def test_simulator_rejects_invalid_inputs(client: AsyncClient):
    """Test 14: Simulator rejects negative experience, invalid proficiency, and blank skill names."""
    user, auth, profile_id, _ = await _register_user_and_create_profile(client, "sim_invalid")
    job = await _get_test_job_with_required_and_preferred(client)
    job_id = job["id"]

    # 1. Negative experience
    resp1 = await client.post(
        f"/api/v1/jobs/{job_id}/simulate",
        json={"experience_years": -3.0},
        headers={"Authorization": auth},
    )
    assert resp1.status_code == 422

    # 2. Invalid proficiency level
    resp2 = await client.post(
        f"/api/v1/jobs/{job_id}/simulate",
        json={"add_skills": [{"name": "Go", "proficiency_level": "wizard"}]},
        headers={"Authorization": auth},
    )
    assert resp2.status_code == 422

    # 3. Empty skill name
    resp3 = await client.post(
        f"/api/v1/jobs/{job_id}/simulate",
        json={"add_skills": [{"name": "   ", "proficiency_level": "advanced"}]},
        headers={"Authorization": auth},
    )
    assert resp3.status_code == 422
