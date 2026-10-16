# ДЗ6 — аудит безопасности (кодовый обзор)

Проверены основные места TaskFlow: `backend/app/main.py`, хранение JWT, SQLAlchemy, CORS, UI, Compose, зависимости. Это статический аудит, **не** подтверждённый внешним pentest.

| Риск | Состояние | Мера |
|---|---|---|
| SQL injection | запросы через SQLAlchemy bind parameters | не использовать конкатенацию SQL |
| XSS | React экранирует текст задач по умолчанию | не применять `dangerouslySetInnerHTML` |
| CSRF в Google login | OAuth state проверяется Authlib | SameSite=Lax, в продакшне Secure и HTTPS |
| JWT в localStorage | **остаточный риск**, доступен при XSS | при production переходить на HttpOnly cookies, CSP |
| Brute force | **не устранён** | rate-limit на login/register, reverse proxy/WAF |
| Account linking OAuth по email | **риск** | добавить отдельный `google_sub` и подтверждение связи |
| Secrets | `.env` gitignored, конфигурация через environment | не коммитить .env, secret scanning |
| Dependency vulnerabilities | автоматические npm audit / pip-audit в CI | результаты зависят от актуальных баз, обновлять по отчётам |
| IDOR | owner_id проверяется в CRUD | отдельный тест межпользовательского доступа |
| Логи | JSON и без паролей | не логировать Authorization/cookies |

Сканирования `npm audit`/`pip-audit` должны быть запущены в GitHub Actions; результат без фактического запуска не заявлен. Итог: учебная конфигурация нуждается в ограничении частоты, HTTPS и усилении identity linking до публичного продакшена.
