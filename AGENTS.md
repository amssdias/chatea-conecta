# AGENTS.md

Canonical, tool-agnostic instructions for AI coding agents (Claude Code, Codex, Cursor, etc.) working in this repository. `CLAUDE.md` just imports this file — edit here, not there, unless something is genuinely Claude-Code-specific.

## Project snapshot

Chatea Conecta is a server-rendered Django 4.2 monolith: a browser-based English/Spanish public and private chat with guest and authenticated users, a Stripe-backed Pro subscription, Channels/Daphne for WebSockets, Celery for background jobs, MySQL for durable data, and Redis for cache/channel-layer/broker. There is no REST API and no separate frontend build app — templates + native ES modules serve the browser client.

Three domain apps: `apps/chat` (real-time chat + public content pages), `apps/users` (custom auth/profile), `apps/subscriptions` (Stripe billing/webhooks). `apps/integrations/stripe` is a thin adapter layer isolating the Stripe SDK.

For deeper, evidence-based detail beyond this file, see `docs/ai-context/` (product/domain, architecture, data model, features, interfaces, dev/ops, risks — start at `docs/ai-context/00-project-index.md`) and `docs/redis-architecture-and-key-reference.md` for the full Redis key/TTL layout. These are more exhaustive than this file but can drift from the code over time, so re-verify anything load-bearing (e.g. `docs/ai-context` currently states Python 3.9, which is stale — see Commands below). Update the relevant `docs/ai-context/0X-*.md` file whenever a change you make affects what it describes.

## Commands

