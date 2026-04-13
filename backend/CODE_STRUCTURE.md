# Hardware Core: ISAG Code Structure

The **iiko Secure API Gateway (ISAG)** architecture is built around a **9-Stage Security Pipeline**. Every request must survive all stages before reaching the iiko upstream.

## The 9-Stage Security Pipeline

| Stage | Name | Implementation Path | Rule Reference |
| :--- | :--- | :--- | :--- |
| **1** | TLS Termination | Infra Layer (Nginx/Traefik) | Rule 8 (HTTPS Only) |
| **2** | Request Size Validation | `app/middleware/size_validator.py` | Rule 12 (DoS Protection) |
| **3** | Rate Limiting | `app/middleware/rate_limiter.py` | Rule 6 (Abuse Protection) |
| **4** | JWT Validation | `app/security/jwt_validator.py` | Rule 3 (Cryptography) |
| **5** | Replay Protection | `app/security/replay.py` | Rule 4 (Zero-Trust) |
| **6** | RBAC Authorization | `app/security/rbac.py` | Rule 15 (Testing Requirements) |
| **7** | Secure Proxy Forwarding | `app/services/iiko_client.py` | Rule 7 (Proxy Hardening) |
| **8** | Audit Logging | `app/security/audit.py` | Rule 11 (Observability) |
| **9** | Response Filtering | `app/middleware/response_filter.py` | Rule 2 (Fail-Closed) |

---

## Directory Layout

```text
backend/
├── app/
│   ├── api/                    # Stage 4 & 6: Entrance & Policy Enforcement
│   │   ├── auth.py             # Token Issuance (RS256)
│   │   └── proxy.py            # Streaming Proxy Endpoints
│   ├── core/                   # System Foundations (Rule 14)
│   │   ├── config.py           # Pydantic Settings & Key Caching (Rule 9)
│   │   ├── hashing.py          # Password Hashing (Bcrypt)
│   │   └── logging.py          # Structured JSON Logging (Rule 11)
│   ├── db/                     # Data Persistence (Post-Mock phase)
│   │   ├── base.py             # SQLAlchemy Base
│   │   └── engine.py           # Async Session Management
│   ├── middleware/             # Fast-fail Pipeline Layers (Rule 8)
│   │   ├── rate_limiter.py     # Stage 3: Rate Limiting
│   │   ├── secure_headers.py   # Transport Security Headers
│   │   ├── size_validator.py   # Stage 2: Request Size Limit
│   │   └── response_filter.py  # Stage 9: Data Leakage Prevention
│   ├── models/                 # Secure Entities
│   │   ├── client.py           # Gateway Client Models
│   │   └── user.py             # User/Sub-account Models (WIP)
│   ├── schemas/                # Input Validation (Rule 5)
│   │   └── token.py            # Strict Pydantic schemas
│   ├── security/               # The "Hardened Core"
│   │   ├── audit.py            # Stage 8: Deep Inspection Logging
│   │   ├── jwt_validator.py    # Stage 4: Cryptographic Verification
│   │   ├── rbac.py             # Stage 6: Identity Management
│   │   └── replay.py           # Stage 5: Nonce/JTI tracking
│   ├── services/               # Internal Integrations
│   │   ├── client_service.py   # Client Registry Logic
│   │   └── iiko_client.py      # Stage 7: Upstream Streaming Proxy
│   └── main.py                 # Lifespan, Exceptions & Pipeline Assembly
├── keys/                       # Secure Key Storage (Rule 3)
├── tests/                      # Mandatory Security Tests (Rule 15)
├── requirements.txt            # Dependency Management
└── .env                        # Configuration (Stricted by Pydantic)
```

## Modular Philosophy

1. **`app/main.py`**: The Orchestrator. Assembles the security pipeline order (LIFO in FastAPI middleware registration).
2. **`app/security/`**: The "Heart". Contains logic that makes decisions based on identity and policy.
3. **`app/middleware/`**: The "Shield". Fast, stateless checks that fail fast under load or attack.
4. **`app/core/`**: The "Engine Room". Provides the necessary utilities (logging, config) to the rest of the app.
