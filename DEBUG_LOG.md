# Debug Log — Authentication & Testing Stability

## Bug 1: settings_init_missing_files
- **Bug**: `FileNotFoundError` during Pydantic `Settings` initialization in tests.
- **Root Cause**: `Settings.model_post_init` was designed to read RSA keys from disk immediately. Tests used `MagicMock` which failed Pydantic validation or lacked actual file handles.
- **Fix**: Updated `conftest.py` to use `tmp_path_factory` to generate actual `.pem` and `.json` files before initializing a real `Settings` object.
- **Status**: ✅ Resolved

## Bug 2: redundant_patch_conflicts
- **Bug**: Tests failing with 404 or 422 even when tokens were valid.
- **Root Cause**: Complex nested `with patch(...)` blocks in `test_jwt.py` were overwriting the `async_client`'s dependency overrides, leading to inconsistent configuration state.
- **Fix**: Removed all manual patches of `get_settings`. Standardized on FastAPI's `app.dependency_overrides` within the `async_client` fixture.
- **Status**: ✅ Resolved

## Bug 3: mock_context_manager_typeerror
- **Bug**: `TypeError: 'builtins.coroutine' object does not support the asynchronous context manager protocol`.
- **Root Cause**: `proxy_request_stream` is a streaming context manager (`@asynccontextmanager`). Mocking it with a standard `AsyncMock` return value failed when the app tried to use it with `async with`.
- **Fix**: Replaced mocks with actual local `@asynccontextmanager` helper functions within tests to simulate streaming behavior.
- **Status**: ✅ Resolved

## Bug 4: missing_sub_claim_keyerror
- **Bug**: 500 Internal Server Error when a JWT was missing the `sub` claim.
- **Root Cause**: `JWTValidator.validate` directly accessed `payload["sub"]` without checking existence, violating the "Fail-Closed" principle.
- **Fix**: Added explicit membership check for `sub` and `iss` claims, calling `_reject()` to return a proper 401 response instead of crashing.
- **Status**: ✅ Resolved

## Bug 5: rate_limit_limiter_divergence
- **Bug**: `test_auth_endpoint_rate_limit_behavior` failing to trigger 429.
- **Root Cause**: `main.py` created a new `Limiter` instance for the app state, while the `@limiter.limit` decorator on the route held a reference to the original module-level singleton. They did not share the same in-memory storage.
- **Fix**: Reconfigured `main.py` to use the global `limiter` singleton and updated its default limits at runtime.
- **Status**: ✅ Resolved

## Bug 6: test_fixture_roles_defaulting
- **Bug**: `test_no_roles_denied` passing with 200 instead of 403.
- **Root Cause**: `make_token` fixture used `roles or ["operator"]`. Passing `roles=[]` (empty list) is falsy in Python, so it defaulted back to providing the operator role.
- **Fix**: Changed logic to `roles if roles is not None else ["operator"]`.
- **Status**: ✅ Resolved

---

## Feature Implementation Log

### Refresh Token Flow (2026-04-13)
- **Feature**: Implemented `/auth/refresh` endpoint with full token-type separation.
- **Changes**:
  - `app/schemas/token.py`: Added `type` field to `TokenClaims`; added `RefreshTokenRequest` model; updated `TokenResponse` to include `refresh_token`.
  - `app/security/jwt_validator.py`: Updated `validate(raw_token, expected_type="access")` to enforce `type` claim matching. Refresh tokens passed to proxy endpoints are rejected (type `access` required); access tokens passed to `/auth/refresh` are rejected (type `refresh` required).
  - `app/api/auth.py`: Added `_issue_refresh_token()` helper; updated `/auth/token` to return token pair; implemented `/auth/refresh` with client re-verification from DB.
- **Tests**: `test_auth.py` — `test_refresh_token_issues_new_pair` (happy path), `test_access_token_rejected_at_refresh_endpoint` (negative).
- **Status**: ✅ Implemented & Tested

### DB-Backed Client Registry (2026-04-11)
- **Feature**: Replaced in-memory/hardcoded client registry with SQLAlchemy 2.0 async SQLite.
- **Changes**:
  - `app/models/client.py`: `GatewayClient` SQLAlchemy model with `client_id`, `hashed_secret`, `roles`, `is_active`.
  - `app/db/engine.py`: Async engine, `AsyncSessionLocal`, `init_db()`, `get_db_session()`.
  - `app/services/client_service.py`: `get_client_by_id()` coroutine.
  - `app/core/hashing.py`: `get_password_hash()`, `verify_password()`, `dummy_verify()`.
  - `app/main.py`: `seed_demo_client()` runs on startup to bootstrap the default client.
- **Status**: ✅ Implemented & Tested
