# Current Status, Risks, and Roadmap

> Last analyzed commit: `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` on branch `003-user-pro`  
> Analysis date: 2026-08-02  
> Assessment basis: tracked commit plus the current working tree; risk labels distinguish **confirmed**, **likely**, and **needs verification**.

## Implemented capabilities

| Capability | Use case and evidence | Verification |
|---|---|---|
| Localized public site | English/Spanish landing/content URLs, hreflang, sitemap, robots (`chat_connect/urls.py`, `chat_connect/context_processors.py`, `apps/chat/sitemaps/`) | Basic route/home tests; metadata paths largely untested |
| Guest chat admission | Nickname validation, collision checks, Redis identity/cookies (`apps/chat/views/chat.py`) | Broad `apps/chat/tests/views/test_chat.py` |
| Account auth | Custom user/profile, signup aggregate, session login/logout, password reset templates (`apps/users/`) | Logout covered; other flows lightly/uncovered |
| Public real-time chat | Channels consumer, action dispatcher, room registration, broadcast, browser modules (`apps/chat/consumers.py`, `services/actions/`, `static/js/`) | Handler/helper unit tests; real consumer/browser flow not covered |
| Private chat | Invite, online/bot checks, group membership, offline/online notifications, Redis restoration (`apps/chat/services/actions/private_invite.py`, `services/private_chats.py`) | Invite/restoration/broadcast tests |
| Pro entitlement | One-to-one subscription predicate and server-side free limit of three (`UserSubscription.pro`, `user_has_pro_access`, `FREE_PRIVATE_CHAT_LIMIT`) | State service and some invite tests; exact fourth-invite matrix incomplete |
| Bot traffic | Topic/flow models, one-week Redis cache, one-hour repeat suppression, scheduled broadcast (`apps/chat/services/bots/`, `tasks/`) | Strong cache/selection tests; task/commands untested |
| Stripe Checkout/results | Customer reuse, Checkout creation, ownership-checked success with pending local state (`apps/subscriptions/services/create_pro_subscription.py`, `apps/subscriptions/views/checkout.py`) | Downstream sync tested; result template is confirmed broken; initiation/views not directly tested |
| Subscription lifecycle | Row-locked Checkout/paid/failed/updated/deleted synchronization; stale subscription rejection (`services/user_subscription.py`) | Extensive lifecycle tests |
| Billing management | Detail UI, Billing Portal, period-end cancellation (`apps/subscriptions/views/`, `integrations/stripe/`) | Cancellation covered; detail/portal not |
| Webhook verification/idempotency | Signature check, unique event ledger, conditional claim, handler registry (`integrations/stripe/webhooks.py`, `services/webhook_handlers.py`) | Individual handlers/mappers covered; orchestration/view coverage missing |
| Transactional email queueing | Invoice notification dedupe, post-commit Celery enqueue, retrying HTML/text emails; cancellation mail (`apps/subscriptions/emails.py`, `apps/subscriptions/tasks/`) | Email/queue/handler tests |
| Admin/operations | Admin registrations, health endpoint, Docker processes, manual VPS deployment, Sentry/CloudWatch (`admin/`, deployments, `.github/`) | Settings check; no deployment/admin integration test |

Point-in-time verification found 248 passing Django tests, no system-check errors, no migration drift, and 87% overall line coverage. This does not exercise the production image or browser JavaScript.

## Partially implemented, stale, or unclear work

