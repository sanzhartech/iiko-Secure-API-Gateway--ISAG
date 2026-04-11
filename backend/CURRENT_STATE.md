# Current State

## 1. What is Implemented and Working
- **Core Proxy Engine (`IikoClient`)**: Fully asynchronous, non-buffering streaming proxy for GET, POST, PUT, PATCH, and DELETE methods. Optimal connection pooling (max 500 connections, 100 keepalive).
- **Security Middlewares**: Audit logs, CORS, and Secure HTTP Headers are active.
- **Rate Limiting Engine**: `SlowAPI` is fully integrated, reading IP-level limits from `.env`. Endpoints have specific limits (`10/minute` for auth, `50/minute` for proxy).
- **JWT Authentication Flow**:
  - `POST /auth/token` endpoint issues RS256 tokens.
  - In-memory RSA key caching mechanism exists to prevent filesystem I/O per request.
  - Multi-key rotation support via `kid` in the token header.
  - Clock skew is hard-capped (max 300s).
- **RBAC Enforcement**: The proxy routes require either `PROXY_READ` (GET) or `PROXY_WRITE` (POST/PUT/etc.) permissions derived from token claims.
- **Error Handling**: Exception handlers gracefully mask upstream failures and unexpected errors, preventing stack-trace leaks.

## 2. What is Partially Implemented (Mocked)
- **Client Registry**: The `/auth/token` endpoint currently uses a mocked dictionary `_get_client_registry()` to validate `client_id` and `client_secret`.
  - *Current Behavior*: Hardcoded `"demo-client"` mapped to `settings.gateway_client_secret` (cleartext).
  - *Target Behavior*: Needs an async DB lookup, with bcrypt-hashed secrets and account lockout after N failures.

## 3. What Still Needs to be Done
- **Refresh Token Flow (`/auth/refresh`)**: The `.env` variables contain `JWT_REFRESH_TOKEN_EXPIRE_DAYS`, but the actual endpoint to exchange a refresh token for a new access token does not exist yet.
- **Database Integration**: Set up async SQLAlchemy (or equivalent) to manage Gateway Clients, Roles, and potentially Audit Logs.
- **Dockerization**: The repository lacks a `Dockerfile` and `docker-compose.yml` for production deployments.
- **Comprehensive Test Coverage Run**: Confirm all `pytest` suites pass reliably, especially testing the exact fail-closed constraints.
