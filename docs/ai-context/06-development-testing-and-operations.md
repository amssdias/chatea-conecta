# Development, Testing, and Operations

> Last analyzed commit: `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` on branch `003-user-pro`  
> Analysis date: 2026-08-02

## Local setup

### Confirmed prerequisites

- Python 3.9 (`.python-version` is 3.9.13; `Pipfile` requires 3.9).
- Pipenv and the locked Python dependencies.
- Docker/Docker Compose for Redis 7.2.4, MySQL, Django, Celery worker, and Celery Beat.
- Node/npm only when regenerating or watching SCSS; `package.json` contains Dart Sass.
- A project-root `.env` and ignored `redis.conf`. Never commit or paste their values.

### Docker path

1. Create `.env` with the required names listed below.
2. Create `redis.conf` with authentication matching the Redis environment; the file is ignored and absent from Git.
3. Start the stack:

   ```powershell
   docker-compose -f docker-compose.dev.yml up --build
   ```

4. Apply migrations explicitly; Compose does not run them:

   ```powershell
   docker-compose -f docker-compose.dev.yml exec chat-app python manage.py migrate
   ```

5. Open `http://localhost:8000/`. The Compose file starts web, worker, Beat, MySQL, and Redis. It does not start a separate frontend server; Django serves static sources in development.

**Known setup limitation:** the development Compose environment does not pass Stripe or email variables into containers, even if they exist in `.env`; payment/email flows therefore need Compose changes or another explicit process environment before they work inside the container.

### Host/Pipenv path

```powershell
pip install pipenv
pipenv install --dev
pipenv run python manage.py migrate --settings=chat_connect.settings.settings_development
pipenv run python manage.py runserver --settings=chat_connect.settings.settings_development
```

Redis and MySQL must already be running and their host/DB settings correct. Start asynchronous processes separately:

```powershell
pipenv run celery -A chat_connect worker --loglevel=info
pipenv run celery -A chat_connect beat --loglevel=info
```

Set `DJANGO_SETTINGS_MODULE=chat_connect.settings.settings_development` for Celery or pass it in the process environment. `manage.py` and `chat_connect/celery.py` otherwise default to the empty `chat_connect.settings` package, so an explicit settings module is safer.

### Environment variable catalogue

| Area | Names |
|---|---|
| Django/site | `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL` |
| MySQL | `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`; Compose additionally interpolates `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` |
| Redis | `REDIS_PROTOCOL`, `REDIS_PASSWORD`, `REDIS_HOST`, `REDIS_PORT`, `DJANGO_REDIS_CACHE_DB`, `REDIS_DB_CHANNEL`, `REDIS_DB_CELERY` |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_MONTHLY_PRICE_ID`; `STRIPE_SUCCESS_URL`/`STRIPE_CANCEL_URL` are currently unused |
| Email | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`; code optionally reads `SUPPORT_EMAIL` |
| AWS/logging | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `APP_NAME`, `SKIP_CLOUDWATCH` |
| Sentry | `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_ENVIRONMENT` |
| Runtime | `DJANGO_SETTINGS_MODULE` |

Do not use the working-tree `prod.txt` as configuration source: it was untracked and contained plaintext production-style credentials during analysis. Rotate any real credentials it contained and remove it securely outside this documentation task.

### Database and seed data

```powershell
pipenv run python manage.py migrate --settings=chat_connect.settings.settings_development
pipenv run python manage.py createsuperuser --settings=chat_connect.settings.settings_development
pipenv run python manage.py create_random_users --file <s3-key> --bucket <bucket> --settings=chat_connect.settings.settings_development
pipenv run python manage.py create_topics_and_messages --file <s3-key> --bucket <bucket> --settings=chat_connect.settings.settings_development
```

No fixtures are tracked. Although command help/docstrings mention local files, both current commands call S3 unconditionally; bucket/key and AWS access are therefore required. Their JSON shapes are described in the command source.

## Common commands

