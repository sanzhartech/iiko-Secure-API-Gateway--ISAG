# API Specification

## 1. Authentication Scheme
The gateway uses **Bearer JWT authentication** signed with an RS256 private key. All protected endpoints expect the token in the `Authorization: Bearer <token>` header. Tokens have a short expiry (default 15 minutes).

## 2. Endpoints

### 2.1. Authentication
**Endpoint:** `POST /auth/token`
**Summary:** Exchange client credentials for a JWT access token.
**Rate Limit:** 10 requests / minute.

**Request Body (JSON):**
```json
{
  "client_id": "demo-client",
  "client_secret": "your_strong_gateway_secret"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Error Responses:**
- `401 Unauthorized`: "Invalid credentials" (Note: same response for bad ID or bad secret).
- `429 Too Many Requests`: Rate limit exceeded.

---

### 2.2. Proxy Read (Upstream GET)
**Endpoint:** `GET /api/{path}`
**Summary:** Proxies a GET request to the iiko upstream server at `/{path}`.
**Required Permission:** `PROXY_READ`
**Rate Limit:** 50 requests / minute.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
Streamed exactly from the iiko upstream server, omitting hop-by-hop headers.

---

### 2.3. Proxy Write (Upstream POST, PUT, PATCH, DELETE)
**Endpoint:** `POST /api/{path}` (or PUT/PATCH/DELETE)
**Summary:** Proxies mutating requests to the iiko upstream server.
**Required Permission:** `PROXY_WRITE`
**Rate Limit:** 50 requests / minute.

**Headers:**
- `Authorization: Bearer <token>`

**Body:**
Streamed directly to the upstream iiko server.

**Response:**
Streamed exactly from the iiko upstream server.

---

### 2.4. Health Check
**Endpoint:** `GET /health`
**Summary:** Internal app health check. Excluded from OpenAPI schema.
**Response:** `{"status": "ok"}`
