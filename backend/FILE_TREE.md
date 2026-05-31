# ISAG — Итоговая структура директорий

Ниже представлено дерево каталогов проекта **iiko Secure API Gateway (ISAG)**, иллюстрирующее четкое разделение фронтенда, бэкенда, инфраструктуры и документации.

```text
iiko-Secure-API-Gateway-ISAG/
├── .github/workflows/          # [CI/CD] Конфигурация автоматического тестирования
│   └── ci.yml                  # Сборочная линия GitHub Actions (Pytest + Redis)
├── backend/                    # Основное приложение шлюза
│   ├── app/                    # Исходный код приложения
│   │   ├── api/                # Конечные точки REST: auth, proxy, admin, protected
│   │   ├── core/               # Общая логика: config, redis, metrics, logging, hashing
│   │   ├── db/                 # Сессии и жизненный цикл базы данных
│   │   ├── middleware/         # Слои конвейера: secure headers, size validation, rate limiter, metrics, response filter
│   │   ├── models/             # Схемы таблиц SQLAlchemy: client, audit, user
│   │   ├── schemas/            # Схемы валидации Pydantic: token, admin, user
│   │   ├── security/           # Валидатор RS256, проверка льготного периода JTI, правила RBAC
│   │   ├── services/           # Службы асинхронного проксирования и реестра клиентов
│   │   └── main.py             # Точка входа FastAPI и сборка middleware
│   ├── keys/                   # Точка монтирования RSA-ключей
│   ├── scripts/                # Утилиты бэкенда (наполнение демонстрационной БД)
│   ├── tests/                  # Тестовый набор Pytest (70 тестов)
│   ├── .env                    # Локальные переменные окружения
│   ├── .env.example            # Шаблон конфигурации переменных окружения
│   ├── API_SPEC.md             # Спецификация API-контрактов
│   ├── CODE_STRUCTURE.md       # Архитектурное описание компонентов
│   ├── CURRENT_STATE.md        # Текущий статус верификации бэкенда
│   ├── FILE_TREE.md            # Справочник структуры директорий
│   ├── PROJECT_CONTEXT.md      # Описание контекста выполнения запросов в бэкенде
│   ├── pyproject.toml          # Настройки менеджера пакетов Python
│   └── requirements.txt        # Список зависимостей бэкенда
├── frontend/                   # Панель администратора React/Vite
│   ├── src/                    # Исходный код страниц и компонентов
│   ├── Dockerfile              # Инструкция сборки Docker-образа фронтенда
│   ├── nginx.conf              # Настройки маршрутизации прокси в Nginx
│   └── package.json            # Зависимости Node.js
├── infrastructure/             # Конфигурация Prometheus и Grafana
│   ├── grafana/                # Настройки источников данных и дашбордов Grafana
│   └── prometheus.yml          # Конфигурация сбора метрик Prometheus
├── scripts/                    # Общие вспомогательные скрипты
│   ├── generate_keys.py        # Скрипт генерации пар ключей RSA
│   └── stress_test.py          # Скрипт нагрузочного тестирования профилей трафика
├── docker-compose.yml          # Файл оркестрации многоконтейнерного стека
├── ARCHITECTURE.md             # Высокоуровневая архитектура и конвейер безопасности
├── DEPLOYMENT.md               # Руководство по развертыванию (Docker и ручной запуск)
├── SECURITY.md                 # Описание мер безопасности и противодействия угрозам
├── ENV_CONFIG.md               # Спецификация переменных окружения
├── TROUBLESHOOTING.md          # Инструкции по устранению неполадок и сбоев
├── DEBUG_LOG.md                # История исправленных багов бэкенда
├── PROJECT_STATE.md            # Выполненные этапы разработки проекта
├── README.md                   # Главная страница проекта и инструкции по запуску
├── ROADMAP.md                  # План дальнейшего развития и масштабирования
├── TESTING_REPORT.md           # Результаты тестов и верификации
└── walkthrough.md              # Итоговый обзор проделанных работ
```
