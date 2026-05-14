# ISAG — API Specification & Interface Control

## 1. Authentication Layer
All protected endpoints require an RS256-signed JWT access token in the standard `Authorization: Bearer <token>` header.

### [POST] /auth/token
Exchange client credentials for a token pair.
- **Access Control**: Public (Rate limited).
- **Request**: `{ "client_id": "...", "client_secret": "..." }`
- **Response**: `{ "access_token": "...", "refresh_token": "...", "expires_in": 900 }`

### [POST] /auth/refresh
Obtain a new access token pair using a valid refresh token.
- **Security**: Validates `refresh` type + re-verifies client in DB + Rotation.

---

## 2. Secure Proxy Services (Upstream)
### [ANY] /api/{path:path}
Securely forwards requests to the upstream iiko API.
- **Auth**: Mandatory Bearer JWT (Type: `access`).
- **Protection**: JTI Replay Protection + RBAC + Rate Limiting.

---

## 3. Admin & Control API
Restricted to clients with the `admin` role.

### [GET] /admin/stats
Returns real-time analytics digest (Total requests, Error rate, Latency, Partner breakdown).

### [POST] /admin/kill-switch
Toggle the global emergency shutdown.
- **Payload**: `{"active": true/false}`

### [GET] /admin/clients
List all registered partner integrations and their status.

### [POST] /admin/clients
Onboard a new partner (Generates strong RSA-compatible secret).

### [GET] /admin/logs
Paginated audit logs of all security-critical events.

---

## 4. Observability & System
### [GET] /metrics
Prometheus telemetry export (Requests, Latency, Security Events).

### [GET] /health
Liveness probe: `{"status": "healthy"}`.

### [GET] /ready
Readiness probe for K8s lifecycle.
