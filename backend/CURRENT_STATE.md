# Current State: ISAG Production Milestone

## 1. Production-Ready Features (100% Implemented)
- **Hardened Proxy Engine**: Asynchronous, non-buffering streaming reverse proxy. Verified with `LEGIT` traffic archetype.
- **RS256 JWT Security**:
  - Dynamic **Key Rotation** via `kid` header and `public_keys.json`.
  - Fail-Closed configuration (app refuses to start without valid RSA secrets).
  - **Token Type Separation**: `type: "access"` vs `type: "refresh"` enforced at validation layer.
- **Refresh Token Flow**:
  - `/auth/token` returns both `access_token` and `refresh_token`.
  - `/auth/refresh` validates refresh token type, re-fetches client from DB, issues new token pair (rotation).
  - Expired or wrong-type tokens are strictly rejected with HTTP 401.
- **Stateful Replay Protection**: Distributed JTI blacklisting in Redis using atomic `SET NX EX` operations.
- **Distributed Rate Limiting**: Multi-layer throttling (IP/User/Endpoint) backed by Redis storage.
- **RBAC Enforcement**: Fine-grained role-to-permission mapping (`proxy:read`, `proxy:write`).
- **DB-Backed Client Registry**: `GatewayClient` model via SQLAlchemy 2.0 async (SQLite default, PostgreSQL-ready). Bcrypt-hashed secrets with constant-time verification and anti-timing-oracle `dummy_verify()` guard.
- **Observability Stack**:
  - Prometheus metrics with **Path Normalization** logic.
  - Pre-provisioned Grafana dashboards for attack visualization.
  - JSON-structured audit logging with `request_id` and `user_id`.

## 2. Infrastructure & DevSecOps
- **Dockerization**: Full-stack orchestration via `docker-compose.yml` (Gateway + Redis + Prometheus + Grafana).
- **CI/CD**: GitHub Actions pipeline enforcing 65-test verification on every push.
- **Secrets Management**: Strict environment validation using `pydantic-settings` — fails startup on missing config.

## 3. Performance & Resilience
- **Fail-Closed Strategy**: The system defaults to "Deny" in all ambiguous states (missing Redis, missing key, missing claim).
- **Zero-Buffering**: Proxies large payloads without memory spikes (Streaming request/response via `httpx`).
- **Concurrency**: Tuned `httpx.AsyncClient` pool for high-throughput upstream communication.

## 4. Test-Suite Bug Fixes (Resolved)
All 6 bugs documented in `DEBUG_LOG.md` have been identified and fixed:
| Bug ID | Summary | Fix Applied |
| :--- | :--- | :--- |
| `settings_init_missing_files` | `FileNotFoundError` in tests | `tmp_path_factory` generates real PEM/JSON files for `Settings` init |
| `redundant_patch_conflicts` | Nested `with patch(...)` broke DI | Replaced with `app.dependency_overrides` in `async_client` fixture |
| `mock_context_manager_typeerror` | `AsyncMock` can't be async ctx manager | Replaced with inline `@asynccontextmanager` helpers |
| `missing_sub_claim_keyerror` | 500 on missing `sub` → now 401 | Explicit membership check in `JWTValidator.validate()` |
| `rate_limit_limiter_divergence` | 429 never triggered | Global `limiter` singleton used in `main.py` and route decorators |
| `test_fixture_roles_defaulting` | `roles=[]` silently became `["operator"]` | Logic changed to `roles if roles is not None else ["operator"]` |

## 5. Final Verification (2026-04-14)
- **Test Suite**: 65/65 tests passed.
- **Coverage**: 83% on core security modules (`app/security/`, `app/services/`).
- **Security Pipeline**: 9 active stages verified via `test_pipeline_hardening.py`.
- **Refresh Token Scenario**: Verified end-to-end (token pair issuance → refresh → new pair, type rejection).
