# PROJECT_CONTEXT: ISAG Architecture & Security Philosophy

**iiko Secure API Gateway (ISAG)** is a hardened, high-performance security layer implemented as an asynchronous reverse proxy. It serves as the single entry point for all client integrations with the iiko ERP/API ecosystem, providing a Zero-Trust environment.

## 1. Core Security Philosophies

### 🛡️ Defense-in-Depth
ISAG implements security as a layered onion. A single failure or misconfiguration in one component (e.g., an overly permissive JWT) is balanced by other layers (e.g., mandatory RBAC or IP-based rate limiting).

### 🚦 Fail-Closed
Security logic is deterministic. In any state of ambiguity — such as a missing configuration parameter, an unreachable Redis cluster, or a malformed security header — the gateway defaults to the most restrictive state (DENY).

### 🔍 Zero-Trust & Identity
Regardless of the network origin, every request must undergo:
1.  **Cryptographic Identity Verification** (RS256 JWT).
2.  **Token Type Validation**: Access tokens for proxying, Refresh tokens for rotation.
3.  **Stateful Replay Verification** (JTI/Redis).
4.  **Authorization Check** (RBAC).

---

## 2. Integrated Security Pipeline (9 Stages)

Requests traverse the following pipeline (LIFO middleware stack):

1.  **Transport Security (Outermost)**: Enforcing HSTS, CSP, and X-Content-Type protections.
2.  **Request Size Validation**: Immediate rejection of payloads exceeding 10MB to mitigate DoS.
3.  **Distributed Rate Limiting**: Throttling via Redis to protect the gateway and upstream.
4.  **CORS Enforcement**: Cross-origin policy validation.
5.  **Audit Logging**: Metadata collection for security forensics (with correlation IDs).
6.  **Telemetry**: Prometheus metrics instrumentation with Path Normalization.
7.  **Authentication & JTI**: JWT RS256 validation (with `kid` rotation) + atomic JTI replay check.
8.  **RBAC Authorization**: Fine-grained role permission checks.
9.  **Response Filtering (Innermost)**: Sanitizing outgoing headers (e.g., removing `Server` signatures).

---

## 3. Key Technical Decisions

### LIFO Middleware Stack
Middleware in ISAG is registered in LIFO (Last-In-First-Out) order. This ensures that the most "expensive" processing (like proxying) happens only after the "cheapest" validations (like Request Size and Rate Limiting) have passed.

### Redis Atomic SET NX EX
To prevent Replay Attacks, ISAG uses Redis `SET (key) 1 NX EX (ttl)`. This atomic operation ensures that even under extreme concurrency, a single `jti` cannot be validated twice.

### Persistent Client Registry
Authentications are verified against an async SQLAlchemy database using Bcrypt for secret hashing, preventing data leakage in case of DB snapshots being compromised.

---

## 4. Operational Readiness
- **Dockerized Stack**: Gateway + Redis + Prometheus + Grafana.
- **CI/CD**: Automated GitHub Actions validating every push (65 tests).
- **Secrets Management**: Fail-fast environment validation with `pydantic-settings`.
