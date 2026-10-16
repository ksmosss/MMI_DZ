# Лабораторная работа 5 — TaskFlow: Backend + PostgreSQL + Frontend

## 1. Цель и контекст

Продолжение TaskFlow из ДЗ3/ДЗ4: перенос in-memory/mock CRUD на реальную БД с аутентификацией и разграничением данных. Архитектура: React/Vite (порт 8080 в Docker) → FastAPI (127.0.0.1:8000) → PostgreSQL 16 (внутренняя сеть Compose). Для тестов backend — SQLite in-memory, чтобы не зависеть от Docker и VPS.

## 2. Проектирование БД и миграция

Сущности: `users (id, email UNIQUE, password_hash)` и `tasks (id, user_id FK, title, completed)`. Связь `users 1:N tasks`. Индекс `tasks(user_id)` ускоряет выборку своих задач, уникальный email предотвращает дубли. Файл `backend/migrations/001_init.sql` содержит SQL для PostgreSQL. Пароли хранятся только в виде Argon2-хеша.

Проектное AI-задание: «Для личного менеджера задач на FastAPI спроектируй PostgreSQL схему users/tasks с ограничениями, индексом по владельцу и миграцией. Проверь, что один пользователь не может читать чужие задачи». Итоговая схема вручную проверена на ограничения и принцип ownership.

## 3. Выбор инфраструктуры

Выбран self-hosted PostgreSQL + FastAPI в Docker Compose: контроль структуры и SQL, переиспользование стека Python, отсутствие привязки к BaaS. Supabase — альтернатива, но потребовал бы переноса существующего API и использования Supabase Auth/RLS. В составе проекта подготовлена конфигурация для локального Docker; **реальное развёртывание на VPS и запуск PostgreSQL в текущей среде не выполнялись**.

## 4. Развёртывание (локально, при наличии Docker)

```bash
cp .env.example .env
# Задайте ДВА случайных независимых секрета: POSTGRES_PASSWORD и JWT_SECRET (минимум 32 символа)
docker compose up --build -d
docker compose ps
docker compose logs api --tail=100
curl http://localhost:8000/health
```

Открыть UI: http://localhost:8080; Swagger: http://localhost:8000/docs. PostgreSQL не опубликован на хост. API привязан к loopback; для VPS требуется reverse-proxy с TLS, домен, корректные origins и firewall. SQL-файл выполняется автоматически Postgres **только при первом создании пустого тома**. Для существующей базы миграции нужно выполнять отдельно, прежде чем обновлять приложение; `docker compose down -v` удалит данные и не годится для обычного обновления.

## 5. API и запросы

| Метод | Маршрут | Назначение / статусы |
|---|---|---|
| GET | `/health` | Проверка API, 200 (не проверяет соединение с DB) |
| POST | `/auth/register` | Регистрация, 201; дубликат 409; формат 422 |
| POST | `/auth/login` | Вход, 200; неверные данные 401 |
| GET | `/tasks` | Список владельца, `search`, `completed`; 401, 422 |
| POST | `/tasks` | Создать, 201; 401/422 |
| GET | `/tasks/{id}` | Детали, 200; чужая или отсутствующая 404 |
| PATCH | `/tasks/{id}` | Изменение title/completed, 200; 404/422 |
| DELETE | `/tasks/{id}` | Удаление, 204; 404 |

Пример ручной проверки:

```bash
curl -sS -X POST http://localhost:8000/auth/register -H 'Content-Type: application/json' -d '{"email":"demo@example.com","password":"example-password-123"}'
# Скопируйте access_token в TOKEN (не добавляйте в Git/скриншоты)
curl -sS -H "Authorization: Bearer $TOKEN" http://localhost:8000/tasks
curl -sS -X POST http://localhost:8000/tasks -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"title":"Проверить интеграцию"}'
```

## 6. Безопасность

JWT HS256 с `exp` (8 часов), Argon2 для хеширования паролей, проверка `user_id` на каждом CRUD, отсутствие возможности читать чужие записи (404), пароль и ключ в `.env` (не коммитить), CORS только для заданных origins. Регистрация и вход без rate limiting, токен хранится в `localStorage` (риск XSS); для публичного развертывания добавить HTTPS, httpOnly secure cookies/CSRF-защиту, rate limiting, управление сессиями и мониторинг.

## 7. Frontend-интеграция

Режим Docker собирает фронтенд с `VITE_API_BASE_URL=http://localhost:8000`. `src/api/tasks.ts` отправляет запросы к `/tasks`, дополняет их `Authorization: Bearer`, обрабатывает HTTP 401/404/422/500 и timeout. `src/App.tsx` обеспечивает регистрацию, вход, выход, загрузку, создание, фильтрацию, изменение и удаление задач. Без `VITE_API_BASE_URL` остаётся учебный mock-режим для совместимости с ДЗ4; для ДЗ5 нужен **именно режим API**.

## 8. Отладка и тестирование

Результат независимого локального запуска: `python -m pytest -q` → **6 passed**. Покрыто: регистрация, повторный email, login, отсутствие авторизации, полный CRUD, изоляция двух пользователей, валидация, фильтрация/поиск. Диагностика: `docker compose logs api`, `docker compose logs db`, `docker compose exec db psql -U taskflow -d taskflow`, FastAPI `/docs`, вкладка Network браузера.

AI-промпты для отладки (шаблоны, а не подтверждение реальных сессий IDE):

1. «По traceback FastAPI локализуй источник HTTP 500, не выводи переменные окружения или токены, предложи тест на регрессию».
2. «Проверь SQL-запрос `SELECT ... FROM tasks WHERE user_id = :current_user` на утечку данных при обращении к чужому ID; напиши негативный pytest-тест».
3. «По Network request с 401/403 и CORS headers объясни различия между невалидным JWT, ошибкой авторизации и ошибкой preflight».
4. «Сверь DTO React и схемы Pydantic для PATCH /tasks; покажи несовместимые поля и исправления».

Тестирование в этой среде: backend pytest выполнен; полноценный запуск PostgreSQL/Docker, frontend сборка и browser E2E **не подтверждены** (Docker недоступен, npm-установка завершилась по тайм-ауту). До окончательной сдачи проверить `docker compose up --build` и ручной E2E.

## 9. Вывод

Подготовлена self-hosted архитектура, SQL-миграция, защищённый FastAPI CRUD, UI-клиент и тесты. Основное улучшение относительно ДЗ4 — постоянное хранение в PostgreSQL и приватные данные пользователей вместо общего in-memory/mock списка. Осталось провести демонстрацию реального Compose и браузерную проверку на машине с Docker.
