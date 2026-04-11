# PROJECT_STATE.md — Checkpoint: Auth Fixes Complete

**Date:** 2026-04-11  
**Session:** Auth Stabilization Phase 1  
**Status:** 🔧 In Progress — Auth flow fixed, remaining test failures being resolved

---

## Current Test Status

| Suite | Pass | Fail | Notes |
|---|---|---|---|
| test_auth.py | 1 | 1 | happy-path refresh in progress |
| test_jwt.py | 4 | 9 | `"type"` claim fix applied, pending settings fixture |
| test_proxy.py | 5 | 4 | settings fixture root cause |
| test_rate_limit.py | 2 | 2 | settings fixture root cause |
| test_rbac.py | 0 | 5 | settings fixture root cause |

Root cause of remaining failures: `test_settings` used a `MagicMock` which was not compatible with FastAPI's `Depends()` Pydantic annotation resolution. Being replaced with a real `Settings` instance.

---

## Fixes Applied This Session

### Fix 1 — IndentationError in `app/api/auth.py` (line 40)
- Comment barrier `# ------` was accidentally merged with `def _issue_access_token(...)` on the same line.
- Fixed by separating the comment and the `def` onto distinct lines.

### Fix 2 — `TESTING=1` env var missing in `conftest.py`
- `main.py` guards module-level `create_app()` with `os.environ.get("TESTING") != "1"`.
- Without the flag, importing `app.main` in tests eagerly called `get_settings()`, which failed due to missing env vars in `.env`.
- Fixed by adding `os.environ["TESTING"] = "1"` at the top of `conftest.py`.

### Fix 3 — `AttributeError: 'MutableHeaders' has no attribute 'pop'`
- `secure_headers.py` called `response.headers.pop(header, None)`.
- Starlette's `MutableHeaders` does not implement `.pop()`.
- Fixed by replacing with `if header in response.headers: del response.headers[header]`.

### Fix 4 — Pydantic 422 Unprocessable Entity on all token-requiring routes
- `get_settings` dependency resolved to `MagicMock()`.
- FastAPI Pydantic validation failed because MagicMock returns MagicMock for all attributes rather than proper typed values.
- Fixed by replacing `MagicMock()` with a real `Settings()` instance in `test_settings` fixture, injecting RSA keys via `object.__setattr__`.
- Registered `dependency_overrides[get_settings] = override_get_settings` in `async_client` fixture.

### Fix 5 — `make_token` missing `"type"` claim
- After `token.type` field was added to `TokenClaims` and validator began asserting `token_type == expected_type`, tokens issued in tests without a `"type"` claim defaulted to being rejected.
- Fixed by adding `token_type: str = "access"` parameter to `make_token` and including `"type": token_type` in the JWT payload.

### Fix 6 — Negative tests for `/auth/refresh` and proxy added
- `test_refresh_token_rejected_for_proxy`: sends `token_type="refresh"` to `/api/v1/restaurants`, expects HTTP 401.
- `test_access_token_rejected_at_refresh_endpoint`: sends `token_type="access"` to `/auth/refresh`, expects HTTP 401.

---

## Auth Flow — Detailed Notes

### `make_token` Fixture Update
```python
# Before (missing 'type' claim)
payload = {"sub": ..., "roles": ..., "iss": ..., ...}

# After
payload = {"type": token_type, "sub": ..., "roles": ..., ...}
```
Default `token_type="access"`. Pass `token_type="refresh"` for refresh token tests.

### Token Type Enforcement
`JWTValidator.validate(raw_token, expected_type="access")` now:
1. Decodes and verifies signature.
2. Reads `payload.get("type", "access")`.
3. Rejects with HTTP 401 if `type != expected_type`.

This strictly enforces that refresh tokens cannot be used on proxy routes and access tokens cannot be used to refresh.

### HTTP 422 Root Cause
The `test_settings` fixture returned a `MagicMock`. When FastAPI resolved `Depends(get_settings)` it received the mock, but Pydantic tried to validate its fields (like `iiko_api_base_url`) and failed. The dependency override was not registerd correctly because `lru_cache` on `get_settings` was pre-populated. Fixed by:
1. Providing real `Settings()` with env vars set.
2. Overriding RSA keys in-memory via `object.__setattr__`.
3. Registering `application.dependency_overrides[get_settings] = override_get_settings`.

---

## Modified Files

| File | Change |
|---|---|
| `app/api/auth.py` | Fixed IndentationError (line 40) |
| `app/middleware/secure_headers.py` | Replaced `.pop()` with `del` on MutableHeaders |
| `tests/conftest.py` | Added `TESTING=1`; replaced MagicMock with real Settings; added `dependency_overrides`; added `token_type` to `make_token` |
| `tests/test_proxy.py` | Added `test_refresh_token_rejected_for_proxy` negative test |
| `tests/test_auth.py` | **NEW** — auth endpoint tests including negative test |

---

## Next Steps

1. **Complete Fix 4**: Verify real `Settings()` fixture resolves all remaining 422 errors.
2. **Run full pytest**: Target 39/39 pass.
3. **Phase 2**: Dockerfile + docker-compose.yml.
4. **Phase 3**: Redis-backed rate limiting.
5. **Phase 4**: Persistent audit log storage.
