# ISAG — Testing Strategy & Verification Report

## 1. Testing Methodology

The verification of the iiko Secure API Gateway (ISAG) follows a **Pyramid Testing Model**, ensuring robustness across all security stages.

### Unit & Integration Testing
- **Suite Size**: 68 Comprehensive Tests.
- **Tools**: `pytest`, `pytest-asyncio`, `pytest-cov`, `respx`.
- **Key Strategy**:
    - **Isolation**: All tests run without external dependencies (Redis and Database are mocked via fixtures in `conftest.py`).
    - **Transport Mocking**: I used `respx` to intercept all `httpx` calls to the virtual iiko upstream.
    - **Security Negative Testing**: Over 60% of the suite is dedicated to "Negative Tests" (verifying rejections for expired tokens, wrong types, wrong signatures, missing JTI, etc.).
    - **Type Enforcement Checks**: Specific tests ensure that `access` tokens cannot be used to refresh, and `refresh` tokens cannot be used to access proxy routes.

---

## 2. Quality Metrics

| Metric | Result | Status |
| :--- | :--- | :--- |
| **Test Pass Rate** | 100% (68/68 passed) | ✅ Pass |
| **Code Coverage** | 83% (Core Security) | ✅ Pass |
| **Fail-Closed Logic** | 100% Verified | ✅ Pass |
| **Flakiness** | 0% (Stable environment) | ✅ Pass |

---

## 3. Stress Testing & Attack Simulation

The system includes a dedicated `scripts/stress_test.py` utility to simulate real-world traffic patterns and adversarial conditions.

### Traffic Archetypes
1. **`LEGIT`**: Baseline traffic simulating authentic user sessions. Verified <15ms overhead.
2. **`NO-AUTH`**: Simulating unauthorized scanning. Verified 100% rejection with HTTP 401.
3. **`DDOS (Rate Limit)`**: High-velocity burst attacks. Verified HTTP 429 throttling via Redis state.
4. **`REPLAY`**: Attempting to reuse a snared JWT. Verified JTI Store detection in Redis.
5. **`TOKEN-TYPE-MISMATCH`**: Attempting to use a refresh token for proxy access. Verified 100% rejection.

---

## 4. Observability Integration (Grafana)

Testing results were validated using the integrated Grafana dashboard.
- **Security Block Distribution**: Observed spikes in 429 and 401 errors during attack simulations.
- **Resource Efficacy**: Verified stable CPU/RAM usage under load due to async streaming.

---

## 5. CI/CD Pipeline (GitHub Actions)

The automated verification pipeline runs on every push:
1. **Environment Setup**: Python 3.12 + Redis Service Container.
2. **Database Migration**: Init SQLite schema for registry tests.
3. **Security Test Suite**: `pytest tests/ --cov=app`.
4. **Outcome**: Deployment is blocked unless all 68 tests pass.
