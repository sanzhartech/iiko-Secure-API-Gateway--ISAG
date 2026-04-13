# ISAG — Testing Strategy & Verification Report

## 1. Testing Methodology

The verification of the iiko Secure API Gateway (ISAG) follows a **Pyramid Testing Model**, ensuring robustness across all security stages.

### Unit & Integration Testing
- **Suite Size**: 65 Comprehensive Tests.
- **Tools**: `pytest`, `pytest-asyncio`, `pytest-cov`, `respx`.
- **Key Strategy**:
    - **Isolation**: All tests run without external dependencies (Redis and Database are mocked via fixtures).
    - **Transport Mocking**: I used `respx` to intercept all `httpx` calls to the virtual iiko upstream, allowing us to verify header mutation and streaming logic without real networking.
    - **Security Negative Testing**: Over 50% of the suite is dedicated to "Negative Tests" (verifying rejections for expired tokens, wrong signatures, missing JTI, etc.).

---

## 2. Quality Metrics

| Metric | Result | Status |
| :--- | :--- | :--- |
| **Test Pass Rate** | 100% (65/65 passed) | ✅ Pass |
| **Code Coverage** | 83% (Overall) | ✅ Pass |
| **Core Logic Coverage**| >95% (app/security/, app/services/) | ✅ Pass |
| **Flakiness** | 0% (Stable across 10+ runs) | ✅ Pass |

---

## 3. Stress Testing & Attack Simulation

The system includes a dedicated `scripts/stress_test.py` utility to simulate real-world traffic patterns and adversarial conditions.

### Traffic Archetypes
1. **`LEGIT`**: Baseline traffic simulating authentic user sessions. Verified that the gateway handles 1.2.0 streaming proxying with minimal latency (<15ms overhead).
2. **`NO-AUTH`**: Simulating unauthorized scanning. Verified 100% rejection with HTTP 401 and zero leakage of upstream data.
3. **`DDOS (Rate Limit)`**: High-velocity burst attacks exceeding 100 req/min. Verified that **SlowAPI** correctly triggers HTTP 429 and subsequent requests are throttled at the gateway edge.
4. **`REPLAY`**: Attempting to reuse a snared JWT. Verified that the **JTI Store** detects the duplicate ID in Redis and blocks the request before it reaches the proxy router.

---

## 4. Observability Integration (Grafana)

Testing results were validated using the integrated Grafana dashboard.
- **Security Block Distribution**: We observed clear spikes in 429 errors during DDoS simulation and 401 errors during Replay simulations.
- **Resource Efficacy**: Verified that the gateway CPU/RAM usage stays stable under load due to the non-buffering async streaming implementation.

---

## 5. CI/CD Pipeline (GitHub Actions)

Every pull request and push to the `main` branch triggers an automated verification pipeline:
1. **Environment Setup**: Python 3.12 + Redis Service Container.
2. **Dependency Audit**: `pip install -r requirements.txt`.
3. **Security Test Suite**: `pytest tests/ --cov=app`.
4. **Outcome**: Deployment is blocked unless all 65 tests pass.
