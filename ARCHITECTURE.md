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
| **7** | **JWT RS256** | Identity | `JWTValidator` (Signature & Claim verification). |
| **8** | **Replay Protection** | State | `JTIStore` (Atomic JTI blacklist in Redis). |
| **9** | **RBAC Authorization**| AuthZ | `require_permissions` (Fine-grained role validation). |

---

## 3. Deep-Dive: Key Security Mechanisms

### 🔑 Zero-Downtime Key Rotation (RS256)
The gateway supports seamless rotation of RSA public keys without service interruption. 
- **Header Injection**: Clients must include the `kid` (Key ID) field in the JWT header.
- **Dynamic Mapping**: `JWTValidator` performs an O(1) lookup in `public_keys.json`.
- **Backward Compatibility**: If `kid` is missing, the gateway falls back to the default active key, allowing for graceful migration periods.

### 🛡️ Atomic Replay Protection (Redis SET NX EX)
To prevent **Race Conditions** in replay attacks (re-sending the same valid token multiple times in milliseconds), ISAG uses an atomic Redis primitive:
```python
# app/security/jti_store.py
success = await self._redis.set(name=key, value="1", ex=ttl, nx=True)
```
- **NX (Not eXists)**: The key is set *only* if it is currently absent.
- **EX (Expiration)**: The entry expires automatically when the token dies.
If `success` is False, the token has been used in the last `ttl` seconds, and the request is immediately rejected.

### 🚦 Path Traversal Sanitization
To prevent **Local File Inclusion (LFI)** or **SSRF** via proxy path manipulation, the `IikoClient` implements strict pre-normalization sanitization. We intercept `..` sequences in the raw URI *before* `posixpath.normpath` resolves them, ensuring malicious intents are detected and blocked.

---

## 4. Observability & Telemetry

### Prometheus Cardinality Control
A common failure mode in API gateways is "Cardinality Explosion" in Prometheus (creating thousands of unique metric series for unique IDs in paths). 
ISAG solves this in `app/middleware/metrics.py` by **Route Normalization**:
- Path `/api/v1/orders/123` is mapped to **`/api/{path}`** as a label.
- This ensures the metric store remains stable regardless of the number of unique resources accessed.

### Grafana Visualization
The system includes a pre-provisioned dashboard that visualizes the **Three Security Quadrants**:
1. **Throughput**: Valid requests (HTTP 2xx).
2. **Abuse**: Rate limited requests (HTTP 429).
3. **Attacks**: Unauthorized (401), Forbidden (403), and Replay events.
