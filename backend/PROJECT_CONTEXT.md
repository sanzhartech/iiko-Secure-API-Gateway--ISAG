# PROJECT_CONTEXT: ISAG Architecture & Security Philosophy

The **iiko Secure API Gateway (ISAG)** is implemented as a hardened, high-performance security layer. Operating as an asynchronous reverse proxy, it serves as the single entrance gateway for third-party integrations connecting to the iiko API.

---

## 1. Core Security Philosophies

*   **Defense-in-Depth**: Security controls are stacked in multiple layers. If one layer is bypassed or misconfigured, others (e.g. rate limits, schema validation) catch and block the request.
*   **Fail-Closed**: In any error state (such as missing environment variables, database lockout, or Redis failure), the gateway defaults to denying the request.
*   **Zero-Trust**: Every request is verified using RS256 cryptographic signatures, client active states, and role-based permissions, irrespective of network origin.

---

## 2. Integrated Security Pipeline (9 Stages)

All requests traverse the following pipeline of LIFO middlewares and FastAPI routing dependencies:

1.  **Transport Security (Outermost)**: `SecureHeadersMiddleware` enforces HSTS, CSP, and X-Frame-Options.
2.  **DoS Protection**: `RequestSizeValidatorMiddleware` drops request bodies larger than 10MB immediately.
3.  **Distributed Rate Limiting**: `SlowAPIMiddleware` limits rates per IP and client using Redis.
4.  **CORS Origin Gating**: `CORSMiddleware` filters browser client cross-origin access.
5.  **Audit Logging**: `AuditLogMiddleware` registers transaction correlation IDs and prepares DB logs.
6.  **Telemetry Exporter**: `MetricsMiddleware` registers Prometheus request statistics using URL path-normalization.
7.  **Asymmetric Verification**: `JWTValidator` verifies RS256 token signatures and checks expiration claims.
8.  **Replay Protection**: `JTIStore` checks JWT IDs in Redis with a 2-second grace period (specifically for refresh tokens).
9.  **RBAC Authorization**: FastAPI dependencies verify that roles and scopes match resource permissions.
10. **Response Filtering (Innermost)**: `ResponseFilterMiddleware` sanitizes outgoing headers to prevent information disclosure.

---

## 3. Core Design Decisions

*   **LIFO MiddlewareStack**: Middlewares are executed in reverse registration order. This places low-overhead validations (size validator, IP rate limiter) at the outermost edge, preventing expensive database lookups on DDoS traffic.
*   **Decoupled Secret Storage**: Upstream access tokens (`IIKO_API_KEY`) and client verification keys (`GATEWAY_CLIENT_SECRET`) are separated, preventing client credential exposures from leaking control of the upstream API.
*   **Bcrypt & Constant-Time Mocks**: Partner registry passwords are Bcrypt-hashed. If a client ID is not found, the gateway triggers `dummy_verify()` to simulate a hashing delay, preventing timing side-channel attacks.
