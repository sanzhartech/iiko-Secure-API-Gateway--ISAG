# ISAG — Руководство по развертыванию и эксплуатации

В данном руководстве приведены пошаговые инструкции по развертыванию и запуску шлюза **iiko Secure API Gateway (ISAG)** как в среде разработки, так и в продакшене.

---

## 1. Требования к системе и предварительные условия

Перед началом убедитесь, что целевой сервер соответствует следующим требованиям:
*   **Docker и Docker Compose**: Рекомендуется для промышленной эксплуатации. Поддерживается версия файлов конфигурации Compose `3.8`.
*   **Python**: Версия `3.12` (при ручном развертывании бэкенда).
*   **Node.js**: Версия `18+` или `20+` с менеджером пакетов `npm` (при ручном запуске фронтенда).
*   **Оперативная память (RAM)**: Минимум `1 ГБ` свободной оперативной памяти для запуска всего стека.

---

## 2. Стандартное развертывание в продакшене (Docker Compose)

ISAG работает как полностью контейнеризированный стек, состоящий из **6 микросервисов**:
1.  **`db`**: СУБД PostgreSQL 15 для хранения реестра клиентов и логов аудита.
2.  **`redis`**: Кэш Redis 7 для распределенного ограничения частоты запросов (rate limiting) и защиты от повторных атак (JTI replay protection).
3.  **`backend`**: Приложение на FastAPI, выполняющее конвейер обработки и валидации запросов безопасности.
4.  **`frontend`**: Панель управления на React, обслуживаемая сервером Nginx (порт 80).
5.  **`prometheus`**: Сервис для сбора метрик бэкенда.
6.  **`grafana`**: Сервис для визуализации предупреждений безопасности и логов запросов (порт 3000).

### Шаг 1: Клонирование репозитория
```bash
git clone https://github.com/sanzhartech/iiko-Secure-API-Gateway--ISAG-.git
cd iiko-Secure-API-Gateway--ISAG-
```

### Шаг 2: Генерация криптографических RSA-ключей
Шлюз использует алгоритм RS256. Перед запуском бэкенда необходимо сгенерировать пару RSA-ключей:
```bash
# Этот скрипт создает keys/private.pem and keys/public.pem,
# а также инициализирует keys/public_keys.json с активным Key ID (KID)
python scripts/generate_keys.py
```

### Шаг 3: Запуск стека
Запустите все сервисы в фоновом режиме (detached mode):
```bash
docker-compose up -d --build
```
Эта команда скомпилирует фронтенд и бэкенд, выполнит миграции базы данных, создаст учетные данные администратора по умолчанию и запустит конвейеры сбора телеметрии.

### Шаг 4: Проверка работоспособности сервисов
Убедитесь, что все контейнеры запущены и работают корректно:
```bash
docker-compose ps
```

---

## 3. Конфигурация обратного прокси Nginx

В режиме Docker контейнер **`frontend`** запускает веб-сервер Nginx, который действует как основной обратный прокси-сервер (reverse proxy). Он отдает статические файлы панели управления и маршрутизирует API-запросы к бэкенду FastAPI:

```nginx
server {
    listen 80;
    server_name localhost;

    # Обслуживание собранного React SPA
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Проксирование API-запросов к бэкенду FastAPI
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }

    # Проксирование запросов аутентификации и администрирования
    location /auth/ {
        proxy_pass http://backend:8000/auth/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /admin/ {
        proxy_pass http://backend:8000/admin/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 4. Рекомендации по настройке Redis

Чтобы предотвратить сбои из-за нехватки оперативной памяти при накоплении JTI или ключей лимитов, сервис Redis настроен как транзитный LRU-кэш:
```yaml
command: redis-server --save "" --appendonly no --maxmemory 128mb --maxmemory-policy allkeys-lru
```
*   `--save ""` и `--appendonly no`: Отключение создания снимков данных на диске (персистентность не требуется, так как кэш JTI и лимиты сбрасываются при перезапуске).
*   `--maxmemory 128mb`: Ограничение максимального объема используемой оперативной памяти в 128 МБ.
*   `--maxmemory-policy allkeys-lru`: Вытеснение наименее часто используемых ключей при достижении лимита памяти, что защищает хост-систему от переполнения.

---

## 5. Запуск в режиме разработки (ручной запуск)

Если вам необходимо запустить компоненты приложения локально без Docker:

### A. Запуск Redis
Убедитесь, что Redis запущен локально на порту `6379`.

### B. Ручной запуск бэкенда
1.  Перейдите в каталог бэкенда:
    ```bash
    cd backend
    ```
2.  Установите необходимые зависимости:
    ```bash
    pip install -r requirements.txt
    ```
3.  Настройте конфигурацию окуржения:
    ```bash
    copy .env.example .env
    # Отредактируйте файл .env, указав ваши локальные учетные данные и пути
    ```
4.  Сгенерируйте ключи локально:
    ```bash
    python ../scripts/generate_keys.py
    ```
5.  Запустите сервер FastAPI:
    ```bash
    python app/main.py
    # или: uvicorn app.main:app --reload --port 8000
    ```

### C. Ручной запуск фронтенда
1.  Перейдите в каталог фронтенда:
    ```bash
    cd frontend
    ```
2.  Установите пакеты зависимостей:
    ```bash
    npm install
    ```
3.  Запустите сервер разработки:
    ```bash
    npm run dev
    ```
4.  Откройте в браузере адрес `http://localhost:5173`.
