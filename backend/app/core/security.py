"""
Core Security Module: Password Hashing (bcrypt) & JWT Authentication (PyJWT).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from app.core.config import settings
from app.core.exceptions import AuthenticationError

# Standard HS256 algorithm for symmetric JWT signing
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt with auto-generated salt.
    Never stores or logs plaintext passwords.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a bcrypt-hashed password string.
    Returns True if valid, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token containing subject (user ID) and expiration.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if claims:
        to_encode.update(claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT token.
    Raises AuthenticationError on expired signature or invalid token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(
            message="Access token has expired. Please log in again.",
            code="TOKEN_EXPIRED",
        )
    except jwt.InvalidTokenError:
        raise AuthenticationError(
            message="Invalid or malformed access token.",
            code="TOKEN_INVALID",
        )