| Area | Evidence | Assessment |
|---|---|---|
| Webhook orchestration tests | Current untracked `apps/subscriptions/tests/services/test_webhook_handlers.py` consists entirely of commented tests | Intended pending/processing/retry/duplicate coverage is disabled |
| Consumer integration tests | `apps/chat/tests/consumers/test_consumer.py` methods are named `_test_*` | Test runner discovers none; file contains stale pre-dispatch payload shapes and a `print` |
| Private chat closing | Sidebar removes DOM only; no WebSocket action, group discard, or Redis hash delete (`apps/chat/static/js/views/sideBarView.js`, `apps/chat/websocket/dispatch.py::ACTION_MAP`) | Slot/count semantics incomplete; also called out in the untracked planning note |
| Promotional bots | Promotional Redis constants and `SEND_PROMOTIONAL_MESSAGES=False` exist; loader always excludes promotional flows | Data model/config without exposed workflow |
| `expired` subscription | Enum/migration include it; mapper never returns it | Unused state |
| Stripe URL settings | `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL` defined but runtime builds URLs from request | Unused settings |
| Message-expiration/cache constants | `CLEAR_MESSAGES_EXPIRATION_TIME` and several cache timeout constants are not consumed | Stale settings from an older message implementation |
| Redis wrapper | `store_in_hash` marked TODO delete; old `get_from_hash` implementation is commented | Deprecated/duplicated infrastructure code |
| S3 command local-file claims | Command help/docstrings say local or file path, but code always calls S3 | Documentation/implementation contradiction |
| Legal/privacy content | Claims no tracking/personal data while Analytics/accounts/Stripe/email/monitoring are implemented; terms contain placeholder contact/jurisdiction text | Public documentation is materially stale |
| Password change | Template duplicates the same block | Confirmed placeholder/editing error that breaks the route |
| Checkout success | `apps/subscriptions/templates/subscriptions/checkout_success.html` splits an `endblocktrans` tag and does not compile | Confirmed error breaks every rendered success/pending/unavailable result |
| Pro planning note | `plan-finishSubscription.prompt.md` remains untracked and describes some already-completed work (safe missing-subscription properties, portal, cancellation email, entitlement) plus still-open close/tests/error issues | Stale mixed-status plan; do not treat every bullet as current |
| Production support files | `nginx.conf`, `prod.txt`, and `celerybeat-schedule` were untracked | Operational state is not reproducible; `prod.txt` is sensitive and must not be committed |
| Frontend controls without backend support | Closing private chat implies releasing it; no backend leave action. Age/terms controls imply consent enforcement; server does not record it. | Partial workflows |
| Backend without dedicated UI/control | Topics, promotional flows, webhook ledgers, notification status mainly live in admin; bot eligibility has no explicit flag/control | Operational-only capability |

## Known risks

### Critical

| Severity | Finding | Evidence | Impact | Recommended action |
|---|---|---|---|---|
| Critical | **Confirmed: plaintext production-style credentials in an untracked file** | Working-tree `prod.txt` contained a Django secret, database/Redis credentials, and monitoring endpoint material during analysis | Credential theft and production compromise if shared, backed up, or accidentally committed; values may already be exposed elsewhere | Immediately rotate every real credential represented, remove the file securely, add a safe example template, and scan Git history/artifacts without echoing values |

### High