Python version is 3.12 (`.python-version`, `Pipfile`'s `[requires]`). Use the project's pipenv virtualenv, not a bare `python`/`pip`.

```powershell
# Install deps
pipenv install --dev

# Run dev server (Redis/MySQL must be reachable)
pipenv run python manage.py runserver --settings=chat_connect.settings.settings_development

# Full test suite
pipenv run python manage.py test --settings=chat_connect.settings.settings_tests

# Single test (dotted label, replace as needed)
pipenv run python manage.py test apps.chat.tests.services.actions.test_private_invite --settings=chat_connect.settings.settings_tests

# Coverage (config in .coveragerc)
pipenv run coverage run manage.py test --settings=chat_connect.settings.settings_tests
pipenv run coverage report

# Migration drift check (CI runs this)
pipenv run python manage.py makemigrations --check --dry-run --settings=chat_connect.settings.settings_tests

# Create/apply migrations
pipenv run python manage.py makemigrations <app> --settings=chat_connect.settings.settings_development
pipenv run python manage.py migrate --settings=chat_connect.settings.settings_development

# Production deploy check
pipenv run python manage.py check --deploy --settings=chat_connect.settings.settings_production

# Celery
pipenv run celery -A chat_connect worker --loglevel=info
pipenv run celery -A chat_connect beat --loglevel=info

# SCSS -> CSS (watch mode; build:css runs both once, unminified + minified)
npm run sass
npm run sass-min
npm run build:css
```

`manage.py` and `chat_connect/celery.py` default to the empty `chat_connect.settings` package — **always pass `--settings=...` or set `DJANGO_SETTINGS_MODULE`** explicitly.

There is no configured lint/type-check tool (no `pyproject.toml`/ruff/black config committed, no pre-commit). `black` is a dev dependency but unenforced; run `pipenv run black .` if asked to format.

### Local stack (Docker)

Compose is split into a base file plus environment overrides — pass **both** `-f` flags:

```powershell
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Env vars are loaded per-service from `.envs/development/*.env` (`django.env`, `docker.env`, `mysql.env`, `redis.env`, `local.env`), not a root `.env` — see `.envs/production/*.env.example` for the production shape. Compose does not run migrations automatically; apply them explicitly inside the `chat-app` container.

## Architecture

- **WebSocket path**: `chat_connect/asgi.py` → `apps/chat/routing.py::websocket_urlpatterns` → `apps.chat.consumers.ChatConsumer`. `ChatConsumer` is action-driven: incoming JSON is routed by `apps/chat/websocket/dispatch.py::ACTION_MAP` (`HEARTBEAT`, `REGISTER_GROUP`, `PRIVATE_INVITE`, `SEND_MESSAGE`) to handlers in `apps/chat/services/actions/`. When adding a WebSocket action: define the protocol constant, implement the handler, register it in `ACTION_MAP`.
- **Presence/state**: Redis-backed via `apps/chat/services/activity.py` and `apps/chat/infrastructure/redis/`; usernames are lowercased, guest identity comes from cookies (`username`, `user_id`), authenticated identity from the session. Chat messages are ephemeral — there is no message-history model.
- **Redis has three logical roles** sharing one server: Django cache, Channels channel layer, and Celery broker, selected by DB index (`DJANGO_REDIS_CACHE_DB`, `REDIS_DB_CHANNEL`, `REDIS_DB_CELERY`). Keep these distinct.
- **Settings**: shared config in `chat_connect/settings/base.py`; environment overrides in `settings_development.py`, `settings_production.py`, `settings_tests.py` (each imports `*` from base).
- **Subscriptions**: `UserSubscription.pro` (via `apps/subscriptions/models/`) is the source of truth for Pro access — Stripe checkout redirects never grant Pro directly, only verified webhook-driven updates do (`apps/subscriptions/webhook_handlers/`, `apps/subscriptions/services/user_subscription.py`). Lifecycle transitions lock the row (`select_for_update`) and ignore events for a non-current Stripe subscription; Stripe SDK calls are isolated in `apps/integrations/stripe/`. Free users are capped at `FREE_PRIVATE_CHAT_LIMIT = 3` open private chats (`apps/chat/constants/private_chat.py`); Pro status is resolved from the authenticated DB user, not a cookie.
- **Celery**: `apps.chat.tasks.send_random_messages_tick` drives Beat-scheduled bot traffic (dev settings run it every 60s, base settings every 3s); `apps/subscriptions/tasks/` handles invoice/cancellation emails, enqueued via `transaction.on_commit`.
- **Cross-app coupling**: `apps.users` and `apps.subscriptions` are tightly coupled by design (signup creates a `UserSubscription`; `User` reads subscription status) — this is expected, not something to "fix" incidentally.

## Routing & i18n conventions

- `chat_connect/urls.py` wraps most routes in `i18n_patterns` (`/en/`, `/es/`) — admin, `accounts/`, `subscriptions/`, and chat pages. `/health/`, `/robots.txt`, `/sitemap.xml`, and the Stripe webhook (`/subscriptions/payments/stripe/webhook/`) sit outside the language prefix.
- `chat_connect/context_processors.py::hreflang_context` builds alternate-language links from `settings.LANGUAGES`/`SITE_URL`.
- When adding URLs or locale-aware pages, route them through `i18n_patterns` and keep the `hreflang` context processor in sync.

## External dependencies / integration points

- Redis: see Architecture above — keep the three DB-index env vars distinct.
- Stripe config comes from env vars in `chat_connect/settings/base.py`; subscription models are re-exported from `apps/subscriptions/models/__init__.py`; all SDK calls go through `apps/integrations/stripe/`.
- S3-backed import behavior exists in `apps/chat/management/commands/create_topics_and_messages.py` and `create_random_users` — their help text implies local-file support but both currently fetch JSON from S3.

## Testing conventions

- Django's built-in test runner (unittest-based); pytest is not used. Tests live under each app's `tests/` directory, mirroring services/views/websocket/infrastructure.
- Use `IsolatedAsyncioTestCase` + Channels `WebsocketCommunicator` for real async/consumer behavior; Django `TestCase` for database-backed services/views.
- `factory_boy` factories exist for users/profiles, topics/flows, subscriptions, invoice notifications — prefer them over building models by hand.
- Test settings (`settings_tests.py`) swap in SQLite, in-memory Channels layer, LocMemCache, and an in-memory Celery broker — Redis/MySQL-specific behavior (e.g. `select_for_update` locking) isn't exercised by this suite.
- CI (`.github/workflows/django-ci.yml`) only runs coverage for `apps.chat`, `apps.integrations`, `apps.subscriptions`, `apps.users` explicitly listed in the workflow — run the full suite locally before considering subscription/user changes done, not just the CI subset.

## Change style

- Prefer small edits that respect the existing service/dispatcher split instead of introducing new cross-cutting helpers.
- Reuse service functions instead of placing billing or Redis logic directly in views.
- Look for edge cases and security issues on every change, not just the happy path (guest/cookie identity spoofing, raw message rendering/XSS, webhook replay, race conditions on subscription rows) — this is a standing project requirement, not optional polish.

## Things not to hand-edit

Migrations once applied, `Pipfile.lock`, `package-lock.json`, compiled locale `.mo` files, generated CSS/maps under `chat_connect/static/style/css/`, `chat_connect/prod_static/`, coverage output, and `celerybeat-schedule`. Change the source and regenerate instead.

## Known production/config gaps (verify before relying on these paths)

- `requirements.txt` (used by the production Docker image) has historically omitted `stripe`, even though the Pipenv dev environment includes it and root URL/subscription code imports it — check both dependency lists stay in sync when touching Stripe code or the deploy image.
- `.envs/production/django.env.example` still omits `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and the Sentry variables (`SITE_URL`, Stripe, and email are already templated there) — verify env wiring against `settings/base.py`'s expectations before assuming production has what it needs.
