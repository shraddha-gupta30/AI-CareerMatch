"""
Common API Dependencies: Authentication and Authorization.
"""
import uuid
from typing import Optional
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates the Bearer JWT token from the Authorization header and resolves
    the authenticated user from the database.
    
    Handles:
    - Missing token (HTTP 401)
    - Malformed or invalid token (HTTP 401)
    - Expired token (HTTP 401)
    - Nonexistent or deactivated user (HTTP 401)
    """
    if not auth_credentials or not auth_credentials.credentials:
        raise AuthenticationError(
            message="Authorization credentials were not provided. Expected 'Bearer <token>'.",
            code="TOKEN_MISSING",
        )

    token = auth_credentials.credentials
    payload = decode_access_token(token)

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise AuthenticationError(
            message="Token payload is missing user identification.",
            code="TOKEN_MALFORMED",
        )

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except (ValueError, TypeError):
        raise AuthenticationError(
            message="Token contains an invalid user identifier.",
            code="TOKEN_INVALID_SUBJECT",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError(
            message="User account associated with this token was not found.",
            code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise AuthenticationError(
            message="User account has been deactivated.",
            code="USER_INACTIVE",
        )

    return user


async def get_optional_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Resolves current user if token is provided and valid; returns None otherwise.
    Allows public browsing with enriched personalization when authenticated.
    """
    if not auth_credentials or not auth_credentials.credentials:
        return None
    try:
        payload = decode_access_token(auth_credentials.credentials)
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            return None
        user_id = uuid.UUID(str(user_id_raw))
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except Exception:
        return None

