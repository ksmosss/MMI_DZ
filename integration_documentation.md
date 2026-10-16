# ДЗ6 — CI/CD и интеграции TaskFlow

## Выбранный стек
FastAPI + PostgreSQL + React/Vite; GitHub Actions, Google OpenID Connect (OAuth2), Яндекс.Метрика, Docker Compose, JSON logging.

## Развёртывание локально
1. Скопировать `.env.example` в `.env`, задать непустые `POSTGRES_PASSWORD` и `JWT_SECRET` (>=32 символов).
2. `docker compose up -d --build`; UI — http://localhost:8080, Swagger — http://localhost:8000/docs.
3. Readiness: `GET http://localhost:8000/health/ready`; запрос проверяет `SELECT 1` в БД.
4. Для тестов: `docker compose run --rm -v "${PWD}/backend/tests:/code/tests:ro" api sh -c "pip install -r requirements-dev.txt && python -m pytest -q /code/tests"` (в Powershell; базовый Dockerfile тесты не содержит).

## Google OAuth2 / OIDC
Создайте веб-приложение в Google Cloud Console → Credentials → OAuth Client ID. Redirect URI: `http://localhost:8000/auth/google/callback`, origin: `http://localhost:8080`; добавьте тестовых пользователей в экран согласия. Заполните `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, перезапустите `api`. Кнопка входа открывает Google. Callback проверяет ID token и verified email через Authlib, создаёт/находит пользователя, выдаёт одноразовый билет (TTL 60 сек), фронтенд обменивает его на JWT через `/auth/google/exchange`. Билет однократный, в URL не передаётся JWT. Production: HTTPS и `COOKIE_SECURE=true`, фиксированные origins и URL, хранить конфигурацию только в secrets. Обычный логин по email сохранён.

**Ограничения:** билеты хранятся в памяти одного процесса; для multi-worker нужен Redis. Увязка существующей почты с Google без отдельного подтверждения нежелательна в production; для полноценной модели нужен `google_sub` и явное linking. Вход провайдером требует реальных credentials, поэтому локально без них не проверяется.

## Яндекс.Метрика
Создайте счётчик в интерфейсе Яндекс.Метрики. Укажите `VITE_METRIKA_ID=<ID>` в `.env` и пересоберите frontend (`docker compose up -d --build frontend`). Скрипт счётчика добавляется только если ID непустой. События: `task_created`, `task_updated`, `task_deleted`. Проверьте Network (`mc.yandex.ru`) и в интерфейсе Метрики после согласия пользователя на аналитические cookies; настройка consent обязательна для публичного сайта. Проверка настоящей доставки событий требует ID и браузера.

## GitHub Actions
`.github/workflows/ci-cd.yml`: PR/push — зависимости Python/Node, Ruff lint/format, pytest, tsc, Vitest, Vite build, pip-audit и npm audit. Push в main после прохождения проверок — SSH deploy с `git pull --ff-only` и `docker compose up -d --build`. Secrets: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH`. На сервере заранее установлен Docker/Compose, имеется checkout репозитория с правильным remote, а `.env` хранится только на сервере. Деплой требует собственный сервер и проверки; сам workflow не доказывает успешный deployment.

## Мониторинг и логирование
`/health` — liveness; `/health/ready` — БД SELECT 1. Docker проверяет PostgreSQL; внешняя GitHub Actions проверка `.github/workflows/health.yml` каждые 15 минут требует secret `HEALTHCHECK_URL` с публичным HTTPS URL и генерирует сигнал об ошибке workflow. Чтобы получать письма, включить notifications for failed workflows в GitHub; для оперативного оповещения лучше внешний UptimeRobot с email/Telegram. Запросы приложений и события API выводятся в структурированном JSON в `docker compose logs api`. Для production подключите Loki/Promtail или аналог.

## Проверки для преподавателя
Скриншоты GitHub Actions (зелёные jobs + deploy), страницы OAuth входа/успешного входа/ошибки, отправленных целей Метрики, health endpoints, логов JSON и состояния Docker. Скриншоты не имитировать. Опциональные платежи не включены.
