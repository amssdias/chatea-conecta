# Chatea Conecta: AI Project Index

> Last analyzed commit: `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` on branch `003-user-pro`  
> Analysis date: 2026-08-02  
> Scope note: the analysis also considered the current working tree. It contained pre-existing uncommitted and untracked files; no secret values are reproduced here.

## Project identity

| Field | Value |
|---|---|
| Project | Chatea Conecta |
| Purpose | Browser-based English/Spanish public and private chat. Visitors may join as guests; account holders can authenticate, recover passwords, and buy a Stripe-backed Pro subscription that removes the three-private-chat opening limit. Redis holds chat identity, presence, private-chat restoration, bot data, and Channels traffic; chat messages are not stored in the database. |
| Branch / commit | `003-user-pro` / `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` |
| Primary languages | Python, JavaScript, Django templates, SCSS/CSS, YAML |
| Frameworks | Django 4.2.16, Channels 4.1.0, Daphne 4.1.2, Celery 5.4.0 |
| Runtime infrastructure | MySQL, Redis, Daphne, Celery worker, Celery Beat, Docker Compose; host NGINX and GitHub Actions deployment are configured |
| External services | Stripe, SMTP email, AWS S3, CloudWatch Logs, Sentry, Google Analytics |
| Maturity | **Inferred:** production-oriented MVP. A VPS deployment workflow and observability exist, but confirmed security, deployment, and coverage gaps prevent treating the repository as production-hardened. |

## Documentation map

| Document | Purpose | Read when |
|---|---|---|
| [01-product-and-domain.md](01-product-and-domain.md) | Users, terminology, permissions, business rules, invariants, product boundaries | Clarifying expected behavior or entitlements |
| [02-architecture-and-codebase.md](02-architecture-and-codebase.md) | Processes, packages, dependency flow, lifecycles, and settings | Locating implementation or changing structure/configuration |
| [03-data-model-and-state.md](03-data-model-and-state.md) | MySQL entities plus Redis, cookies, and transient state | Changing models, migrations, ownership, presence, or concurrency |
| [../redis-architecture-and-key-reference.md](../redis-architecture-and-key-reference.md) | Full Redis key/TTL reference (cache, channel layer, broker DBs) | Adding/changing a Redis key, debugging presence/private-chat/bot state |
| [04-features-and-workflows.md](04-features-and-workflows.md) | Feature-by-feature entry points, flows, failures, tests, and status | Implementing or debugging a user-facing capability |
| [05-interfaces-and-integrations.md](05-interfaces-and-integrations.md) | HTTP/WebSocket contracts, reusable services, authentication, and providers | Changing endpoints, events, Stripe, email, Redis, or S3 |
| [06-development-testing-and-operations.md](06-development-testing-and-operations.md) | Setup, commands, test strategy, deployment, observability, troubleshooting | Running, testing, releasing, or diagnosing the application |
| [07-current-status-risks-and-roadmap.md](07-current-status-risks-and-roadmap.md) | Evidence-based capabilities, incomplete work, risks, debt, roadmap | Prioritizing work or reviewing safety/correctness |

## Fast project orientation

### Users and use cases

- **Guests** choose a 3–20 character nickname and use public chat without an account. Their identity is stored only in cookies and Redis (`apps/chat/views/chat.py::ChatView`).
- **Authenticated users** use Django sessions, can reset passwords, own a profile and normally a `UserSubscription`, and retain an account identity (`apps/users/views/`, `apps/users/services/create_user.py`).
- **Pro users** are authenticated users whose local subscription grants `UserSubscription.pro`; they are not subject to the three-private-chat initiation limit (`apps/subscriptions/models/user_subscription.py::UserSubscription.pro`, `apps/chat/services/actions/private_invite.py`).
- **Staff/superusers** use Django admin. There is no moderator, organization, tenant, or business-account model.
- **Automated bot identities** are currently every non-staff, non-superuser database user—not a dedicated role (`apps/chat/services/bots/bot_cache_loader.py::BotCacheLoader._load_bot_users`).

### Important packages and entry points

| Area | Entry points |
|---|---|
| HTTP | `manage.py`, `chat_connect/urls.py`, `chat_connect/views.py` |
| ASGI/WebSocket | `chat_connect/asgi.py` → `apps/chat/routing.py` → `apps/chat/consumers.py::ChatConsumer` |
| WebSocket actions | `apps/chat/websocket/dispatch.py::ACTION_MAP` → `apps/chat/services/actions/` |
| Background work | `chat_connect/celery.py`, `apps/chat/tasks/send_random_chat_messages.py`, `apps/subscriptions/tasks/` |
| Accounts | `apps/users/urls.py`, `apps/users/views/`, `apps/users/services/create_user.py` |
| Billing | `apps/subscriptions/urls.py`, the non-localized webhook in `chat_connect/urls.py`, and `apps/subscriptions/services/` |
| Provider adapters | `apps/integrations/stripe/` |
| Browser chat | `apps/chat/templates/chat/chat.html`, `apps/chat/static/js/main.js` |

### Critical dependencies and business rules

