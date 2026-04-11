# Project File Tree

```text
backend/
├── app
│   ├── api
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── proxy.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── middleware
│   │   ├── __init__.py
│   │   ├── rate_limiter.py
│   │   └── secure_headers.py
│   ├── models
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas
│   │   ├── __init__.py
│   │   └── token.py
│   ├── security
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── jwt_validator.py
│   │   └── rbac.py
│   ├── services
│   │   ├── __init__.py
│   │   └── iiko_client.py
│   ├── __init__.py
│   └── main.py
├── keys
│   ├── .gitkeep
│   └── public_keys.json.example
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_jwt.py
│   ├── test_proxy.py
│   ├── test_rate_limit.py
│   └── test_rbac.py
├── vscode
│   └── settings.json
├── .coverage
├── .env
├── .env.example
├── API_SPEC.md
├── CODE_STRUCTURE.md
├── CURRENT_STATE.md
├── generate_tree.py
├── NEXT_TASKS.md
├── PROJECT_CONTEXT.md
├── pyproject.toml
├── requirements.txt
├── Логическая архитектура backend.txt
└── Формулировка для диплома.txt
```
