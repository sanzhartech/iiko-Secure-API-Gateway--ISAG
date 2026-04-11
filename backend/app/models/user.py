"""
models/user.py — Domain Models

Simple, immutable domain models for users and roles.
These are NOT ORM models — ISAG is stateless and authenticates via JWT.
For a production deployment with a user database, replace these with
SQLAlchemy / asyncpg models and a user service.

[Fix #6] DEPRECATION WARNING:
  The `User` class below is currently NOT USED anywhere in production code.
  All request pipelines pass `TokenClaims` (from schemas/token.py) directly.
  Before shipping: either wire `User.from_claims()` into the pipeline OR
  delete this file and its __init__.py re-export to avoid dead code confusion.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Represents an authenticated user extracted from JWT claims."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(..., description="Unique user identifier (JWT sub)")
    roles: list[str] = Field(default_factory=list)
    is_active: bool = True

    @classmethod
    def from_claims(cls, sub: str, roles: list[str]) -> "User":
        """Construct a User from validated JWT claims."""
        return cls(user_id=sub, roles=roles)
