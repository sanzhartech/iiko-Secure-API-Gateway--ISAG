# ISAG — Testing Strategy & Verification Report

This document details the testing framework, test coverage metrics, and validation strategy used to guarantee the reliability and security of the iiko Secure API Gateway (ISAG).

---

## 1. Testing Methodology

The verification of ISAG follows a strict **Pyramid Testing Model**, focusing heavily on integration-level and negative security testing.

### Unit & Integration Testing
*   **Suite Size**: 70 Comprehensive Automated Tests.
*   **Tools**: `pytest`, `pytest-asyncio`, `pytest-cov`, `respx` (for HTTP transport mocking).
*   **Key Strategies**:
    *   **Isolation**: Tests execute using mocked Redis clients and a local SQLAlchemy SQLite memory database to eliminate external environment state dependencies.
    *   **Upstream Interception**: The `respx` library intercepts all outgoing `httpx` connections to the simulated iiko API, verifying header insertion and stripping.
    *   **Negative Security Testing**: Over 60% of the test suite is dedicated to malicious and malformed input scenarios, such as algorithm confusion, missing claims, expired tokens, invalid keys, and rate limit exhaustion.
    *   **Stateful Controls Verification**: Dynamic tests verify the correctness of the global Kill-Switch, JTI grace-window limits, and SQLAlchemy audit trail recording.

---

## 2. Test Execution & Coverage Metrics

The automated test suite runs in less than 20 seconds. Below are the verified metrics from the latest execution:

| Metric | Result | Status |
| :--- | :--- | :--- |
| **Test Pass Rate** | 100% (70/70 passed) | ✅ Pass |
| **Code Coverage (Overall)** | 76% (1045 statements) | ✅ Pass |
| **Core Security Component Coverage** | 90%+ Average | ✅ Pass |
| **Fail-Closed Logic** | 100% deterministic blocking | ✅ Pass |

### Coverage Breakdown by Component
*   `app/security/jwt_validator.py` — **92%** (Signature, expiry, algorithm checks)
*   `app/security/jti_store.py` — **88%** (Replay protection grace window)
*   `app/security/rbac.py` — **100%** (Role and permission mappings)
*   `app/middleware/rate_limiter.py` — **100%** (SlowAPI integration)
*   `app/middleware/secure_headers.py` — **95%** (HSTS, CSP, XSS headers)
*   `app/middleware/size_validator.py` — **100%** (Request body size ceiling)

---

## 3. Stress Testing & Threat Simulation

The system provides two dedicated scripts to simulate traffic archetypes and stress-test the gateway's defenses under realistic loads.

### A. Stress Test Engine (`scripts/stress_test.py`)
This script simulates multi-threaded concurrent connections representing different traffic archetypes:
1.  **`LEGIT`**: Baseline traffic using valid RS256 keys. Overhead is measured at $<15\text{ms}$.
2.  **`NO-AUTH`**: Requests with missing or malformed headers. Verified $100\%$ blocking rate.
3.  **`DDOS`**: High-frequency request spikes. Verified triggering of `HTTP 429 Too Many Requests`.
4.  **`REPLAY`**: Attempts to reuse a single `jti` refresh token. Verified that second-use within 2 seconds is allowed once (grace), and third-use is blocked.

### B. Live Attack Simulation Demo (`demo_attack.py` or `scripts/demo_attack.py`)
A script designed to showcase the real-time defense response during the diploma presentation:
*   Sends normal requests to show a green "health pulse" on the React dashboard.
*   Sends a burst of requests to trigger rate limiting, producing a red glow in the live telemetry feed.
*   Sends forged tokens showing immediate `UNAUTHORIZED` blocks.

---

## 4. CI/CD Integration

To ensure security settings are never degraded during development, the validation pipeline is automated via **GitHub Actions** on every push to the repository:
1.  **Environment Initialization**: Spins up Python 3.12, PostgreSQL, and Redis service containers.
2.  **Secret Mocking**: Generates temporary RSA private and public keys.
3.  **Database Migration**: Runs SQLAlchemy migrations to create the database schemas.
4.  **Test Suite Execution**: Runs `pytest tests/ --cov=app` to assert 100% pass rates.
5.  **Fail-Secure Guard**: The deployment branch is blocked if any test fails or coverage drops.
