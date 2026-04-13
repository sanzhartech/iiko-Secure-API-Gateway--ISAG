# ISAG — API Specification & Interface Control

## 1. Authentication Layer
All protected endpoints require an RS256-signed JWT access token in the standard `Authorization: Bearer <token>` header.

### [POST] /auth/token
Exchange client credentials for a token pair.
- **Access Control**: Public (Rate limited).
- **Rate Limit**: **10 requests / 60s**.
- **Request**: `{ "client_id": "...", "client_secret": "..." }`
- **Response**: `{ "access_token": "...", "refresh_token": "...", "expires_in": 900 }`

### [POST] /auth/refresh
Obtain a new access token using a valid refresh token.
- **Access Control**: Token-based.
- **Rate Limit**: **10 requests / 60s**.
- **Security**: Validates that the token sub-type is `refresh`.

---

## 2. Secure Proxy Services (Upstream)
All proxy endpoints are subject to mandatory JWT signature verification, JTI replay protection, and RBAC authorization.

### [ANY] /api/{path:path}
Securely forwards requests to the upstream iiko API.
- **Auth**: Mandatory Bearer JWT.
- **RBAC Roles**: 
  - `GET`: Requires `proxy:read` permission.
  - `POST/PUT/DELETE`: Requires `proxy:write` permission.
- **Rate Limit**: **50 requests / 60s** (Distributed via Redis).
- **Path Sanitization**: Rejects `..` sequences to prevent Path Traversal.

---

## 3. Observability & System
These endpoints provide telemetry and health data for orchestration (K8s) and monitoring (Prometheus).

### [GET] /metrics
Exports system telemetry in Prometheus text format.
- **Access Control**: Unauthenticated (Recommended for internal VPC scraping only).
- **Tags**: Observability.
- **Included Metrics**:
  - `isag_requests_total`: Request count by status/method/endpoint.
  - `isag_request_latency_seconds`: Latency histogram.
  - `isag_blocked_requests_total`: Security events count (rate_limit, replay, etc.).

### [GET] /health
Basic liveness probe.
- **Access Control**: Public.
- **Response**: `{"status": "ok"}`

### [GET] /ready
Readiness probe for K8s lifecycle management.
- **Access Control**: Public.
- **Response**: `{"status": "ready"}`
