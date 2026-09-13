"""
Integration Tests for Candidate Career Profile: Retrieval, Upsert, and User Isolation.
"""
import uuid
import pytest
from httpx import AsyncClient


async def _register_user(client: AsyncClient, name_suffix: str) -> tuple[dict, str]:
    """Helper to register a user and return (user_data, auth_header)."""
    uid = uuid.uuid4().hex[:8]
    email = f"candidate_{name_suffix}_{uid}@example.com"
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
    token = data["access_token"]
    return data["user"], f"Bearer {token}"


async def test_empty_profile_retrieval(client: AsyncClient):
    """Verify newly registered user receives null profile before setup."""
    user, auth_header = await _register_user(client, "newbie")

    resp = await client.get("/api/v1/profile", headers={"Authorization": auth_header})
    assert resp.status_code == 200
    assert resp.json() is None


async def test_profile_creation_upsert(client: AsyncClient):
    """Verify candidate can create their initial career profile."""
    user, auth_header = await _register_user(client, "creator")

    profile_data = {
        "target_role": "Backend Cloud Engineer",
        "headline": "Python & Distributed Systems Enthusiast",
        "bio": "Specialized in high-throughput API architectures and relational data modeling.",
        "target_location": "Remote, Global",
        "target_employment_type": "Full-time",
        "total_experience_years": 3.5,
    }

    resp = await client.put(
        "/api/v1/profile",
        json=profile_data,
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["target_role"] == "Backend Cloud Engineer"
    assert data["headline"] == "Python & Distributed Systems Enthusiast"
    assert data["total_experience_years"] == 3.5
    assert data["user_id"] == user["id"]
    assert "id" in data


async def test_profile_update(client: AsyncClient):
    """Verify candidate can update their existing career profile."""
    user, auth_header = await _register_user(client, "updater")

    # Initial creation
    await client.put(
        "/api/v1/profile",
        json={"target_role": "Junior Analyst", "total_experience_years": 1.0},
        headers={"Authorization": auth_header},
    )

    # Subsequent update
    updated_payload = {
        "target_role": "Senior Data Scientist",
        "headline": "AI & ML Specialist",
        "bio": "Deep learning and statistical analysis background.",
        "target_location": "Bengaluru, India",
        "target_employment_type": "Full-time",
        "total_experience_years": 5.0,
    }
    resp = await client.put(
        "/api/v1/profile",
        json=updated_payload,
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["target_role"] == "Senior Data Scientist"
    assert data["headline"] == "AI & ML Specialist"
    assert data["total_experience_years"] == 5.0

    # Verify retrieval returns the updated data
    get_resp = await client.get("/api/v1/profile", headers={"Authorization": auth_header})
    assert get_resp.status_code == 200
    assert get_resp.json()["target_role"] == "Senior Data Scientist"


async def test_profile_user_isolation(client: AsyncClient):
    """
    CRITICAL SECURITY TEST:
    Verify User A and User B cannot see or overwrite each other's career profile.
    """
    user_a, auth_a = await _register_user(client, "alice")
    user_b, auth_b = await _register_user(client, "bob")

    # User A creates profile
    resp_a = await client.put(
        "/api/v1/profile",
        json={
            "target_role": "DevOps Architect",
            "headline": "Alice's Headline",
            "total_experience_years": 7.0,
        },
        headers={"Authorization": auth_a},
    )
    assert resp_a.status_code == 200

    # User B creates distinct profile
    resp_b = await client.put(
        "/api/v1/profile",
        json={
            "target_role": "Frontend Developer",
            "headline": "Bob's Headline",
            "total_experience_years": 2.0,
        },
        headers={"Authorization": auth_b},
    )
    assert resp_b.status_code == 200

    # User A reads profile -> receives Alice's data only
    read_a = (await client.get("/api/v1/profile", headers={"Authorization": auth_a})).json()
    assert read_a["target_role"] == "DevOps Architect"
    assert read_a["headline"] == "Alice's Headline"
    assert read_a["user_id"] == user_a["id"]

    # User B reads profile -> receives Bob's data only
    read_b = (await client.get("/api/v1/profile", headers={"Authorization": auth_b})).json()
    assert read_b["target_role"] == "Frontend Developer"
    assert read_b["headline"] == "Bob's Headline"
    assert read_b["user_id"] == user_b["id"]


async def test_profile_validation_negative_experience(client: AsyncClient):
    """Verify negative experience years is rejected by Pydantic schema validation."""
    user, auth_header = await _register_user(client, "negval")

    resp = await client.put(
        "/api/v1/profile",
        json={"target_role": "Developer", "total_experience_years": -2.0},
        headers={"Authorization": auth_header},
    )
    assert resp.status_code == 422
