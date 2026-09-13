"""
Global Application Exception Definitions and Exception Handlers.
"""
from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        self.headers = headers
        super().__init__(message)


class AuthenticationError(AppException):
    """Raised when authentication fails (missing, expired, or invalid token/credentials)."""
    def __init__(
        self,
        message: str = "Could not validate credentials.",
        code: str = "UNAUTHORIZED",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=code,
            details=details,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserAlreadyExistsError(AppException):
    """Raised when a user registration attempt uses an existing email."""
    def __init__(
        self,
        message: str = "A user with this email address already exists.",
        code: str = "USER_ALREADY_EXISTS",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code=code,
            details=details,
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""
    def __init__(
        self,
        message: str = "Requested resource not found.",
        code: str = "NOT_FOUND",
        details: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code=code,
            details=details,
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred.",
                    "details": str(exc) if app.debug else None,
                }
            },
        )
