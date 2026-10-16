# Использование AI в ДЗ6
AI применён для генерации скелета CI/CD, кода OAuth2/аналитики, code review по OWASP и примеров JSON logs. Промпты для воспроизведения:

1. «Проверь FastAPI + React стек. Составь GitHub Actions pipeline: Ruff, pytest, TypeScript, Vitest, Vite build, npm audit, pip-audit и SSH deploy. Не добавляй секреты в репозиторий».
2. «Проверь login / task CRUD на IDOR, SQL injection, XSS, CSRF, утечки JWT и brute force. Раздели исправленные и остающиеся риски».
3. «Проанализируй JSON logs API: ошибки 401/422/5xx, корреляции, деградацию ready endpoint, дай план диагностики без утечки секретов».

**Статус:** это исходные промпты и результаты подготовки, не записи реального диалога с отдельным AI-агентом. Для доказательства в Cursor сохранить реальные запросы/ответы и скриншоты.
