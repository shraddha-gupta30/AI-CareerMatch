"""
Authentication API Endpoints: Register, Login, and Current User.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import AuthenticationError, UserAlreadyExistsError
from app.core.logging import logger
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new candidate user, securely hashes password, and issues an initial JWT token.",
)
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    # Check for existing email
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.info(f"Registration rejected: email '{payload.email}' already exists.")
        raise UserAlreadyExistsError(
            message=f"An account with email '{payload.email}' already exists."
        )

    # Securely hash password with bcrypt
    hashed_pwd = hash_password(payload.password)

    new_user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hashed_pwd,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"User registered successfully: id={new_user.id}, email={new_user.email}")

    # Issue JWT access token
    access_token = create_access_token(
        subject=str(new_user.id),
        claims={"email": new_user.email},
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(new_user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticates candidate credentials and returns a JWT access token.",
)
async def login_user(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning(f"Login failed for email: {payload.email}")
        raise AuthenticationError(
            message="Invalid email or password.",
            code="INVALID_CREDENTIALS",
        )

    if not user.is_active:
        logger.warning(f"Login attempt on inactive account: {payload.email}")
        raise AuthenticationError(
            message="Your account is deactivated. Please contact support.",
            code="ACCOUNT_INACTIVE",
        )

    access_token = create_access_token(
        subject=str(user.id),
        claims={"email": user.email},
    )

    logger.info(f"User logged in successfully: id={user.id}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the identity profile of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
