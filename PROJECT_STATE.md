# Project State: iiko Secure API Gateway (ISAG)

## Current Status
- **Tests Passing**: 100% (39/39).
- **Core Features**: Authentication, JWT Validation, RBAC, Rate Limiting, and Secure Proxying are verified and stable.
- **Security Pipeline**: Fully enforced as per `Gemini.md`.

## Summary of Fixes Applied
- **Test Infrastructure Stability**:
  - Implemented real `Settings` initialization in `conftest.py` with temporary RSA key files.
  - Eliminated redundant `patch("app.security.jwt_validator.get_settings")` calls across the test suite, favoring genuine FastAPI dependency injection.
  - Resolved `TypeError` in proxy mocks by transitioning from simple `AsyncMock` to proper `@asynccontextmanager` mocks.
- **Fail-Closed JWT Validation**:
  - Added explicit validation for the `sub` claim in `JWTValidator` to prevent internal server errors (KeyError).
  - Fixed 422 Unprocessable Entity errors by aligning token claim schemas and increasing mock `client_secret` length to meet Pydantic requirements.
- **Rate Limiter Unification**:
  - Unified the module-level `limiter` singleton and the `app.state.limiter` in `main.py` to ensure consistent rate tracking across decorators and middleware.
- **DB Isolation in Tests**:
  - Mocked `get_client_by_id` in authentication and rate limit integration tests to ensure tests run reliably without requiring a persistent SQLite schema during CI-like runs.

## Detailed Auth Fixes
- **make_token Fixture**: Updated to correctly preserve an empty `roles=[]` list (previously defaulted back to `["operator"]`).
- **Token Claims**: Correctly implemented the `"type": "access"` (or `"refresh"`) claim required by the validator.
- **Validation Logic**: Transitioned from Pydantic `422` validation errors to strict `401 Unauthorized` responses for malformed or invalid tokens, maintaining the "Fail-Closed" principle.

## Modified Files
- `backend/app/main.py`
- `backend/app/security/jwt_validator.py`
- `backend/app/middleware/rate_limiter.py`
- `backend/tests/conftest.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_jwt.py`
- `backend/tests/test_proxy.py`
- `backend/tests/test_rbac.py`
- `backend/tests/test_rate_limit.py`

## Next Steps
- **Phase 2: Containerization**: Implement `Dockerfile` and `docker-compose.yml` for production-like deployment.
- **Phase 3: Persistence Layer**: Finalize Redis migration for the rate limiter and implement structured audit logs.
