# Refresh Token Flow Implementation

This plan details the implementation of the Refresh Token flow (Phase 1 of NEXT_TASKS). It strictly adheres to the security guidelines mandated in `GEMINI.md`, ensuring fail-closed behavior, token type separation, and strict schema validation.

## User Review Required

> [!IMPORTANT]
> **Token Type Separation**: We will introduce a new `type` field in the JWT payload (`type: "access"` and `type: "refresh"`). This guarantees that a leaked refresh token cannot be used to call proxy endpoints, and an access token cannot be used to request a refresh token.
> **Refresh Rotation**: The `/auth/refresh` endpoint will return a *new* access token AND a *new* refresh token. The client should discard the old refresh token.
> Please let me know if you approve this plan or have any objections before I proceed.

## Proposed Changes

### Schemas

#### [MODIFY] [token.py](file:///d:/Desktop/Дипломка%20-%20iiko%20Secure%20API%20Gateway%20(ISAG)/backend/app/schemas/token.py)
* Add `type: Literal["access", "refresh"] = "access"` to `TokenClaims`.
* Update `TokenResponse` to include `refresh_token: str | None = None`.
* Create new model `RefreshTokenRequest`:
```python
class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(..., description="The refresh token string")
```

---
### Security Logic

#### [MODIFY] [jwt_validator.py](file:///d:/Desktop/Дипломка%20-%20iiko%20Secure%20API%20Gateway%20(ISAG)/backend/app/security/jwt_validator.py)
* Update `JWTValidator.validate(self, raw_token: str)` to `JWTValidator.validate(self, raw_token: str, expected_type: str = "access")`.
* In `validate`, verify that `payload.get("type", "access") == expected_type`. Reject immediately if mismatched.
* Include `type` when mapping to `TokenClaims`.

---
### API Endpoints

#### [MODIFY] [auth.py](file:///d:/Desktop/Дипломка%20-%20iiko%20Secure%20API%20Gateway%20(ISAG)/backend/app/api/auth.py)
* **`_issue_access_token`**: Include `"type": "access"` in the generated payload.
* **Add `_issue_refresh_token`**: Same structure as access token but uses `settings.jwt_refresh_token_expire_days`, omits `roles`, and includes `"type": "refresh"`.
* **Update `/auth/token`**: Modify the response to generate and include a `refresh_token` using the new function.
* **New Endpoint `/auth/refresh`**:
  * Extracts the token from `RefreshTokenRequest`.
  * Validates it via `validator.validate(..., expected_type="refresh")`.
  * Verifies the client associated with the `sub` claim still exists and is active in `_get_client_registry()`. (Strict security logic: if the user was deleted/banned, refresh will fail).
  * Returns a new Access Token and a new Refresh Token.

## Open Questions

None at this time.

## Verification Plan

### Automated Tests
- The proxy tests and auth tests will be reviewed to ensure existing login flows use the new `type` field correctly.
- Add/update token expiration/rejection tests using `RefreshRequest`.

### Manual Verification
1. Run application via `fastapi run` or `uvicorn`.
2. Generate token pair with `POST /auth/token`.
3. Verify proxy rejects the new `refresh_token` if sent as Bearer authorization.
4. Verify `POST /auth/refresh` succeeds with the `refresh_token` and fails with an `access_token`.
