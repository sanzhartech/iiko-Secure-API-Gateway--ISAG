# Debug Log — Authentication & Testing Stability

## Bug 1: settings_init_missing_files
- **Bug**: `FileNotFoundError` during Pydantic `Settings` initialization in tests.
- **Root Cause**: `Settings.model_post_init` was designed to read RSA keys from disk immediately. Tests used `MagicMock` which failed Pydantic validation or lacked actual file handles.
- **Fix**: Updated `conftest.py` to use `tmp_path_factory` to generate actual `.pem` and `.json` files before initializing a real `Settings` object.

## Bug 2: redundant_patch_conflicts
- **Bug**: Tests failing with 404 or 422 even when tokens were valid.
- **Root Cause**: Complex nested `with patch(...)` blocks in `test_jwt.py` were overwriting the `async_client`'s dependency overrides, leading to inconsistent configuration state.
- **Fix**: Removed all manual patches of `get_settings`. Standardized on FastAPI's `app.dependency_overrides` within the `async_client` fixture.

## Bug 3: mock_context_manager_typeerror
- **Bug**: `TypeError: 'builtins.coroutine' object does not support the asynchronous context manager protocol`.
- **Root Cause**: `proxy_request_stream` is a streaming context manager (`@asynccontextmanager`). Mocking it with a standard `AsyncMock` return value failed when the app tried to use it with `async with`.
- **Fix**: Replaced mocks with actual local `@asynccontextmanager` helper functions within tests to simulate streaming behavior.

## Bug 4: missing_sub_claim_keyerror
- **Bug**: 500 Internal Server Error when a JWT was missing the `sub` claim.
- **Root Cause**: `JWTValidator.validate` directly accessed `payload["sub"]` without checking existence, violating the "Fail-Closed" principle.
- **Fix**: Added explicit membership check for `sub` and `iss` claims, calling `_reject()` to return a proper 401 response instead of crashing.

## Bug 5: rate_limit_limiter_divergence
- **Bug**: `test_auth_endpoint_rate_limit_behavior` failing to trigger 429.
- **Root Cause**: `main.py` created a new `Limiter` instance for the app state, while the `@limiter.limit` decorator on the route held a reference to the original module-level singleton. They did not share the same in-memory storage.
- **Fix**: Reconfigured `main.py` to use the global `limiter` singleton and updated its default limits at runtime.

## Bug 6: test_fixture_roles_defaulting
- **Bug**: `test_no_roles_denied` passing with 200 instead of 403.
- **Root Cause**: `make_token` fixture used `roles or ["operator"]`. Passing `roles=[]` (empty list) is falsy in Python, so it defaulted back to providing the operator role.
- **Fix**: Changed logic to `roles if roles is not None else ["operator"]`.