| Goal | Command | Verification/status |
|---|---|---|
| Install exact dev dependencies | `pipenv install --dev` | Used by CI |
| Install production Pipenv set | `pipenv install` | Used by migration/deploy-check jobs; production image instead uses `requirements.txt` |
| Run development server | `pipenv run python manage.py runserver --settings=chat_connect.settings.settings_development` | Host MySQL/Redis required |
| Full tests | `pipenv run python manage.py test --settings=chat_connect.settings.settings_tests` | Verified 2026-08-02: 248 tests passed |
| App/target test | `pipenv run python manage.py test apps.chat.tests.services.actions.test_private_invite --settings=chat_connect.settings.settings_tests` | Replace dotted label as needed |
| System check | `pipenv run python manage.py check --settings=chat_connect.settings.settings_tests` | Verified: no issues |
| Production check | `pipenv run python manage.py check --deploy --settings=chat_connect.settings.settings_production` | Supply safe required environment; CI sets `SKIP_CLOUDWATCH=1` |
| Migration drift | `pipenv run python manage.py makemigrations --check --dry-run --settings=chat_connect.settings.settings_tests` | Verified: no changes detected |
| Create migrations | `pipenv run python manage.py makemigrations <app> --settings=chat_connect.settings.settings_development` | Review generated migration |
| Apply migrations | `pipenv run python manage.py migrate --settings=chat_connect.settings.settings_development` | Not automatic in Compose |
| Coverage | `pipenv run coverage run --source="." manage.py test --settings=chat_connect.settings.settings_tests` then `pipenv run coverage report` | CI limits source/tests to `apps.chat`; local analysis measured whole-project 87% line coverage |
| Format/check Python | `pipenv run black --check .` / `pipenv run black .` | Black exists; no repository config or CI job |
| Celery worker | `pipenv run celery -A chat_connect worker --loglevel=info` | Set settings module and Redis env |
| Celery Beat | `pipenv run celery -A chat_connect beat --loglevel=info` | Generates `celerybeat-schedule`; do not commit/edit |
| Sass expanded watcher | `npm run sass` | Watches SCSS directory and writes CSS/maps |
| Sass minified watcher | `npm run sass-min` | Watches `main.scss` and writes `main.min.css` |
| Collect static | `pipenv run python manage.py collectstatic --noinput --settings=chat_connect.settings.settings_production` | Manifest storage requires all referenced assets |
| Compile translations | `pipenv run python manage.py compilemessages` | Requires gettext; production image installs it |

There is no confirmed lint/type-check command for Ruff, isort, mypy, pyright, ESLint, Prettier, or pre-commit because those tools/configurations are absent. Sass scripts are watchers; no dedicated one-shot frontend build script exists.

## Testing strategy

### Framework and layout

- Django’s built-in unittest runner is used; pytest is not installed/configured.
- Tests live inside each app under `apps/<app>/tests/` and mirror services, views, WebSocket helpers, and infrastructure.
- `factory_boy` factories exist for users/profiles, topics/flows, subscriptions, and invoice notifications.
- Test settings use SQLite, in-memory Channels, LocMemCache, in-memory Celery broker, locmem email, non-secure cookies, and muted logging.
- Most Stripe/Redis/Channels/email boundaries are mocked. No live MySQL, Redis, Stripe CLI, SMTP, S3, Sentry, CloudWatch, NGINX, or browser integration test is run by the Django suite.

### Coverage observed during analysis

Fresh full-suite verification found 248 passing tests and 87% overall line coverage using `--source=apps,chat_connect`. Important low-coverage runtime modules included:

| Area | Observed coverage | Interpretation |
|---|---:|---|
| `apps/chat/consumers.py` | 29% | Consumer `_test_*` helpers are not discovered; connect/disconnect/event methods largely unverified |
| `apps/subscriptions/services/webhook_handlers.py` | 26% | Its intended test file is entirely commented out |
| S3 management commands | 0% | Input, partial failure, and provider behavior untested |
| `apps/subscriptions/services/create_pro_subscription.py` | 39% | Checkout/customer/idempotency paths untested |
| Subscription Checkout/webhook/portal views | 44–54% | Direct request/permission/provider-error tests missing |
| Signup/login views and signup service/form | 45–56% | Account aggregate and cookies/errors under-tested |
| Bot task | 52% | Scheduling/probability/Channels task flow under-tested |
| ASGI/WSGI/production/development settings | 0% | Deployment import/runtime integration not covered |

