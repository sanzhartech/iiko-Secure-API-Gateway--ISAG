# Project State: iiko Secure API Gateway (ISAG)

## Final Status: 100% Completed (Hardened & Documented)
- **Phase 7 Finalized**: Documentation, observability, and CI/CD integrations are complete.
- **Verification**: 100% test pass rate (68/68).
- **Security Audit**: All 9 stages of the security pipeline are active and verified.
- **JTI Replay Fix**: Implemented a 2-second grace period for JTI Store to support parallel frontend requests.

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
| **Phase 10** | JTI Replay Grace Period (frontend stability) | ✅ Done |

## Key Technical Metrics
- **Test Pass Rate**: 100% (68/68 tests).
- **Test Coverage**: 83% (core security modules), 28% overall (cold-path branches excluded).
- **Latency (Overhead)**: <15ms (excluding upstream processing).
- **Security Pipeline**: 9 active stages.

## Recent Additions (2026-05-04)
- **JTI Replay Grace Period**: Added a 2-second window for identical tokens to support React parallel fetching without triggering 401 errors.
- **Academic Technical Documentation**: Added `technical_documentation.md` with mathematical justification for RS256 and deep-dives into system architecture.
- **Grafana Provisioning**: Automated datasource and dashboard setup for immediate observability.

## Latest Verification (2026-05-04)
- [x] Full `pytest` suite passing (68/68) with new JTI logic.
- [x] Parallel request stress-test verified on Admin Dashboard.
- [x] Grafana metrics (`isag_requests_total`) confirmed working.
- [x] Refresh Token round-trip verified: access → refresh → new access pair.
