# ISAG — Security Controls & Specifications

This document outlines the security architecture, threat model, and technical controls implemented in the **iiko Secure API Gateway (ISAG)** to ensure a Zero-Trust environment.

---

## 1. Cryptographic Authentication & Authorization

ISAG uses JSON Web Tokens (JWT) signed with the asymmetric **RS256** algorithm. Symmetric signing algorithms (like HS256) or unsigned tokens (`alg: none`) are strictly rejected.

### Key Rotation & Key ID (KID)
*   **Decoupled Verification**: The gateway checks the JOSE header of incoming tokens for the `kid` (Key ID) parameter.
*   **Key Store mapping**: It retrieves the corresponding public key from `keys/public_keys.json`.
*   **Zero-Downtime Rotation**: New public keys can be appended to the JSON registry. The authorization endpoint can immediately begin issuing tokens signed with the new key while older active tokens continue to validate against their corresponding key until expiration.

### Token Type Separation
To prevent privilege escalation, ISAG enforces strict separation between token types via the custom `type` claim:
*   **Access Token**: Carry `type: "access"` and client roles. Accepted only at `/api/*` proxies. Rejection occurs if presented to `/auth/refresh`.
*   **Refresh Token**: Carry `type: "refresh"` and omit roles. Valid only at `/auth/refresh` for rotation. Rejected if presented to `/api/*` proxies.

---

## 2. Stateful Replay Protection (JTI Store)

ISAG mitigates token capture attacks using stateful Redis-backed JWT ID (`jti`) blacklisting.

*   **Atomic SET NX**: During a token exchange, the token's `jti` is stored in Redis using an atomic `SET key timestamp NX EX expiry` command. If the key exists, the request is flagged as a potential replay.
*   **Grace Window (Parallel Races)**: To handle legitimate browser double-requests or retry packets on slow connections, ISAG allows a configurable 2-second grace period. The first duplicate request increments a grace key (`isag:jti:grace:{jti}`). Any subsequent reuse, or reuse outside the 2-second window, triggers an immediate `HTTP 401 Unauthorized` block.

---

## 3. Input Validation & Injection Mitigation

*   **Pydantic Schema Validation**: All incoming requests are validated against strict Pydantic schemas. Schemas use `model_config = ConfigDict(extra="forbid")` to block undeclared payload parameters.
*   **Payload Size Ceiling**: To prevent buffer exhaustion and resource denial-of-service (DoS) attacks, the outermost middleware (`RequestSizeValidatorMiddleware`) rejects any payload larger than **10MB** immediately before parsing.
*   **Injection Protections**: FastAPI's type checks and SQLAlchemy's parameterized queries prevent SQL injection, path traversal, and JSON injection attacks.

---

## 4. Abuse Protection & Admin Controls

### Rate Limiting
ISAG uses a distributed rate-limiter backed by Redis:
*   **IP-Based Limiting**: Tracks requests by remote IP (`RATE_LIMIT_PER_IP` defaults to `100/minute`).
*   **User-Based Limiting**: Tracks requests by client ID (`RATE_LIMIT_PER_USER` defaults to `50/minute`) once the JWT signature is verified.
*   **Auth Endpoint Throttling**: The `/auth/token` and `/auth/refresh` endpoints are capped at `10/minute` to mitigate brute-force and credential-stuffing attacks.

### Global Kill-Switch
*   Administrators can toggle a global emergency shutdown via `POST /admin/kill-switch`.
*   When active, a `global_deny` key is set in Redis. The gateway immediately fails-closed, rejecting all non-admin proxy requests with an `HTTP 503 Service Unavailable` response.

---

## 5. Security Audit Logging

All security-sensitive operations are captured by the database-backed logging engine:
*   **Correlation IDs**: Every request is assigned a unique `X-Request-ID` UUID header to trace actions through the system.
*   **Admin Logs**: Tracks actions (e.g. client creation, status toggles, secret rotation) with timestamp, administrator ID, target ID, and client IP.
*   **Request Logs**: Tracks client request latency, status code, and timestamp for real-time security telemetry.
*   **Credential Masking**: Sensitive headers, JWT tokens, and client secrets are stripped or masked before writing logs to prevent credential leakage.