High-coverage service areas include subscription lifecycle state (95%), bot Redis store (94%), and WebSocket broadcast helpers (95%). Line coverage does not cover browser JavaScript, including the unsafe `innerHTML` path.

### Test gaps to prioritize

- Real session/guest `WebsocketCommunicator` connection, malformed JSON, valid close codes, multi-client public/private messaging, and disconnect cleanup.
- Guest identity mapping verification and message HTML/XSS regression tests (with browser/DOM coverage for rendering).
- Signup/login/password change/password reset and custom `UserAdmin` password semantics.
- Checkout creation ownership, customer reuse, duplicate/concurrent initiation, absolute URLs, provider errors, result/cancel methods, Billing Portal, and subscription detail.
- Webhook HTTP signature/dispatch/error responses plus active claim/retry/stuck-event behavior.
- Celery task state transitions/retries/duplicate sending; S3 commands; health dependencies.
- MySQL-specific locking/concurrency. SQLite tests cannot validate `select_for_update` behavior.

### CI mismatch

`.github/workflows/django-ci.yml` runs tests and coverage only for `apps.chat`, so subscription/user regressions can merge despite the full local suite being healthy. Migration and deploy checks do cover the project configuration globally.

## Code quality tooling

| Tool | Status |
|---|---|
| Black | Dev dependency (lock 24.10.0); no `pyproject.toml`/config, pre-commit hook, or CI enforcement |
| Coverage.py | Dev dependency; CI report exists, no `.coveragerc`; generated `.coverage` is ignored |
| Factory Boy/Faker | Used throughout tests |
| Ruff/isort/mypy/pyright | Not configured |
| ESLint/Prettier/JS tests | Not configured |
| Markdown lint | Not configured/installed in repository |
| Pre-commit | Not configured |

Style is mostly service-oriented and type hints appear in newer modules, but there is no enforced type or lint baseline. Generated CSS/maps are tracked; edit SCSS and regenerate rather than patching generated output.

## Deployment

### Confirmed model

`docker-compose.prod.yml` defines MySQL, password-protected Redis, Daphne web, an autoscaled Celery worker (`--autoscale=4,2`), and Celery Beat. The web healthcheck requests `/health/`. Static collection writes to a mounted `chat_connect/prod_static`; the repository’s deployment workflow restarts a host NGINX service after containers.

The manual GitHub workflow:

1. SSHes to the VPS using repository secrets.
2. Fetches and hard-resets to remote `master`.
3. Builds, stops, and starts production Compose.
4. Compiles translations.
5. Optionally flushes all Redis databases, migrates, and collects static.
6. Restarts NGINX.

There is no blue/green/canary deployment, automated backup, rollback command, migration rollback policy, artifact registry, or verified zero-downtime procedure. Rollback is effectively another Git reset/deploy and is not documented.

### Confirmed deployment blockers/contradictions

