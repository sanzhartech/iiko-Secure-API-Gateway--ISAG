# ISAG — Code Structure & Module Architecture

## 1. Architectural Patterns
The iiko Secure API Gateway is built using a **Modular Layered Architecture** with a focus on **Dependency Injection (DI)** and **Fail-Closed Security**.

### Middleware Registration (LIFO Strategy)
FastAPI/Starlette executes middleware in a "Last-In-First-Out" (LIFO) stack.
- **Outermost Layers**: Low-cost, high-volume rejection (Request Size, Rate Limiting).
- **Innermost Layers**: High-fidelity auditing and business-logic filtering (Metrics, Response Filtering).

---

## 2. Core Modules

### 🛠️ Core Infrastructure (`app/core/`)
- **`config.py`**: Strict Pydantic-settings validation.
- **`redis.py`**: Async connection pool to Redis.
- **`metrics.py`**: Prometheus collectors with Cardinality Normalization.
- **`hashing.py`**: Bcrypt password hashing and `dummy_verify` logic.

### 🛡️ Security Logic (`app/security/`)
- **`jwt_validator.py`**: RS256 verification + **Token Type Enforcement** (`access` vs `refresh`) + **Key Rotation**.
- **`jti_store.py`**: Replay Protection engine using Redis atomic operations.
- **`rbac.py`**: Role-Based Access Control mapping roles to discrete permissions.

### 🗄️ Database Layer (`app/db/` & `app/models/`)
- **`db/engine.py`**: Async SQLAlchemy engine and session management.
- **`models/client.py`**: `GatewayClient` entity (SQLAlchemy/Pydantic).

### 🚦 Middlewares (`app/middleware/`)
- **`metrics.py`**: Observability injection.
- **`rate_limiter.py`**: SlowAPI + Redis distributed limiter.
- **`secure_headers.py`**: HSTS, CSP, and XSS transport protections.

### 🔄 Proxy Engine (`app/services/`)
- **`iiko_client.py`**: Async, streaming reverse proxy with path traversal protection.
- **`client_service.py`**: Registry lookup logic for authenticated clients.

---

## 3. Dependency Injection Graph
1.  **Transport Check**: (Secure Headers Middleware)
2.  **Rate Limit Check**: (SlowAPI Middleware)
3.  **Auth Gating**: `get_current_claims` -> `JWTValidator` (JWT + JTI + Type Check).
4.  **Client Registry**: `get_client_by_id` -> Verifies client is active in DB.
5.  **RBAC Gating**: `require_permissions` -> Validates Roles.
6.  **Proxy Forwarding**: `IikoClient` (streaming response).
