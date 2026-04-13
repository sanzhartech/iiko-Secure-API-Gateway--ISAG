# ISAG — iiko Secure API Gateway

![CI Status](https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-/actions/workflows/ci.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**ISAG (iiko Secure API Gateway)** — это защищенный высокопроизводительный обратный прокси-сервер, разработанный для безопасной интеграции с iiko API. Система реализует модель Zero-Trust и обеспечивает глубокую эшелонированную защиту (Defense-in-Depth) для внешних запросов.

---

## 🚀 Основные возможности (Features)

- 🔒 **RS256 JWT Authentication**: Строгая проверка подписей и Payload (iss, aud, sub). Поддержка бесшовной ротации ключей через `KID`.
- 🔄 **Replay Protection**: Защита от повторных атак с использованием JTI (JWT ID) и атомарных операций в Redis.
- 🚦 **Distributed Rate Limiting**: Гибкие лимиты запросов на уровне IP и User ID, синхронизированные между экземплярами шлюза через Redis.
- 🔐 **RBAC (Role-Based Access Control)**: Проверка прав доступа клиента перед проксированием запроса к iiko.
- 🏗 **Secure Proxy Forwarding**: Автоматическое удаление опасных заголовков, подмена клиентских токенов на внутренние API-ключи iiko и защита от SSRF.
- 🛡 **Path Traversal Protection**: Санитайзер путей для предотвращения попыток доступа к скрытым ресурсам.
- 📈 **Full Observability**: Встроенный экспорт метрик в Prometheus и готовый дашборд в Grafana.

---

## 🏗 Архитектура (Architecture)

Проект построен на современном стеке технологий, ориентированном на безопасность и масштабируемость:

- **Backend**: FastAPI (Python 3.12) — асинхронный и высокопроизводительный.
- **Security Store**: Redis — используется для хранения JTI (защита от повторов) и счетчиков лимитов.
- **Database**: SQLAlchemy 2.0 + SQLite (Async) — хранение данных клиентов и политик доступа.
- **Observability**: Prometheus (сбор метрик) + Grafana (визуализация).
- **Containerization**: Docker & Docker Compose.

---

## 🛡 Security Pipeline (Stage-by-Stage)

Каждый запрос проходит через 9 стадий проверки в строгом порядке (LIFO Stack):

1️⃣ **TLS Termination** (на уровне внешнего прокси/LB).  
2️⃣ **Request Size Validation**: Блокировка слишком тяжелых Payload.  
3️⃣ **Rate Limiting**: Проверка лимитов (IP/User).  
4️⃣ **JWT Validation**: Проверка подписи RS256, срока действия и эмитента.  
5️⃣ **Replay Protection**: Проверка уникальности JTI в Redis.  
6️⃣ **RBAC Authorization**: Проверка ролей для целевого ресурса.  
7️⃣ **Secure Proxy Forwarding**: Мутация заголовков и маршрутизация.  
8️⃣ **Audit Logging**: Запись события в структурированный JSON-лог.  
9️⃣ **Response Filtering**: Удаление из ответа технических заголовков (`Server`, `X-Powered-By`).

---

## 🛠 Быстрый старт (Quickstart)

### 1. Подготовка окружения
Клонируйте репозиторий и создайте файл `.env` из примера:
```bash
git clone https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-.git
cd iiko-Secure-API-Gateway--ISAG-
cp backend/.env.example backend/.env
```

### 2. Генерация RSA-ключей
Для работы JWT необходимо сгенерировать пару ключей:
```bash
cd backend
python scripts/generate_keys.py
cd ..
```

### 3. Запуск всего стека
```bash
docker-compose up -d --build
```

После запуска сервисы будут доступны по адресам:
- **API Gateway**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (логин: `admin`, пароль: `isag-grafana-2024`)

---

## 🧪 Тестирование и Нагрузка

### Запуск Unit-тестов:
```bash
cd backend
pytest tests/ -v
```

### Запуск стресс-теста (симуляция атак):
```bash
python scripts/stress_test.py --url http://localhost:8000 --duration 120
```

---

## 📈 Мониторинг

Дашборд Grafana (ISAG Dashboard) предоставляет визуализацию:
- **RPS (Requests per second)** по кодам ответа.
- **Latency P95/P99** (задержка проксирования).
- **Security Block Distribution**: распределение причин блокировок (rate_limit, replay_attack, invalid_token).

---
**Author**: Karzhaubayev Sanzhar  
**Security Level**: Production-Oriented / Zero-Trust Model