- `deployments/production/Dockerfile` installs `requirements.txt`, but that file omits the `stripe` dependency imported by root URL/subscription modules. The Pipenv environment contains Stripe; the production image dependency list does not.
- Production Compose does not pass `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, Stripe, email, Sentry, or `SITE_URL` variables to app/worker containers. With the tracked file alone, hosts default empty and payment/email configuration is absent.
- The container healthcheck uses Host `localhost`; an empty production `ALLOWED_HOSTS` causes Django host rejection before the health view.
- CI tests the Pipenv dependency set, not the production `requirements.txt` image, so it does not catch the missing Stripe import.
- Deploy always targets `master`, not the analyzed branch, and optional migrations/collectstatic default false.
- Compose publishes MySQL and Redis ports on the host. External reachability depends on VPS firewall/network policy, which is outside the repository.
- No restart policy is specified for services.

## Observability

- Development logs the `chat_connect` logger to console at INFO while the handler level is DEBUG.
- Production sends Django and `chat_connect` INFO+ to console and CloudWatch, with warning+ also becoming Sentry events. Sentry integrates Django/Celery and samples traces at an environment-controlled rate.
- Admin pages expose subscription, webhook-event, notification, topic/flow, user, and profile records.
- `StripeWebhookEvent.error_message/processed_at/status` and `StripeInvoiceNotification` provide operational ledgers.
- `/health/` confirms only that Django can return a response. There are no metrics, structured audit log, queue dashboard, Redis/MySQL dependency probes, alert rules, or repository-defined operational dashboards.
- Avoid logging raw webhook payloads, Redis URLs, customer email, or configuration secrets. Current webhook logs only event type/ID-oriented messages.

## Troubleshooting guide

| Symptom | Checks / likely repository cause |
|---|---|
| `python` says no version configured | `.python-version` expects 3.9.13. Activate/configure pyenv or use `pipenv run`; do not trust a shim that returns success after printing an error. |
| Django settings are missing | Pass `--settings=chat_connect.settings.settings_development` or set `DJANGO_SETTINGS_MODULE`; the base package itself is empty. |
| Redis authentication/connection failure | Ensure `redis.conf` password matches env; confirm host/port/protocol and three DB indices. The chat wrappers use the Channels DB URL. |
| Guest nickname remains taken | Inspect `chatconnect:users:usernames`; disconnect cleanup may have failed and the set has no TTL. Do not flush all Redis in production without understanding Channels/Celery impact. |
| User appears offline with another tab open | Presence is not reference-counted; one disconnect deletes the shared marker/username. Heartbeat may restore only the marker. |
| WebSocket immediately closes | Confirm session or both cookies, allowed Host/Origin, proxy upgrade headers, and `/ws/chat/` routing. Invalid group/identity uses close 4001; send-message invalid group uses problematic 401. |
| Messages disconnect or render strangely | Validate JSON shape. Server does not catch malformed JSON or validate message type/length; first-cluster browser rendering uses `innerHTML`. |
| Private-chat slot will not free | Closing the sidebar is UI-only; the consumer/Redis relationship remains until TTL/reconnect behavior. |
| No bot messages | Beat/worker/broker must run; at least one online marker must exist; MySQL needs eligible users/topics/non-promotional flows; cache may be stale for a week. |
| Stripe import fails in production image | `requirements.txt` omits Stripe; the Pipenv environment and production image are inconsistent. |
| Checkout returns 500 | Check Stripe variables/network and local customer state; creation view does not catch provider errors. |
| Checkout success stays pending | It intentionally waits for verified webhook-updated local state. Inspect event ledger, Stripe webhook configuration, customer/subscription matching, and stuck `processing`. |
| Webhook keeps returning 500 | Inspect `StripeWebhookEvent.error_message`, local customer mapping, event object assumptions/API version, and worker/provider logs. Failed rows can be reclaimed only on another delivery. |
| Webhook never retries | A row left `processing` cannot be reclaimed; no recovery task exists. |
| Email retries/fails | Inspect invoice notification state, user email validity, SMTP config, worker logs, and templates. Cancellation email has no notification ledger. |
| Password change page errors | The template contains duplicate `content` blocks and raises `TemplateSyntaxError`; this was confirmed by loading the template. |
| Checkout success returns a template error | `subscriptions/checkout_success.html` has a split `endblocktrans` tag; all result renders fail template compilation until it is corrected. |
| Production container unhealthy | Check missing `ALLOWED_HOSTS` propagation and production dependencies before debugging the health function itself. |
| CloudWatch blocks checks/startup | Provide AWS config or set `SKIP_CLOUDWATCH=1` for non-production validation, as CI does. |

## Verification baseline

On 2026-08-02, using the repository’s existing Pipenv virtual environment with Python 3.9.13/Django 4.2.16:

- `manage.py check` with test settings: no issues.
- migration drift check: no changes detected.
- full test suite: 248/248 passed in roughly one second.
- whole-project coverage: 87% line coverage.
- all 28 repository templates were compiled: 26 loaded and two failed—password change (duplicate `content` block) and Checkout success (`blocktrans` incorrectly contains a later `elif`).

These results are a point-in-time baseline for the analyzed working tree, not a guarantee for a rebuilt production image.