- MySQL is authoritative for users, profiles, subscription state, webhook claims, notification delivery state, topics, and bot message text.
- Redis is separately used for Django cache, the Channels layer/application chat state, and the Celery broker. Keep `DJANGO_REDIS_CACHE_DB`, `REDIS_DB_CHANNEL`, and `REDIS_DB_CELERY` distinct (`chat_connect/settings/base.py`).
- A free user may initiate at most `FREE_PRIVATE_CHAT_LIMIT = 3` private chats held in the consumer mapping; Pro access is decided from the authenticated database user, not a cookie (`apps/chat/constants/private_chat.py`, `apps/chat/services/subscription_access.py`).
- Stripe redirects never activate Pro. Only verified webhook-driven local state updates do (`apps/subscriptions/views/checkout.py::checkout_success_view`, `apps/subscriptions/webhook_handlers/`).
- Subscription lifecycle handlers lock the `UserSubscription` row and ignore events for a non-current Stripe subscription (`apps/subscriptions/services/user_subscription.py`). Checkout completion is the only service that replaces the current Stripe subscription ID.
- Webhook event IDs and invoice/email-type pairs are unique, providing claim and notification deduplication (`apps/subscriptions/models/stripe_webhook_event.py`).
- Chat messages are ephemeral. There is no message-history model after `apps/chat/migrations/0004_delete_userconversation.py`.
- Public online counts are deliberately inflated: the home page shows a random 55–63 when the Redis count is at most five, and WebSocket room registration reports the Redis count plus 60 (`apps/chat/views/home_chat.py`, `apps/chat/services/actions/register_group.py`).

### Important commands

```powershell
docker-compose -f docker-compose.dev.yml up --build
pipenv run python manage.py migrate --settings=chat_connect.settings.settings_development
pipenv run python manage.py test --settings=chat_connect.settings.settings_tests
pipenv run python manage.py makemigrations --check --dry-run --settings=chat_connect.settings.settings_tests
pipenv run python manage.py check --deploy --settings=chat_connect.settings.settings_production
npm run sass
npm run sass-min
```

Custom import commands are `create_random_users` and `create_topics_and_messages`; both implementations currently fetch JSON from S3 even though their help text implies local-file support.

### Current priorities

Priorities are evidence-based, not a declared roadmap: close the guest identity and browser XSS paths; restore production dependency/configuration correctness; make checkout creation idempotent; define private-chat close/count semantics; reactivate webhook orchestration tests; and broaden CI beyond `apps.chat`. See [07-current-status-risks-and-roadmap.md](07-current-status-risks-and-roadmap.md).

## Recommended AI reading order

| Task | Read first | Then |
|---|---|---|
| Implement a feature | `01`, `04` | `02`, `03`, relevant sections of `05` and `06` |
| Fix a bug | `04`, `07` | `02` lifecycle, `03` state, relevant tests in `06` |
| Modify a model | `03` | `01` invariants, `04` callers, `06` migration checks |
| Change an HTTP/API interface | `05` | `04`, `02` request lifecycle; note that no REST API exists |
| Authentication/permissions | `01` actors, `05` auth | `03` ownership, `04` account/chat flows, `07` identity risks |
| Payments | `01` subscription rules, `04` billing workflows | `03` state machine, `05` Stripe interface, `07` risks |
| WebSocket/Celery behavior | `02`, `05` | `03` Redis state, `04` chat/bot workflows, `06` process commands |
| Deployment configuration | `06` | `02` configuration, `05` provider variables, `07` deployment risks |
| Write tests | `04` feature tests, `06` strategy | `07` coverage gaps and the target implementation |

## AI working instructions

- Preserve the Django app boundaries: chat behavior in `apps/chat`, account behavior in `apps/users`, subscription domain logic in `apps/subscriptions`, and Stripe SDK calls in `apps/integrations/stripe`.
- Keep settings shared in `chat_connect/settings/base.py`; put environment overrides in `chat_connect/settings/settings_development.py`, `chat_connect/settings/settings_production.py`, or `chat_connect/settings/settings_tests.py`.
- Keep `ChatConsumer` action-driven. For a new action, define the protocol constant, implement a handler under `apps/chat/services/actions/`, and register it in `apps/chat/websocket/dispatch.py::ACTION_MAP`.
- Reuse service functions instead of placing billing or Redis logic directly in views. Subscription state transitions belong in `apps/subscriptions/services/user_subscription.py`; Stripe object mapping belongs in `apps/subscriptions/webhook_handlers/mappers.py`.
- Use repository-relative references and do not copy `.env` or provider credentials into code, tests, or documentation.
- Add tests beside the owning app: `apps/chat/tests/`, `apps/users/tests/`, or `apps/subscriptions/tests/`. Use `IsolatedAsyncioTestCase`/Channels communicators for actual async behavior and Django `TestCase` for database services/views.
- Before completion, run the full suite—not only CI’s current `apps.chat` subset—plus system and migration checks shown above. For deployment changes also run Django’s production `check --deploy` with safe test environment values.
- Handle these areas carefully: cookie/WebSocket identity, raw message rendering, Redis TTL/key compatibility, subscription row locks, webhook status claiming, Stripe event ordering, Celery `transaction.on_commit`, i18n URL prefixes, and production logging initialization.
- Do not manually edit migrations once applied, `Pipfile.lock`, `package-lock.json`, compiled locale `.mo` files, generated CSS/maps under `chat_connect/static/style/css/`, collected `prod_static/`, coverage output, `celerybeat-schedule`, or cache directories. Change their sources and regenerate.
- The working tree already had user-owned changes before these docs were created. Do not reset, delete, or fold them into unrelated work.
