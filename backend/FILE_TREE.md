# ISAG — Final Directory Structure

```text
iiko-Secure-API-Gateway-ISAG/
├── .github/workflows/          # [CI/CD] Automated Testing Pipeline
│   └── ci.yml                  # GitHub Actions: Pytest + Redis
├── backend/                    # Core Gateway Application
│   ├── app/                    # Main Application Logic
│   │   ├── api/                # [REST] Controllers & Route Definitions
│   │   ├── core/               # [Shared] Config, Redis, Metrics, Logging
│   │   ├── db/                 # [DB] Engine & Session Logic
│   │   ├── middleware/         # [Pipeline] Security & Observation Middlewares
│   │   ├── models/             # [Entity] User & Client Definitions
│   │   ├── schemas/            # [DTW] Pydantic Validation Models
│   │   ├── security/           # [Auth] JWT, JTI (Replay), RBAC logic
│   │   ├── services/           # [Integration] Iiko Upstream Client
│   │   └── main.py             # App Factory & Middleware Orchestration
│   ├── keys/                   # [Security] RSA Private/Public Key Registry
│   ├── scripts/                # [Utility] Generation & Stress-test scripts
│   ├── tests/                  # [QA] Comprehensive 65-Test Suite
│   ├── .env                    # Production/Local Environment Configuration
│   ├── CODE_STRUCTURE.md       # Technical module breakdown
│   ├── API_SPEC.md             # Interface Contract
│   └── requirements.txt        # Production dependencies
├── infrastructure/             # Orchestration & Monitoring Config
│   ├── grafana/                # Grafana Dashboards & Provisioning
│   └── prometheus/             # Prometheus Scrapers & Data Sources
├── scripts/                    # Root Utility Scripts
│   ├── stress_test.py          # Attack Simulation Engine
│   └── generate_keys.py        # RS256 Key Pair Generator
├── docker-compose.yml          # Full-Stack Orchestration (Gateway+Redis+Monitoring)
├── ARCHITECTURE.md             # Deep Technical Analysis
├── README.md                   # Project Showcase & Quickstart
├── ROADMAP.md                  # Future Development & Scaling Vectors
└── TESTING_REPORT.md           # Verification & Metric Proof
```
