"""
Integration and Unit Tests for Authentication: Registration, Login, and Current User.
"""
import uuid
import pytest
from httpx import AsyncClient
from app.core.security import decode_access_token, hash_password, verify_password


def test_password_hashing_security():
    """Verify bcrypt hashes passwords, salts them uniquely, and verifies accurately."""
    pwd = "SuperSecretPassword123!"
    hashed = hash_password(pwd)

    # Password must never match plaintext
    assert hashed != pwd
    assert hashed.startswith("$2b$")
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False

    # Two hashes of the same password must differ (salt uniqueness)
    second_hash = hash_password(pwd)
    assert hashed != second_hash
    assert verify_password(pwd, second_hash) is True


async def test_successful_registration(client: AsyncClient):
    """Verify user registration returns 201, valid JWT, and safe user payload without password hash."""
    uid = uuid.uuid4().hex[:8]
    email = f"user_{uid}@example.com"
    payload = {
        "email": email,
        "password": "ValidPassword999!",
        "full_name": "Ada Lovelace",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert data["expires_in"] > 0

    user = data["user"]
    assert user["email"] == email.lower()
    assert user["full_name"] == "Ada Lovelace"
    assert user["is_active"] is True
    assert "id" in user
    # Critical security invariant: password hash must NEVER be exposed
    assert "hashed_password" not in user
    assert "password" not in user

    # Verify JWT validity
    token_claims = decode_access_token(data["access_token"])
    assert token_claims["sub"] == user["id"]
    assert token_claims["email"] == email.lower()


async def test_duplicate_email_rejection(client: AsyncClient):
    """Verify registration with already registered email returns 409 Conflict."""
    uid = uuid.uuid4().hex[:8]
    email = f"dup_{uid}@example.com"
    payload = {
        "email": email,
        "password": "ValidPassword999!",
        "full_name": "Charles Babbage",
    }

    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second attempt with same email
    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    err = resp2.json()["error"]
    assert err["code"] == "USER_ALREADY_EXISTS"


async def test_successful_login(client: AsyncClient):
    """Verify login with correct credentials returns 200 and access token."""
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@example.com"
    password = "MySecurePassword123!"

    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Grace Hopper"},
    )
    assert reg_resp.status_code == 201

    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email.upper(), "password": password},  # Case-insensitive email
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == email.lower()


async def test_invalid_password_rejection(client: AsyncClient):
    """Verify login with incorrect password returns 401 Unauthorized."""
    uid = uuid.uuid4().hex[:8]
    email = f"badpass_{uid}@example.com"

    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "CorrectPassword123!", "full_name": "Alan Turing"},
    )
    assert reg_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "IncorrectPassword456!"},
    )
    assert login_resp.status_code == 401
    assert "WWW-Authenticate" in login_resp.headers


async def test_jwt_me_endpoint_valid_token(client: AsyncClient):
    """Verify GET /api/v1/auth/me returns current user profile when valid token provided."""
    uid = uuid.uuid4().hex[:8]
    email = f"me_{uid}@example.com"

    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Katherine Johnson"},
    )
    token = reg_resp.json()["access_token"]

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    user = me_resp.json()
    assert user["email"] == email.lower()
    assert user["full_name"] == "Katherine Johnson"


async def test_jwt_missing_and_invalid_token(client: AsyncClient):
    """Verify endpoints reject missing, invalid, or malformed tokens with 401."""
    # Missing token
    resp_no_token = await client.get("/api/v1/auth/me")
    assert resp_no_token.status_code == 401
    assert resp_no_token.headers.get("WWW-Authenticate") == "Bearer"

    # Malformed token
    resp_malformed = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"},
    )
    assert resp_malformed.status_code == 401
    assert resp_malformed.headers.get("WWW-Authenticate") == "Bearer"
