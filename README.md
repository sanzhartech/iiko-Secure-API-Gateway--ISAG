# ISAG — iiko Secure API Gateway

![CI Build](https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**ISAG (iiko Secure API Gateway)** — это асинхронный высокопроизводительный обратный прокси-сервер, разработанный для глубокой защиты интеграций с iiko API. Система реализует модель **Zero-Trust** и обеспечивает эшелонированную безопасность по принципу **Defense-in-Depth**.

---

## 🛡️ Security Pipeline (9 Stages)

Каждый запрос проходит через строго детерминированный пайплайн (LIFO Middleware Stack):

1.  **Transport Security**: HSTS, CSP, XSS protection.
2.  **Request Size Gating**: Отсечка Payload > 10MB (DoS mitigation).
3.  **Distributed Rate Limiting**: Троттлинг на базе Redis (IP/User/API).
4.  **CORS Enforcement**: Строгий контроль источников запроса.
5.  **Audit Logging**: Сбор метаданных для форензики.
6.  **Telemetry**: Prometheus-инструментация с нормализацией путей.
7.  **JWT RS256 Validation**: Криптографическая проверка подписи и Identity.
8.  **Atomic Replay Protection**: Блокировка повторных атак через Redis JTI Store.
9.  **RBAC Authorization**: Проверка прав доступа в реальном времени.

---

## 🏗️ Технологический стек

- **Backend**: FastAPI (Python 3.12) — High-performance async core.
- **State Store**: Redis (Sentinel/Cluster ready) — JTI Registry & Rate Limits.
- **Observability**: 
  - **Prometheus**: Сбор метрик без Cardinality Explosion.
  - **Grafana**: Визуализация атак, задержек и нагрузки.
- **Infrastructure**: Docker & Docker Compose (Full-stack orchestration).

---

## 🛠️ Быстрый старт (Quickstart)

### 1. Подготовка
```bash
git clone https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-.git
cd iiko-Secure-API-Gateway--ISAG-
cp backend/.env.example backend/.env
```

### 2. Генерация ключей
```bash
python scripts/generate_keys.py
```

### 3. Запуск
```bash
docker-compose up -d --build
```

---

## 📈 Мониторинг и Стресс-тесты

Для демонстрации защитных механизмов (429 Too Many Requests, 401 Unauthorized, Replay detection) используйте встроенный скрипт:
```bash
python scripts/stress_test.py --url http://localhost:8000
```
Затем откройте **Grafana** (`http://localhost:3000`), чтобы увидеть визуализацию заблокированных атак в реальном времени.

---

## 🔗 Документация (Deep Dive)
- 📗 [Architecture Deep-Dive](file:///d:/Desktop/%D0%94%D0%B8%D0%BF%D0%BB%D0%BE%D0%BC%D0%BA%D0%B0%20-%20iiko%20Secure%20API%20Gateway%20%28ISAG%29/ARCHITECTURE.md)
- 📘 [Testing & Verification Report](file:///d:/Desktop/%D0%94%D0%B8%D0%BF%D0%BB%D0%BE%D0%BC%D0%BA%D0%B0%20-%20iiko%20Secure%20API%20Gateway%20%28ISAG%29/TESTING_REPORT.md)
- 📙 [API Specification](file:///d:/Desktop/%D0%94%D0%B8%D0%BF%D0%BB%D0%BE%D0%BC%D0%BA%D0%B0%20-%20iiko%20Secure%20API%20Gateway%20%28ISAG%29/backend/API_SPEC.md)
- 🏴 [Future Roadmap](file:///d:/Desktop/%D0%94%D0%B8%D0%BF%D0%BB%D0%BE%D0%BC%D0%BA%D0%B0%20-%20iiko%20Secure%20API%20Gateway%20%28ISAG%29/ROADMAP.md)

---
**Author**: Karzhaubayev Sanzhar  
**Security Level**: Hardened (Level 5)
