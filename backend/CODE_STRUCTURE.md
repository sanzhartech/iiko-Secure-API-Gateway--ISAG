# ISAG — Code Structure & Module Architecture

## 1. Architectural Patterns
The iiko Secure API Gateway is built using a **Modular Layered Architecture** with a focus on **Dependency Injection (DI)** and **Fail-Closed Security**.

### Middleware Registration (LIFO Strategy)
FastAPI/Starlette executes middleware in a "Last-In-First-Out" (LIFO) stack relative to the registration order in `app/main.py`.
- **Outermost Layers**: Responsible for low-cost, high-volume rejection (Secure Headers, Request Size, Rate Limiting).
- **Innermost Layers**: Responsible for high-fidelity auditing and business-logic filtering (Metrics, Response Filtering).

---

## 2. Core Modules

### 🛠️ Core Infrastructure (`app/core/`)
- **`config.py`**: Strict Pydantic-settings validation. Rejects application startup if security configurations are weak (e.g., short secrets) or missing.
- **`redis.py`**: Manages the asynchronous connection pool to the Redis cluster.
- **`metrics.py`**: Defines Prometheus collectors (Counter, Histogram) and handles **Cardinality Normalization** logic to prevent metrics storage bloat.

### 🛡️ Security Logic (`app/security/`)
- **`jwt_validator.py`**: Handles RS256 signature verification. Implements **Key Rotation** by dynamically selecting public keys from a JSON registry based on the `kid` header.
- **`jti_store.py`**: The stateful engine for **Replay Protection**. Uses Redis atomic `SET NX EX` to prevent race conditions during token verification.
- **`rbac.py`**: Role-Based Access Control dependency. Maps client roles to discrete permissions (`proxy:read`, `proxy:write`).

### 🚦 Middlewares (`app/middleware/`)
- **`metrics.py`**: Injects observability logic into the lifecycle. Infers security block reasons (e.g., `rate_limit`, `replay_attack`) from response status/body markers.
- **`rate_limiter.py`**: Distributed rate limiting implementation using SlowAPI + Redis.

### 🔄 Proxy Engine (`app/services/`)
- **`iiko_client.py`**: An asynchronous, streaming reverse proxy. Implements **Path Traversal Protection** (sanitizing `..` sequences) and ensures zero-buffering for large payloads.

---

## 3. Dependency Injection Graph
ISAG heavily uses FastAPI's `Depends` for security gating:
1.  **Transport Check**: (Secure Headers Middleware)
2.  **Rate Limit Check**: (SlowAPI Middleware)
3.  **Auth Gating**: `get_current_claims` -> Validates JWT + JTI.
4.  **RBAC Gating**: `require_permissions` -> Validates Roles.
5.  **Proxy Forwarding**: `IikoClient` (after all gates are passed).
