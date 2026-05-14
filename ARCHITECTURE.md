# ISAG — Technical Architecture & Security Analysis

## 1. Architectural Philosophy: Hardened Proxy

**iiko Secure API Gateway (ISAG)** is designed as an asynchronous, non-buffering security middleware. For my diploma defense, the system represents a modern implementation of the **Defense-in-Depth** and **Zero-Trust** security models.

---

## 2. Integrated Security Pipeline (9 Stages)

The core logic resides in a hybrid architecture of **FastAPI Middlewares** and **Security Dependencies**. This ensures that every request undergoes a mandatory, multi-layered verification.

| Stage | Component | Category | Purpose |
| :--- | :--- | :--- | :--- |
| **1** | **TLS/Headers** | Transport | Enforced via `SecureHeadersMiddleware` (HSTS, CSP, XSS). |
| **2** | **DoS Protection** | Resource | `RequestSizeValidatorMiddleware` (Max 10MB rejection). |
| **3** | **Rate Limiting** | Abuse | `SlowAPIMiddleware` (Redis-backed distributed limits). |
| **4** | **CORS Gating** | Origin | `CORSMiddleware` (Strict origin allowlist). |
| **5** | **Forensics** | Audit | `AuditLogMiddleware` (Historical request tracking). |
| **6** | **Telemetry** | Observation | `MetricsMiddleware` (Prometheus instrumentation). |
| **7** | **JWT RS256** | Identity | `JWTValidator` (Signature & Claim verification). |
| **8** | **Replay Protection** | State | `JTIStore` (Atomic JTI blacklist in Redis). |
| **9** | **RBAC Authorization**| AuthZ | `require_permissions` (Fine-grained role validation). |

---

## 3. Deep-Dive: Key Security Mechanisms

### 🔑 Zero-Downtime Key Rotation (RS256)
The gateway supports seamless rotation of RSA public keys without service interruption. 
- **Header Injection**: Clients include the `kid` (Key ID) field in the JWT header.
- **Dynamic Mapping**: `JWTValidator` performs an O(1) lookup in `public_keys.json`.

### 🛡️ Token Type Separation (Access vs. Refresh)
To prevent privilege escalation, ISAG enforces strict type separation:
- **Access Tokens**: Required for all `/api/*` routes.
- **Refresh Tokens**: Only accepted at `/auth/refresh` for rotation.

### 👑 Admin Management Hub
A dedicated React-based dashboard provides full visibility into the gateway's operation:
- **Kill-Switch**: Instant global denial of service via a Redis "global_deny" flag.
- **Partner Hub**: A wizard-driven interface for onboarding third-party aggregators.
- **Real-time Stats**: Aggregated metrics from the audit logs and Prometheus.

---

## 4. Observability & Telemetry

### Prometheus & Path Normalization
ISAG solves "Cardinality Explosion" by **Route Normalization**:
- Paths like `/api/v1/orders/123` are normalized to **`/api/{path}`** as a label.
- This ensures stable metrics regardless of the number of unique resources.

### Grafana Visualization
The system includes pre-provisioned dashboards visualizing:
1. **Security Health**: Blocked vs. Allowed traffic.
2. **System Efficacy**: Latency, CPU, and Memory usage.
3. **Attack Analysis**: Patterns of unauthorized and replay attempts.
