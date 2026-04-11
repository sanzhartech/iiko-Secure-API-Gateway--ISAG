# Архитектура проекта: iiko Secure API Gateway (ISAG)

Этот документ представляет собой полное архитектурное описание проекта ISAG, созданное для быстрого введения в курс дела новых разработчиков (или AI-агентов). Он объединяет текущее состояние кодовой базы, спецификации API, структуру проекта и модель безопасности.

---

## 1. Project Overview (О проекте)
**iiko Secure API Gateway (ISAG)** — это асинхронный высокопроизводительный обратный прокси-сервер (reverse proxy) и слой безопасности (security layer). Система ставится перед целевым (upstream) API iiko, чтобы защитить его от прямого доступа.

**Ключевые цели проекта:**
- **Защита секретов:** Полностью скрыть от конечных клиентов реальный ключ авторизации iiko (`iiko_api_key`) и физический URL бэкенда iikoCloud.
- **Управление доступом (RBAC):** Ограничение прав клиентов на конкретные действия (например, только чтение — GET, или запись — POST/PUT/DELETE).
- **Защита от DDoS и Brute-force:** Ограничение частоты запросов (Rate Limiting) на уровне IP-адресов и конкретных пользователей.
- **Аудит и Наблюдаемость:** Ведение подробного журнала безопасности и логирование чувствительных запросов.
- **Оптимальная производительность:** Использование потоковой передачи данных (asynchronous streaming) для проксирования без буферизации больших ответов в оперативной памяти шлюза.

---

## 2. System Architecture (Системная архитектура)
Шлюз написан на **FastAPI** и функционирует как связующее звено между клиентом (мобильным приложением, фронтендом) и серверами iiko.

**Поток обработки запроса (Request Flow):**
1. Сначала запрос клиента проходит через цепочку **Middlewares**:
   - `SecureHeadersMiddleware` — инъекция заголовков безопасности (подобно Helmet).
   - `CORSMiddleware` — защита и правила Cross-Origin.
   - `AuditLogMiddleware` — логирование заголовков и пути запроса.
   - `SlowAPIMiddleware` — проверка Rate-Limits (допустимое количество запросов в минуту).
2. Запрос попадает на один из маршрутизаторов (Routers):
   - Если это запрос за токеном (`/auth/token`), он проверяет клиентские учетные данные и выдает JWT-токен (signed with RS256).
   - Если это API-запрос (`/api/{path}`), управление передается в `Proxy Router`.
3. В **Proxy Router**:
   - Происходит валидация JWT (с учетом допустимого `clock_skew_seconds`).
   - Проверяются права (RBAC): есть ли у роли разрешение `PROXY_READ` или `PROXY_WRITE`.
   - Запрос передается в `IikoClient`.
4. Блок **IikoClient** `(httpx.AsyncClient)`:
   - Подготавливает безопасные заголовки (очищает `hop-by-hop` заголовки вроде `connection`, `host`, `upgrade`).
   - Инжектит в заголовок `Authorization` реальный iiko API Key.
   - Потоком (stream) посылает тело запроса в целевой iiko API и также потоком отдает HTTP-ответ обратно клиенту.
5. Клиент получает ответ напрямую от шлюза.

---

## 3. API Interface
API шлюза делится на две основные логические части. Идентификация базируется на JWT (Bearer Token).

### 3.1 Аутентификация
- **Endpoint:** `POST /auth/token`
- **Описание:** Обменивает пару `client_id` + `client_secret` на краткосрочный JWT токен (RS256, по умолчанию 15 минут).
- **Защита:** Лимит 10 запросов в минуту. Сравнение паролей идет с константным временем (`hmac.compare_digest`), чтобы предотвратить тайминг-атаки и энумерацию пользователей (возвращает одинаковый статус 401 для неправильного ID или пароля).

### 3.2 Проксирование iiko
- **Endpoint (Чтение):** `GET /api/{path}`
  - **Требуемое разрешение:** `PROXY_READ`
- **Endpoint (Запись):** `POST, PUT, PATCH, DELETE /api/{path}`
  - **Требуемое разрешение:** `PROXY_WRITE`
- **Защита:** Лимит 50 запросов в минуту (как защита бэкенда iiko от спама).
- Отправка и получение данных идет через `StreamingResponse`.

### 3.3 Сервисные endpoints
- **Endpoint:** `GET /health` (System check).

---

## 4. Backend Architecture
Проект построен по модульным принципам Domain-Driven Design (DDD) для удобной масштабируемости.

- **`app/main.py`** — Точка входа приложения. Здесь собирается FastAPI, настраивается асинхронный контекст (lifespan) для `IikoClient` и подключаются глобальные middlewares.
- **`app/api/`** — Слой роутеров (контроллеров).
  - `auth.py` — Логика выдачи токенов.
  - `proxy.py` — Безопасное проксирование с использованием `AsyncExitStack` для корректного освобождения сетевых соединений в случае ошибок.
