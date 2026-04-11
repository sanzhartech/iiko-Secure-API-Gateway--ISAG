# DEBUG_LOG.md — Session Bug Log

**Session:** 2026-04-11 Auth Stabilization  
**Project:** iiko Secure API Gateway (ISAG)

---

## Bug #1 — IndentationError in auth.py

| Field | Detail |
|---|---|
| **File** | `app/api/auth.py`, line 40 |
| **Error** | `IndentationError: unexpected indent` |
| **Root Cause** | The separator comment `# -----------...` was merged onto the same line as the function definition `def _issue_access_token(...)`. Python parsed the function body as an unexpected indent. This likely happened during a copy-paste or editor operation. |
| **Fix** | Inserted a newline between the comment and the `def` statement. File now has them on separate lines. |

---

## Bug #2 — Tests failing: `pydantic_core.ValidationError: 4 validation errors for Settings`

| Field | Detail |
|---|---|
| **Files** | All test files via `conftest.py` / `app/main.py` |
| **Error** | `ValidationError: iiko_api_base_url Field required`, `iiko_api_key Field required`, `gateway_client_secret Field required`, `python_path Extra inputs are not permitted` |
| **Root Cause** | `app/main.py` had a module-level guard: `if os.environ.get("TESTING") != "1": app = create_app()`. During test collection pytest imported `app.main`, which triggered `create_app()` → `get_settings()`. The `.env` file only contained `PYTHON_PATH=venv\Scripts\python.exe` — an extra field that `Settings(extra="forbid")` rejects. Required fields were also missing. |
| **Fix** | Added `os.environ["TESTING"] = "1"` at the very top of `tests/conftest.py` so the module-level guard in `main.py` is triggered before any app code runs. |

---

## Bug #3 — `AttributeError: 'MutableHeaders' object has no attribute 'pop'`

| Field | Detail |
|---|---|
| **File** | `app/middleware/secure_headers.py`, line 77 |
| **Error** | `AttributeError: 'MutableHeaders' object has no attribute 'pop'` |
| **Root Cause** | Starlette's `MutableHeaders` class implements the `MutableMapping` protocol but does NOT provide a `pop()` method, unlike Python's built-in `dict`. |
| **Fix** | Replaced `response.headers.pop(header, None)` with `if header in response.headers: del response.headers[header]`, which uses only the interface Starlette guarantees. |

---

## Bug #4 — HTTP 422 Unprocessable Entity on all auth-gated routes in tests

| Field | Detail |
|---|---|
| **Files** | `tests/test_jwt.py`, `test_proxy.py`, `test_rbac.py`, `test_rate_limit.py` |
| **Error** | All routes returning 422 instead of expected 200/401/403 |
| **Root Cause (a)** | `test_settings` was a `MagicMock()`. When FastAPI dependency injection resolved `Depends(get_settings)`, Pydantic received the mock and could not validate typed fields such as `iiko_api_base_url: str`. `MagicMock.__getattr__` returns another `MagicMock`, which is not a `str`. |
| **Root Cause (b)** | The `with patch("app.security.jwt_validator.get_settings", ...)` context manager overrode the module-level reference but `dependency_overrides` was not set on the app, so the FastAPI DI machinery still resolved to the uncached real `get_settings()`. |
| **Fix** | Replaced `MagicMock()` with a real `Settings()` instance. Required env vars set via `os.environ` inside the fixture. RSA keys injected via `object.__setattr__` (bypassing `frozen` Pydantic model). Registered `application.dependency_overrides[get_settings] = override_get_settings` in `async_client` fixture. |

---

## Bug #5 — HTTP 401 on valid tokens after `"type"` claim enforcement

| Field | Detail |
|---|---|
| **Files** | `tests/conftest.py` → `make_token`, all test files |
| **Error** | Tests issuing tokens and expecting 200 started getting 401 |
| **Root Cause** | `JWTValidator.validate()` was updated to enforce `payload["type"] == expected_type`. The `make_token` factory fixture didn't include a `"type"` claim. Without the claim the validator defaulted to `payload.get("type", "access")` — but `expected_type="access"` was the default too — so this should have passed. Actual cause was that `"type"` was absent while the `TokenClaims` Pydantic model now required it via `Literal["access", "refresh"]` without a fallback, causing a validation failure. |
| **Fix** | Added `token_type: str = "access"` parameter to `make_token`. Added `"type": token_type` to the JWT payload dict. Default is `"access"` for backward compatibility; tests requiring refresh tokens pass `token_type="refresh"`. |

---

## Bug #6 — `test_refresh_token_issues_new_pair` failing with 422

| Field | Detail |
|---|---|
| **File** | `tests/test_auth.py` |
| **Error** | HTTP 422 on `POST /auth/refresh` |
| **Root Cause** | The `with patch("app.api.auth.get_settings", ...)` pattern was being used but this patches the name `get_settings` in the `auth` module's namespace. However `get_settings` is used as a FastAPI `Depends()` argument — FastAPI resolves it through dependency injection, NOT by calling `auth.get_settings()` directly. The patch therefore did not apply. FastAPI still called the real `get_settings()` dependency, which failed. |
| **Fix** | Removed the erroneous `patch("app.api.auth.get_settings")` from the test. The `dependency_overrides` mechanism in `conftest.py` handles this globally for all tests. Patched only `app.api.auth.get_client_by_id` (an async function called directly inside the handler) via `new_callable=AsyncMock`. |
