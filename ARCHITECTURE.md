# ISAG — Technical Architecture & Security Analysis

## 1. Architectural Philosophy: Hardened Proxy

**iiko Secure API Gateway (ISAG)** is designed as an asynchronous, non-buffering security middleware. For my diploma defense, the system represents a modern implementation of the **Defense-in-Depth** and **Zero-Trust** security models.

---

## 2. Integrated Security Pipeline (9 Stages)

The core logic resides in the **LIFO Middleware Stack**. By registering middlewares in a specific sequence, we ensure that every request undergoes a mandatory, multi-layered verification before hitting the expensive proxy logic.

| Stage | Component | Category | Purpose |
| :--- | :--- | :--- | :--- |
| **1** | **TLS Termination** | Transport | Enforced externally (Docker/LB) + `SecureHeadersMiddleware`. |
| **2** | **DoS Protection** | Resource | `RequestSizeValidatorMiddleware` (Max 10MB rejection). |
| **3** | **Rate Limiting** | Abuse | `SlowAPIMiddleware` (Per-IP / Per-User distributed limits). |
| **4** | **CORS Gating** | Origin | `CORSMiddleware` (Strict origin allowlist). |
| **5** | **Forensics** | Audit | `AuditLogMiddleware` (Structured JSON logging of metadata). |
| **6** | **Telemetry** | Observation | `MetricsMiddleware` (Prometheus instrumentation). |
| **7** | **JWT RS256** | Identity | `JWTValidator` (Signature & Claim verification + Type enforcement). |
| **8** | **Replay Protection** | State | `JTIStore` (Atomic JTI blacklist in Redis). |
| **9** | **RBAC Authorization**| AuthZ | `require_permissions` (Fine-grained role validation). |

---

## 3. Deep-Dive: Key Security Mechanisms

### 🔑 Zero-Downtime Key Rotation (RS256)
The gateway supports seamless rotation of RSA public keys without service interruption. 
- **Header Injection**: Clients must include the `kid` (Key ID) field in the JWT header.
- **Dynamic Mapping**: `JWTValidator` performs an O(1) lookup in `public_keys.json`.
- **Backward Compatibility**: If `kid` is missing, the gateway falls back to the default active key.

### 🛡️ Token Type Separation (Access vs. Refresh)
To prevent privilege escalation via leaked refresh tokens, ISAG enforces strict type separation:
- **Access Tokens**: Short-lived, carry `type: access` and `roles`. Required for all `/api/*` routes.
- **Refresh Tokens**: Long-lived, carry `type: refresh`. Only accepted at `/auth/refresh`.
- **Fail-Closed Validation**: The `JWTValidator` rejects tokens if the `type` claim does not match the expected context.

### 🗄️ Secure Client Registry (Bcrypt + DB)
Authentication is backed by a persistent SQLite/PostgreSQL store using SQLAlchemy 2.0.
- **One-Way Hashing**: Client secrets are never stored in plaintext; `bcrypt` is used for salted hashing.
- **Timing Attack Mitigation**: `dummy_verify()` is executed even when a client ID is not found, ensuring consistent response times and preventing client enumeration via timing oracles.

### 🛡️ Atomic Replay Protection (Redis SET NX EX)
To prevent **Race Conditions** in replay attacks, ISAG uses an atomic Redis primitive:
```python
# app/security/jti_store.py
success = await self._redis.set(name=key, value="1", ex=ttl, nx=True)
```
- **NX (Not eXists)**: The key is set *only* if it is currently absent.
- **EX (Expiration)**: The entry expires automatically when the token dies.
If `success` is False, the request is immediately rejected.

---

## 4. Observability & Telemetry

### Prometheus Cardinality Control
ISAG solves "Cardinality Explosion" in `app/middleware/metrics.py` by **Route Normalization**:
- Path `/api/v1/orders/123` is mapped to **`/api/{path}`** as a label.
- This ensures the metric store remains stable regardless of the number of unique resources accessed.

### Grafana Visualization
The system includes a pre-provisioned dashboard that visualizes the **Three Security Quadrants**:
1. **Throughput**: Valid requests (HTTP 2xx).
2. **Abuse**: Rate limited requests (HTTP 429).
3. **Attacks**: Unauthorized (401), Forbidden (403), and Replay events.
