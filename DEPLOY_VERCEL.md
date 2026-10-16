# TaskFlow: один Vercel-проект + Neon PostgreSQL

## 1. GitHub
Распакуйте ZIP; залейте **содержимое папки** `taskflow_vercel` в новый GitHub-репозиторий. Не добавляйте `.env`.

## 2. PostgreSQL
В Vercel Marketplace подключите Neon PostgreSQL либо создайте БД на neon.tech.
В SQL Editor Neon **один раз** выполните `backend/migrations/001_init.sql` (до регистрации первого пользователя).

## 3. Vercel
Import Git Repository. **Root Directory = корень репозитория**, не `frontend`.
Framework Preset: **Other**. Конфигурация `vercel.json` задаёт build/output.
В Environment Variables (Production/Preview при необходимости) укажите:

- `DATABASE_URL`: строка подключения Neon с `sslmode=require` (server-side).
- `JWT_SECRET`: случайная строка минимум 32 символа; пример генерации: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
- `COOKIE_SECURE`: `true`.

`VITE_API_BASE_URL` **необязательна**: production по умолчанию использует `/api`. При явном задании её значение должно быть `/api`.

Нажмите Deploy.

## 4. Проверка

- `https://ВАШ-ДОМЕН/api/health` → `{"status":"ok"}`
- `https://ВАШ-ДОМЕН/api/health/ready` → `{"status":"ready","database":"ok"}`
- `https://ВАШ-ДОМЕН/` → React UI, попробуйте регистрацию и сохранение задачи.

## Ограничения

- PostgreSQL работает **в Neon, а не внутри Vercel**, т. к. файловая система Vercel Functions не подходит для постоянной SQLite-базы.
- Google OAuth выключен в UI: текущая реализация backend использует локальное in-memory хранилище одноразовых ticket и не рассчитана на несколько serverless-инстансов.
- Обязательно храните секреты в Vercel Environment Variables, а не в Git.
- Production API `/api/…` проксируется функцией `api/index.py`; маршруты на стороне backend остаются `/auth`, `/tasks`, `/health`.
- Деплой на действительном аккаунте Vercel не проверялся; после первого деплоя проверьте Runtime Logs и маршруты выше.
