# ISAG — API Specification & Interface Control

This document defines the contract for all API endpoints exposed by the **iiko Secure API Gateway (ISAG)**.

All protected endpoints require an RS256-signed JWT token passed in the `Authorization: Bearer <token>` header.

---

## 1. Authentication Endpoints

### A. Exchange Credentials for Token Pair
*   **Method / Route**: `POST /auth/token`
*   **Access Control**: Public (Rate Limit: 10/minute)
*   **Description**: Exchanges partner client credentials for a JWT access token and a refresh token.
*   **Request Schema**:
    ```json
    {
      "client_id": "string (min 3 chars, max 128)",
      "client_secret": "string (min 8 chars, max 256)"
    }
    ```
*   **Response Schema (200 OK)**:
    ```json
    {
      "access_token": "eyJhbGciOiJSUzI1NiIsImtpZC...",
      "token_type": "bearer",
      "expires_in": 900,
      "refresh_token": "eyJhbGciOiJSUzI1NiIsImtpZC..."
    }
    ```
*   **Errors**:
    *   `401 Unauthorized` (Invalid credentials or inactive client)
    *   `429 Too Many Requests` (Rate limit exceeded)

### B. Renew Access Token via Refresh Token
*   **Method / Route**: `POST /auth/refresh`
*   **Access Control**: Public (Rate Limit: 10/minute)
*   **Description**: Validates the refresh token (signature, expiration, `type: refresh`), performs JTI replay checks, re-verifies that the client is active in the database, and issues a new access/refresh token pair.
*   **Request Schema**:
    ```json
    {
      "refresh_token": "eyJhbGciOiJSUzI1NiIsImtpZC..."
    }
    ```
*   **Response Schema (200 OK)**: Same as `/auth/token`.
*   **Errors**:
    *   `401 Unauthorized` (Invalid token, token type mismatch, expired token, or JTI replay detected)
    *   `429 Too Many Requests` (Rate limit exceeded)

### C. Get Current Client Profile
*   **Method / Route**: `GET /auth/me`
*   **Access Control**: Authenticated (Requires valid access token)
*   **Description**: Verifies the access token and returns client details.
*   **Response Schema (200 OK)**:
    ```json
    {
      "id": "partner-aggregat-1",
      "roles": ["operator"]
    }
    ```

---

## 2. Secure Proxy Services (Upstream Integration)

### Route Proxy Handler
*   **Method / Route**: `[GET|POST|PUT|DELETE|PATCH] /api/{path:path}`
*   **Access Control**: Authenticated (Access token required, role matches requested path)
*   **Description**: Streams requests asynchronously to the upstream iiko API. Strips hop-by-hop headers, masks upstream API keys, and blocks path traversal attempts.
*   **Security Controls**:
    *   JWT Validation (`type: "access"`)
    *   RBAC validation (e.g. requires `proxy:read` or `proxy:write` scopes)
    *   Distributed Rate Limiting (IP and User limits)
    *   Payload size ceiling (max 10MB)

---

## 3. Administrative Management API

Requires the client to have the `admin` role in their access token claims.

### A. Get System Status & Analytics
*   **Method / Route**: `GET /admin/stats`
*   **Description**: Returns real-time metrics and historical logs digest for the admin dashboard.
*   **Response Schema (200 OK)**:
    ```json
    {
      "total_requests": 14205,
      "error_rate": 0.42,
      "avg_latency_ms": 11.2,
      "partner_stats": [
        { "client_id": "client-1", "requests": 8410 },
        { "client_id": "client-2", "requests": 5795 }
      ]
    }
    ```

### B. Toggle Global Emergency Kill-Switch
*   **Method / Route**: `POST /admin/kill-switch`
*   **Description**: Instantly toggles global blocking in Redis. When `active` is true, all non-admin proxy requests return 503.
*   **Request Schema**:
    ```json
    {
      "active": true
    }
    ```
*   **Response Schema (200 OK)**:
    ```json
    {
      "status": "success",
      "kill_switch_active": true
    }
    ```

### C. Create New Partner Integration
*   **Method / Route**: `POST /admin/clients`
*   **Description**: Registers a new partner, generating a cryptographically secure client ID and password.
*   **Request Schema**:
    ```json
    {
      "client_id": "new-partner-delivery",
      "roles": ["operator"],
      "scopes": ["orders:read", "orders:write"],
      "rate_limit": 100
    }
    ```
*   **Response Schema (200 OK)**:
    ```json
    {
      "client_id": "new-partner-delivery",
      "client_secret": "isag_sec_9a8f23b1c...",
      "roles": ["operator"],
      "scopes": ["orders:read", "orders:write"],
      "rate_limit": 100
    }
    ```

### D. Get Audit Logs
*   **Method / Route**: `GET /admin/logs`
*   **Description**: Returns a paginated list of security audit logs.
*   **Response Schema (200 OK)**:
    ```json
    [
      {
        "id": "b182cb04-...",
        "timestamp": "2026-05-30T15:30:00Z",
        "admin_id": "admin",
        "action": "CLIENT_CREATED",
        "target_id": "new-partner-delivery",
        "ip_address": "127.0.0.1"
      }
    ]
    ```

---

## 4. System & Observability Endpoints

### A. Liveness Probe
*   **Method / Route**: `GET /health`
*   **Description**: Verifies the container process is running.
*   **Response (200 OK)**: `{"status": "healthy"}`

### B. Kubernetes Readiness Probe
*   **Method / Route**: `GET /ready`
*   **Description**: Verifies backend connection to DB and Redis.
*   **Response (200 OK)**: `{"status": "ready"}`

### C. Prometheus Exporter
*   **Method / Route**: `GET /metrics`
*   **Description**: Exposes current gateway metrics in standard Prometheus text format. Must be accessible without JWT authentication.