| Severity | Finding | Evidence | Impact | Recommended action |
|---|---|---|---|---|
| High | **Confirmed: cross-user HTML injection in chat browser** | `apps/chat/static/js/views/chatView.js::_createUserChatMessageElements` assigns untrusted WebSocket `message` to `paragraph.innerHTML`; server accepts arbitrary message content | A participant can inject markup/event-bearing elements into other users’ pages; possible session/user action compromise depending browser payload/CSP (no CSP configured) | Render every message with text nodes/safe linkification, add strict server payload limits, CSP, and browser regression tests |
| High | **Confirmed: guest identity/notification ownership can be forged** | `ChatView._has_valid_guest_session` checks username set membership but not Redis ID mappings; `ChatConsumer.connect` trusts anonymous cookies | Impersonated display names, forged user IDs, interception/misdirection of predictable personal notification groups, bypass of presence assumptions | Issue a signed opaque guest session/token and validate server-side ID↔username ownership on HTTP and socket connect; rotate/reject legacy cookies |
| High | **Confirmed: production image omits a required Stripe package** | `deployments/production/Dockerfile` installs `requirements.txt`; that file has no `stripe`, while root URLs import subscription/Stripe modules | Fresh production image cannot import/start payment-enabled Django code | Generate/maintain one production dependency source, build the image in CI, and add an import/startup smoke test |
| High | **Confirmed: tracked production Compose omits required runtime configuration** | `docker-compose.prod.yml` does not pass `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, Stripe, email, Sentry, or site variables; production settings default hosts empty | Host rejection/failed healthcheck and nonfunctional payment/email flows in the repository-defined deployment | Explicitly propagate all required variables or use a managed env file/secret store; validate Compose-rendered config and container health in CI |
| Medium (was High) | **Mitigated: concurrent Checkout requests can create duplicate billable subscriptions** | `create_pro_checkout_session` now locks the subscription row with `select_for_update` inside a transaction, sends a stable Stripe idempotency key for customer creation, and a per-user 10-minute windowed key for Checkout Sessions | Duplicate customers are prevented; duplicate sessions remain possible only for requests straddling a window boundary, since no pending session is persisted | Persist the open Checkout Session ID and reuse it while `status == "open"` to close the residual boundary gap; add concurrency tests against MySQL |
| High | **Likely: ordinary customer accounts are used as bot identities** | `BotCacheLoader._load_bot_users` selects every non-staff/non-superuser, including inactive; tests explicitly codify inactive inclusion | Automated speech can be attributed to real customers without consent; privacy/trust and account-reputation harm | Add explicit bot/service-account field/group/model and migrate only intended identities; expire/remove stale bot membership |

### Medium

| Severity | Finding | Evidence | Impact | Recommended action |
|---|---|---|---|---|
| Medium | **Confirmed: webhook claims can remain stuck forever** | Only `pending`/`failed` are claimable; no lease/timeout/reaper for `processing` | Crash after claim can permanently suppress an entitlement/payment event | Add claimed-at/lease semantics, recovery command/task, alerting, and active orchestration tests |
| Medium | **Confirmed: private-chat close does not free authoritative state** | Sidebar deletes DOM; consumer dict/Channels membership/Redis hash remain; no leave action | Free users cannot reliably reuse slots and restored/locked chats diverge from UI | Define count semantics and add idempotent leave action that updates connection, group, Redis, both peers as appropriate |
| Medium | **Confirmed: presence is not multi-connection safe** | One shared username/online key; every disconnect deletes it; no connection counter | Multiple tabs/devices cause false offline state and nickname/session invalidation | Track connection IDs/counts atomically and remove presence only after last connection; TTL each connection |
| Medium | **Confirmed: password-change page is broken** | Duplicate `content` blocks in `registration/password_change_form.html`; template loader raised `TemplateSyntaxError` | Authenticated users cannot change passwords through that route | Remove duplicate block and add auth template/request tests |
| Medium | **Confirmed: Checkout result page is broken** | `apps/subscriptions/templates/subscriptions/checkout_success.html` raises `TemplateSyntaxError` because `blocktrans` is parsed across later `elif` tags | Users returning from Stripe receive a server error instead of active/pending status | Correct tag formatting and add valid/missing/mismatched/unavailable render tests |
| Medium | **Likely: custom admin mishandles passwords** | `apps/users/admin.py::UserAdmin` subclasses `admin.ModelAdmin` rather than Django auth `UserAdmin` while exposing `password` | Admin may expose/edit hashes or create unusable raw-password users | Subclass Django `UserAdmin`, configure add/change forms, and verify hash-safe create/change behavior |
| Medium | **Confirmed: no user-message validation/rate limit and malformed JSON is unhandled** | `handle_send_message` forwards any `message`; `receive` calls `json.loads` without guard | Resource abuse, oversized/invalid payload failures, noisy disconnects, spam | Define schema/type/size/rate rules and recoverable error events; test boundary/abuse cases |
| Medium | **Confirmed: invalid WebSocket close code used** | `handle_send_message` calls `consumer.close(code=401)` | Protocol/server errors rather than predictable client closure | Use an application code in 4000–4999 and integration-test Daphne/communicator behavior |
| Medium | **Likely: invoice emails can be sent concurrently more than once** | Notification has no processing claim/lock; multiple queued tasks see non-`sent` state | Duplicate customer emails | Atomically claim delivery, add attempts/lease, and make task idempotency explicit |
| Medium | **Confirmed: non-canonical private group names** | `get_private_group_name(user1,user2)` preserves argument order | Same pair can have two channels/state records depending inviter | Sort stable IDs or persist a canonical chat ID; migrate/accept legacy names carefully |
| Medium | **Confirmed: stale Redis usernames/bot IDs may persist** | Active username and bot-ID sets have no TTL; cleanup is best effort; bot loader has no removal | Nicknames remain blocked, counts and bot checks drift | Use per-identity leases/sets with cleanup/reconciliation and explicit bot-cache invalidation |
| Medium | **Likely: production database/Redis ports may be exposed** | Compose publishes 3306/6379 to host interfaces | External attack surface if firewall is permissive | Remove public bindings or bind loopback/private network; verify VPS firewall |
| Medium | **Confirmed: CI omits users/subscriptions tests and production image build** | `.github/workflows/django-ci.yml` runs only `apps.chat` and Pipenv | Payment/auth/dependency regressions can pass CI | Run full suite, build/smoke-test production image, and add frontend/security tests |
| Medium | **Confirmed: privacy/legal behavior contradicts implementation** | `chat_connect/templates/base.html` loads Analytics; accounts/Stripe/email/Sentry/CloudWatch collect/process data; privacy/terms say otherwise | Compliance and user-trust exposure | Obtain legal/product review and align consent, disclosures, retention, analytics behavior, and contact details |

### Low

| Severity | Finding | Evidence | Impact | Recommended action |
|---|---|---|---|---|
| Low | **Confirmed: online counts are fabricated/inconsistent** | Home randomizes 55–63; room adds 60 | Misleading UI/analytics and debugging confusion | Make simulation explicit/configurable or report actual counts consistently |
| Low | **Confirmed: health endpoint is shallow** | Always returns OK without dependency checks | Orchestrator can report healthy while DB/Redis/worker/payment paths fail | Add separate liveness/readiness with bounded dependency checks |
| Low | **Confirmed: unused/deprecated settings and Redis methods** | TODO/commented code and unreferenced feature flags/constants | Maintenance confusion | Remove after compatibility audit or wire documented behavior |
| Low | **Confirmed: help text overstates local import support** | Both commands always call boto3 | Operator confusion | Implement local read path or correct help/docs and validate JSON |
| Low | **Needs verification: untracked NGINX config lacks WebSocket upgrade headers** | `nginx.conf` proxy only sets ordinary forwarding headers | WebSockets fail if this exact file is deployed | Confirm active VPS config; add upgrade headers and configuration test if used |

## Technical debt

- Browser responsibilities are concentrated in `apps/chat/static/js/views/chatView.js` (578 lines) and `apps/chat/static/js/views/sideBarView.js` (355) with no JS tests or type/schema layer.
- Subscription state is internally disciplined but centralized in a 359-line service that mixes queries, mappings, transitions, cancellation/provider handling, and logging.
- Users and subscriptions are tightly coupled: the `User` model imports subscription choices and signup creates subscription state, while subscriptions reference the custom user model.
- Chat state uses low-level Redis wrappers with inconsistent naming, obsolete methods, and multiple non-expiring sets; identity mappings are written but not used for authorization.
- Business rules are duplicated across backend constant, browser constant, template string, sidebar count, and consumer dict.
- Public legal content, README, Compose, dependencies, CI, and current implementation disagree in material ways.
- Weak typing is common around Stripe SDK objects, consumers, request data, Redis results, and JavaScript payloads.
- No frontend lint/tests, Python lint/type enforcement, pre-commit, Markdown lint, or production image test exists.
- Test suites are fast and broad at unit level but heavily mock infrastructure; MySQL locking, Redis/Channels, Celery, Stripe webhook HTTP, and browser behavior lack integration coverage.
- Webhook/invoice ledgers have no retention, cleanup, or operational recovery policy.

## Suggested roadmap

### 1. Security and data-integrity fixes

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Rotate/remove exposed credentials | Prevent external compromise; working-tree `prod.txt`, deployment secrets/config | Access to providers/VPS | Provider rotation readback, history/secret scan, ensure file absent/ignored | medium |
| Eliminate chat HTML injection | Direct cross-user input path; `apps/chat/static/js/views/chatView.js`, `apps/chat/static/js/utils/create_elements.js`, send handler | Decide link rendering and CSP | Browser tests with hostile markup; CSP/security header check | medium |
| Replace guest cookie trust with signed server identity | Fix impersonation/notification ownership; `ChatView`, `ChatConsumer`, Redis keys | Guest session/token design and legacy transition | Forged-cookie negative tests and two-client socket tests | large |
| Repair production dependency/config pipeline | Make deployments start safely; `requirements.txt`, Dockerfile, Compose, CI | Secret/environment ownership | Build image, import/start Daphne, readiness, Stripe/email config checks | medium |
| Make Checkout idempotent | Prevent duplicate billing; Checkout service/model/Stripe adapter | Define pending Checkout intent/state | Concurrent-request and provider-idempotency tests | large |

### 2. Correctness and missing business rules

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Define private-chat count/leave semantics | Current UI/server/TTL disagree; action constants/handlers, Redis service, JS | Product decision: simultaneous vs relationship limit | Fourth-invite, leave/reuse, reconnect, peer cleanup, bot cases | large |
| Canonicalize private pair IDs | Avoid duplicate pair channels; `apps/chat/websocket/group_names.py`, stored hashes/JS | Legacy compatibility/migration plan | Order symmetry and restore tests | medium |
| Make presence multi-connection safe | Prevent false offline/stale names; activity/consumer/Redis | Connection-ID schema | Two-tab connect/disconnect/TTL integration tests | medium |
| Define bot identity explicitly | Stop customer impersonation; user/bot model/admin/cache loader | Data migration/seed ownership | Only explicit bots load; deletion/inactive/cache invalidation tests | medium |
| Align subscription statuses/access policy | Clarify `expired`, active-without-end, failed-payment mapping, reactivation | Billing/product decisions | State transition table tests and UI/entitlement consistency | medium |

### 3. Missing tests

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Activate webhook orchestration/view tests | Critical idempotency path is 26% covered/commented | Stuck-claim design if changed | Pending/failed/duplicate/unknown/signature/500 cases | medium |
| Replace inert consumer helpers with integration tests | Connect/disconnect path is 29% covered | Guest identity changes | Session/guest/malformed/action/multi-client tests | medium |
| Cover accounts/auth/admin templates | Confirm password/admin safety and signup aggregate | Password template/admin fix | Request tests and password hash assertions | medium |
| Cover Checkout/portal/tasks/commands | Payment initiation and ops are under-tested | Idempotency/error decisions | Provider mocks plus transactional/concurrency/integration tests | large |
| Expand CI and add frontend security tests | Prevent recurrence across all apps/browser | Browser runner choice | Full suite, production image smoke, JS DOM tests in CI | medium |

### 4. Incomplete product functionality

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Fix password change and auth UX | Confirmed broken route | None | Authenticated GET/POST/change-login tests | small |
| Complete payment failure/update journey | Tasks never provide direct update URL | Portal strategy | Email and portal end-to-end tests | medium |
| Add moderation/safety or narrow claims | Adult stranger chat currently has no controls | Product/legal policy | Permissions, report/block flows, abuse tests—or updated boundaries | large |
| Align legal/privacy/consent UI | Current public claims conflict with actual processing | Legal/product review | Content review, analytics consent/environment tests | medium |

### 5. Architecture improvements

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Introduce a stable entitlement interface | Reduce users↔subscriptions/chat coupling | Status policy | Unit tests against missing/free/past-due/Pro rows | medium |
| Split browser chat/socket/state/rendering | Reduce 578/355-line hotspots and make tests possible | JS test tooling | Module unit/DOM tests and unchanged protocol contract | large |
| Clean Redis boundary/key lifecycle | Remove obsolete code and centralize ownership/TTL | Guest/presence/private-chat designs | Contract tests against real Redis | medium |
| Add webhook recovery/retention services | Operationally manage ledgers | Retention policy | Lease recovery, replay authorization, cleanup tests | medium |

### 6. Performance improvements

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Make bot sent selection atomic | Multiple workers can duplicate messages | Redis design | Concurrent worker test with one winner | small |
| Review cache/Redis scan behavior | `has_online_users` scans keys each 3-second production tick | Presence redesign | Redis command/load measurement and constant-time alternative | medium |
| Add indexes only from measured queries | Stripe subscription ID/event/status queries may grow | Production query evidence | MySQL `EXPLAIN`, migration tests | medium |

### 7. Developer-experience improvements

| Priority item | Why / main files | Dependencies | Suggested verification | Scope |
|---|---|---|---|---|
| Unify dependency generation | Pipenv vs requirements drift caused production blocker | Packaging choice | Lock/export consistency and image build | small |
| Make setup/config self-validating | README/Compose defaults are incomplete | Env ownership | Checked example env, startup validation, fresh-machine rehearsal | medium |
| Add lint/type/pre-commit/Markdown checks | No enforced quality baseline | Agree initial rules | CI passes on existing code after scoped baseline | medium |
| Make imports truthful and testable | S3-only behavior contradicts help | Choose local support vs docs | Local/S3 JSON validation and command tests | small |

No time estimates are provided; scopes are relative implementation sizes only.
