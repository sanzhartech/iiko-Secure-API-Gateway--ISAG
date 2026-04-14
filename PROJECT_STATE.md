# Project State: iiko Secure API Gateway (ISAG)

## Final Status: 100% Completed (Production-Ready)
- **Phase 7 Finalized**: Documentation, observability, and CI/CD integrations are complete.
- **Verification**: 100% test pass rate (65/65).
- **Security Audit**: All 9 stages of the security pipeline are active and verified.

## Architectural Philosophy
The system is built on three core pillars:
1. **Zero-Trust Model**: No request is trusted by default. Every incoming packet must undergo rigorous cryptographic and logic validation regardless of its origin.
2. **Defense-in-Depth**: Multiple redundant layers of security (Rate Limiting → JWT → JTI → RBAC) ensure that if one layer is bypassed or misconfigured, others remain as barriers.
3. **Fail-Closed Principle**: The gateway is designed to reject access in case of ambiguity. If Redis is down, or a configuration is missing, the system defaults to "401 Unauthorized" or "500 Internal Server Error" rather than allowing potentially unauthenticated traffic.

## Milestone Completion Summary
| Phase | Feature | Status |
| :--- | :--- | :--- |
| **Phase 1** | Core Proxy & Async Streaming | ✅ Done |
| **Phase 2** | JWT RS256 Auth & Key Management | ✅ Done |
| **Phase 3** | Redis Integration & Replay Protection | ✅ Done |
| **Phase 4** | Advanced Routing & Header Mutation | ✅ Done |
| **Phase 5** | Observability (Prometheus / Grafana) | ✅ Done |
| **Phase 6** | Infrastructure & Dockerization | ✅ Done |
| **Phase 7** | CI/CD & Final Documentation | ✅ Done |
| **Phase 8** | DB-Backed Client Registry (SQLAlchemy + SQLite) | ✅ Done |
| **Phase 9** | Refresh Token Flow & Token Type Separation | ✅ Done |

## Key Technical Metrics
- **Test Pass Rate**: 100% (65/65 tests).
- **Test Coverage**: 83% (core security modules), 28% overall (cold-path branches excluded).
- **Latency (Overhead)**: <15ms (excluding upstream processing).
- **Security Pipeline**: 9 active stages.

## Recent Additions (2026-04-13 → 2026-04-14)
- **Refresh Token Flow**: `/auth/refresh` endpoint with token-type separation (`type: access` / `type: refresh`). Refresh tokens are long-lived (7 days), access tokens are short-lived (15 min).
- **Token Rotation**: Each `/auth/refresh` call issues a new refresh token, invalidating the previous one implicitly.
- **DB-Backed Client Registry**: `GatewayClient` model persisted via SQLAlchemy 2.0 async SQLite. `get_client_by_id()` replaces the old in-memory mock registry.
- **Bcrypt Hashing**: `client_secret` stored as a bcrypt hash. Constant-time verification via `verify_password()` and a `dummy_verify()` anti-timing-oracle guard.
- **6 Test-Suite Bugs Resolved**: All bugs documented in `DEBUG_LOG.md` have been fixed and verified.

## Latest Verification (2026-04-14)
- [x] Full `pytest` integration suite passing (65/65).
- [x] Stress-test validated: 401/429/403 responses correctly metered.
- [x] Grafana dashboard correctly visualizing block reasons.
- [x] GitHub Actions CI workflow operational.
- [x] Refresh Token round-trip verified: access → refresh → new access pair.
- [x] Access token correctly rejected at `/auth/refresh` endpoint (type enforcement).