- **`app/core/`** — Базовая конфигурация системы.
  - `config.py` — Самая строгая часть приложения (Fail-Closed). Читает `.env`, проверяет совпадение iiko_api_key и клиентского секрета (одинаковых быть не должно), кеширует RSA ключи в памяти (Pydantic `model_post_init` + `lru_cache`).
  - `logging.py` — Интеграция `structlog` для гибкого логирования (консоль в dev, JSON в production).
- **`app/middleware/`** — Пользовательские middleware для FastAPI (Rate Limiter, Secure Headers).
- **`app/schemas/` & `app/models/`** — Pydantic-схемы (валидация In/Out) и заделы под базу данных (ORM SQLAlchemy).
- **`app/security/`** — Слой информационной безопасности (RBAC, JWT парсинг, Audit).
- **`app/services/`** — Интеграции с внешними системами:
  - `iiko_client.py` — Обертка над `httpx.AsyncClient` с тюнингом connection pool (max 500 соединений).

---

## 5. Security Model (Модель безопасности)
- **Token-Based Auth (RS256):** Пароли больше не гуляют по сети при каждом прокси-запросе. Клиенты используют асимметрично подписанный JWT, который невозможно подделать.
- **Zero-Downtime Key Rotation:** В заголовок JWT вшит параметр `kid` (Key ID). Шлюз умеет считывать файл `public_keys.json` и на лету поддерживать ротацию RSA-ключей. Устаревшие ключи просто убираются из маппинга.
- **Credential Decoupling:** Архитектура жёстко разделяет `gateway_client_secret` (данные доступа к шлюзу) и `iiko_api_key` (ключ от серверов iiko).
- **Rate Limiting:** Интегрирован модуль `slowapi`. IP-лимиты и лимиты конечных маршрутов читаются динамически из переменных окружения.
- **Fail-Closed Principle:** Если при старте сервер не нашел ключи, или переменные в `.env` настроены вразрез с политикой безопасности (например, DEBUG включен в PROD-среде), система откажется запускаться.

---

## 6. Integration with iiko (Взаимодействие с iiko)
`app/services/iiko_client.py` использует библиотеку `httpx`. Связь устроена по принципу **потокового проксирования (Non-Buffering Streaming Proxy)**.
- `req.stream()` считывает байты от клиента по мере их поступления и параллельно отправляет в iikoCloud.
- Точно так же ответ iiko возвращается обратно клиенту с помощью генератора асинхронных байтов `upstream_response.aiter_bytes()`. Это защищает шлюз от ООМ (Out of Memory) атак при передаче больших JSON или бинарных файлов.
- Для обеспечения корректности закрытия сокетов при разрывах коннекта со стороны пользователя используется `AsyncExitStack`.

---

## 7. Current Implementation State (Текущее состояние и TODO)

**Полностью реализовано:**
✔ Ядро прокси (`IikoClient`) со стримингом и управлением пулами соединений.
✔ Мидлвари безопасности (CORS, Audit, Headers).
✔ Динамический IP-based Rate Limiter.
✔ Выдача и проверка RS256 JWT токенов с поддержкой `kid`.
✔ RBAC проверки при обращении к `/api/{path}`.
✔ Корректный перехват ошибок без утечек Traceback'а клиентам.

**Текущие заглушки (Частично реализовано):**
🚧 **Client Registry:** Функция `_get_client_registry()` внутри `api/auth.py` пока захардкожена (данные берутся из `settings.gateway_client_secret`). В будущем должна использовать асинхронный доступ в БД.

**Что осталось сделать (Next Tasks):**
- **Refresh Token (`/auth/refresh`):** Реализовать конечную точку (endpoint) для продления (refresh) токена без повторной передачи `client_secret`. Переменные времени жизни для него уже заданы в `.env`.
- **Интеграция с БД (Database):** Настроить PostgreSQL/SQLite для хранения сущностей Client и Role, чтобы избавиться от хардкода.
- **Отказоустойчивое сохранение логов:** AuditLogMiddleware пока пишет просто в консоль/файл, логично было бы скидывать это в очередь (RabbitMQ/Redis) или в изолированную таблицу логов.
- **Dockerization:** Добавление `Dockerfile` и `docker-compose.yml`.

---

## 8. Project File Structure (Дерево файлов проекта)

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
├── .env
├── .env.example
├── main.py (Entry point for IDE/uvicorn runner in some configs)
├── API_SPEC.md
├── CODE_STRUCTURE.md
├── CURRENT_STATE.md
├── NEXT_TASKS.md
├── PROJECT_CONTEXT.md
├── pyproject.toml
└── requirements.txt
```
