"""
schemas/token.py — JWT Token Schemas

Pydantic v2 models for JWT claims and auth API contracts.
All models use strict mode: extra fields are rejected.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TokenClaims(BaseModel):
    """
    Parsed and validated JWT payload claims.
    This is the object passed down the request pipeline after validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    sub: str = Field(..., description="Subject — unique user identifier")
    jti: str = Field(..., description="JWT ID — unique token identifier for replay protection")
    type: Literal["access", "refresh"] = Field("access", description="Type of the token")
    roles: list[str] = Field(default_factory=list, description="User roles")
    iss: str = Field(..., description="Issuer")
    aud: list[str] = Field(..., description="Audience")
    exp: int = Field(..., description="Expiry timestamp (Unix)")
    iat: int = Field(..., description="Issued-at timestamp (Unix)")


class TokenRequest(BaseModel):
    """Request body for POST /auth/token."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., min_length=1, max_length=128)
    client_secret: str = Field(..., min_length=8, max_length=512)


class TokenResponse(BaseModel):
    """Response body for POST /auth/token."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds")
    refresh_token: str | None = Field(None, description="Refresh token")


class RefreshTokenRequest(BaseModel):
    """Request body for POST /auth/refresh."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., description="Refresh token string")
