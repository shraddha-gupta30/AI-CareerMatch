"""
Declarative Base for SQLAlchemy ORM Models.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all domain database models."""
    pass
