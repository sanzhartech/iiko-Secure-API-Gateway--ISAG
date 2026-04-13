# Project File Tree

```text
backend/
├── app/
│   ├── api/                    # Stage 4 & 6
│   │   ├── auth.py             # Token Issuance
│   │   ├── proxy.py            # Streaming Proxy
│   │   └── __init__.py
│   ├── core/                   # Engine Room
│   │   ├── config.py           # Settings & Key Cache
│   │   ├── hashing.py          # Bcrypt logic
│   │   ├── logging.py          # JSON Logging
│   │   └── __init__.py
│   ├── db/                     # Stage 3+ (Persistence)
│   │   ├── base.py             # SQLAlchemy Base
│   │   ├── engine.py           # Async Engine
│   │   └── __init__.py
│   ├── middleware/             # Stage 2, 3, 9 (The Shield)
│   │   ├── rate_limiter.py     # Stage 3: Rate Limit
│   │   ├── response_filter.py  # Stage 9: Filter
│   │   ├── secure_headers.py   # HSTS/CSP Headers
│   │   ├── size_validator.py   # Stage 2: Size Limit
│   │   └── __init__.py
│   ├── models/                 # Zero-Trust Entities
│   │   ├── client.py           # Registry Client
│   │   ├── user.py             # User models
│   │   └── __init__.py
│   ├── schemas/                # Strict Validation
│   │   ├── token.py            # JWT Schemas
│   │   └── __init__.py
│   ├── security/               # The Hardened Core
│   │   ├── audit.py            # Stage 8: Audit
│   │   ├── jwt_validator.py    # Stage 4: JWT
│   │   ├── rbac.py             # Stage 6: RBAC
│   │   ├── replay.py           # Stage 5: Replay
│   │   └── __init__.py
│   ├── services/               # Integrations
│   │   ├── client_service.py   # Registry logic
│   │   ├── iiko_client.py      # Stage 7: Upstream
│   │   └── __init__.py
│   ├── main.py                 # Pipeline Assembly
│   └── __init__.py
├── keys/                       # RSA Keys
├── tests/                      # Mandatory Tests
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_jwt.py
│   ├── test_proxy.py
│   ├── test_rate_limit.py
│   └── test_rbac.py
├── .env                        # Configuration
├── CODE_STRUCTURE.md           # Architecture Map
├── FILE_TREE.md                # This file
├── PROJECT_CONTEXT.md          # Domain Context
└── requirements.txt            # Dependencies
```
