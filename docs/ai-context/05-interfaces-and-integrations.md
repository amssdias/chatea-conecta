# Interfaces and Integrations

> Last analyzed commit: `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` on branch `003-user-pro`  
> Analysis date: 2026-08-02

## HTTP interfaces

`[lang]` is `en` or `es`. Django’s locale prefix is enabled for all application/admin/account/subscription pages; health, robots, sitemap, and Stripe webhook are deliberately unprefixed. There is no REST API, serializer, or token endpoint.

| Method | Path | Authentication / permission | Input | Output | Main implementation |
|---|---|---|---|---|---|
| Any (intended GET) | `/health/` | Public | None | JSON `{"status":"ok"}`; does not probe dependencies | `chat_connect/views.py::health_check` |
| Any (intended GET) | `/robots.txt` | Public | None | Text rules plus production sitemap URL | `robots_txt` |
| Any (intended GET) | `/sitemap.xml` | Public | None | XML with English/Spanish alternates | `multilingual_sitemap` |
| POST; others 405 | `/subscriptions/payments/stripe/webhook/` | Stripe signature; CSRF-exempt | Raw body, `Stripe-Signature` header | Empty 200, invalid signature/payload 400, handler exception 500 | `apps/subscriptions/views/webhooks.py::stripe_webhook_view` |
| GET | `/[lang]/` | Public | Guest cookies | Landing page, or redirect to live chat when username cookie exists | `HomeChatView` |
| GET/POST | `/[lang]/live-chat/` | Session identity or guest cookies/nickname | POST `username`; GET cookies | Chat HTML/cookies or redirect/error | `ChatView` |
| GET | `/[lang]/faq/`, `privacy-policy/`, `terms/`, `about/`, `contact/`, `security/` | Public | None | Static rendered page | `apps/chat/urls.py` `TemplateView`s |
| Django admin methods | `/[lang]/chatea-admin/...` | Staff plus model permissions | Admin forms | Admin HTML/redirects | `django.contrib.admin` and app admins |
| GET/POST | `/[lang]/accounts/signup/` | Anonymous; authenticated users redirected home | username, email, two passwords, hidden `intent` | Account/session plus chat or Stripe redirect | `apps/users/views/signup.py::SignUpView` |
| GET/POST | `/[lang]/accounts/login/` | Anonymous; authenticated users redirected | Django authentication form | Session/cookies; redirect live chat | `CustomLoginView` |
| POST | `/[lang]/accounts/logout/` | Public/session-aware; CSRF applies | Cookies/session | Session/cookies cleared, Redis username removed, redirect home | `CloseChatSessionView` |
| Built-in auth family | `/[lang]/accounts/password_change/`, `password_change/done/`, `password_reset/`, `password_reset/done/`, `reset/<uidb64>/<token>/`, `reset/done/` | Django defaults; password change requires login | Standard Django forms/tokens | Templates/email/redirects | `django.contrib.auth.urls` and `chat_connect/templates/registration/` |
| POST | `/[lang]/subscriptions/checkout/pro/` | `login_required`; CSRF | None beyond session | Redirect to Stripe Checkout; provider errors currently 500 | `create_pro_checkout_session_view` |
| Any (intended GET) | `/[lang]/subscriptions/checkout/success/?session_id=...` | `login_required` | Stripe Checkout session ID | HTML status `active`, `pending`, `missing_session`, `unavailable`; mismatch 403 | `checkout_success_view` |
| Any (intended GET) | `/[lang]/subscriptions/checkout/cancel/` | `login_required` | None | Cancel/retry HTML | `checkout_cancel_view` |
| Any (intended GET) | `/[lang]/subscriptions/detail/` | `login_required` | None | Local subscription summary/actions | `subscription_detail_view` |
| POST | `/[lang]/subscriptions/cancel/` | `login_required`; CSRF | None | Django message and redirect detail | `cancel_subscription_view` |
| POST | `/[lang]/subscriptions/billing-portal/` | `login_required`; CSRF; stored Stripe customer required | None | Redirect to Stripe Portal or message/detail | `create_billing_portal_session_view` |
| GET | `/__reload__/...` | Development only | Browser reload protocol | Reload support | `django_browser_reload.urls` |

Route shadowing note: `apps.users.urls` is included before `django.contrib.auth.urls` at the same `/accounts/` prefix, so custom login/logout views resolve incoming requests while global Django URL names such as `login` still reverse to the same paths.

## WebSocket interface

### Connection

| Item | Contract |
|---|---|
| Route | `/ws/chat/` (not locale-prefixed) |
| Consumer | `apps/chat/consumers.py::ChatConsumer` |
| Origin | `AllowedHostsOriginValidator` around `AuthMiddlewareStack` |
| Authentication | Django session when authenticated; otherwise `username` and `user_id` cookies |
| Accept sequence | Validate identity → accept → online marker → active username → restore private groups |
| Reject | Close code `4001`, reason `Invalid chat identity` |
| Connection state | `consumer.groups: set[str]`; `consumer.private_chats: dict[target_id, group]` |
| Disconnect | Notify private peers, discard all groups, broadcast counts, remove username, delete online marker |
| Limits | Per connection, eight `send_message` attempts are allowed in a five-second sliding window; the next attempt closes with `4008`. Reconnects and parallel sockets have independent quotas. Channel layer capacity/expiry are separate library controls. |

### Incoming messages

| `type` | Payload | Behavior | Error |
|---|---|---|---|
| `heartbeat` | No additional fields | Refresh `USER_ONLINE_KEY` to 90 seconds | Redis exceptions propagate |
| `register_group` | `group: string` | Trim/lowercase, reject private prefix, join group and personal notification group, broadcast count | Invalid closes `4001`; private name sends `error_action` |
| `private_invite` | `target_user_id` coercible to string | Enforce self/duplicate/Pro/free/online rules, join/save group, notify target | Missing/self/duplicate silently ignored; offline event; limit sends dedicated denial |
| `send_message` | `group: string`, `message: nonblank string` (max 1,000 characters) | Normalize group; enforce membership only for `private-`; validate and rate-limit before broadcast | Invalid group closes with code `401`; private nonmember or invalid message gets `error_action`; exceeding eight attempts in five seconds closes with `4008` |
| Unknown/missing | Any | No handler | `{"type":"error_action","error":"Invalid action"}` |

`ChatConsumer.receive` converts malformed JSON and non-object JSON roots into an `Invalid payload` `error_action`.

### Outgoing messages

| `type` | Payload | Source |
|---|---|---|
| `notify_users_count` | `users_online` | Room count broadcast |
| `send_message` | `message`, `username`, `userId`, `groupChatName` | User/bot `chat.message` event |
| `private_invite` | `fromUserId`, `privateGroup` | Target’s personal notification group |
| `private_chat_participant_offline` | `userId`, `privateGroupId` | Disconnect/offline target |
| `private_chat_participant_online` | `userId`, `privateGroupId` | Restoring participant |
| `private_chats_restored` | `privateChats` object mapping target ID→group | Reconnect restore |
| `private_chat_access_denied` | `reason`, localized `message`, `targetUserId` | Free limit; current reason is `private_chat_limit_reached` |
| `error_action` | `error` | Unknown action, prohibited group registration/send |

### Group names and Redis

- Public browser group: `chatea`.
- Private group: `private-{inviter_id}-{target_id}` lowercased, spaces replaced with hyphens. IDs are not sorted.
- Personal notification group: `chatconnect.user.inbox.{user_id}`.
- Redis presence/private state is detailed in [03-data-model-and-state.md](03-data-model-and-state.md).

## Internal service interfaces

| Function/class | Responsibility | Inputs | Output | Side effects / main callers |
|---|---|---|---|---|
| `register_user_on_redis` | Allocate/register chat ID and mappings | username, optional user ID | ID | Redis set/strings; chat/signup/login views |
| `mark_user_online`, `is_user_online`, `cleanup_user_presence` | Presence lifecycle | user ID; cleanup also username | none/bool | Redis; consumer/actions |
| `save_user_private_chat_group` | Save target→group with TTL | user, target, group | none | Redis hash; invite/consumer |
| `restore_user_private_chat_groups` | Rejoin saved groups and notify browser/peers | consumer | none | Redis, Channels; consumer connect |
| `user_has_pro_access` | Async-safe entitlement query | Django user | bool | DB query; private invite |
| `BotCacheLoader.load` | Load eligible users/topics/messages | optional store | none | MySQL reads, Redis writes; message service |
| `BotMessageService.get_message_to_send` | Select unsent bot payload | none | typed dict or `None` | Redis mark; bot task |
| `create_user_account_from_signup_form` | Atomic account aggregate creation | validated form | user | User/profile/subscription rows; signup |
| `create_pro_checkout_session` | Create/reuse customer and Checkout | user, request | Stripe session | DB write, Stripe calls; signup/checkout view |
| `get_user_subscription` | Query current user row | user | row or `None` | detail/portal/cancel/access callers |
| `sync_user_subscription_from_checkout` | Establish new current Stripe subscription | `StripeSubscriptionSyncDTO` | locked row | Complete DB snapshot; Checkout handler |
| `mark_subscription_paid` | Activate matching current subscription | `PaidSubscriptionDTO` | row or `None` for stale | Locked DB update; invoice handler |
| `mark_subscription_payment_failed` | Map matching provider status | `FailedSubscriptionPaymentDTO` | row or `None` | Locked DB update; invoice handler |
| `sync_user_subscription_from_stripe` | Refresh matching current subscription | `StripeSubscriptionSyncDTO` | row or `None` | Locked DB update; update handler |
| `mark_subscription_deleted` | Finalize matching subscription | deletion DTO | row or `None` | Locked DB update; deletion handler |
| `cancel_user_subscription` | Schedule period-end cancellation | user | row | Stripe update then local save; cancel view |
| `handle_stripe_webhook_event` | Claim/deduplicate/dispatch verified event | Stripe event | bool | Event ledger, domain handlers; webhook view |
| `queue_invoice_email_notification` | Idempotently create and enqueue invoice mail | invoice ID, type, user ID, optional URL | bool | DB plus Celery on commit; invoice handlers |

Future code should reuse these interfaces rather than duplicating provider/state logic in views.

## External integrations

### Stripe

| Aspect | Implementation |
|---|---|
| Purpose | Monthly Pro Checkout, customer reuse, subscription retrieval/cancel, Billing Portal, invoice links, signed webhooks |
| SDK/protocol | `stripe` Python SDK; lock has 15.1.0; API version pinned by `STRIPE_API_VERSION`; cached `StripeClient` with two network retries |
| Configuration | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_MONTHLY_PRICE_ID`; `STRIPE_SUCCESS_URL`/`STRIPE_CANCEL_URL` are defined but unused |
| Data sent | User email and ID metadata/customer metadata; price ID; absolute success/cancel/portal return URLs; subscription cancellation flag |
| Data received | Customer/session/subscription/invoice objects; signed event IDs/types/objects/status/timestamps/URLs |
| Authentication | Secret key for API; webhook HMAC signature verification through SDK |
| Events | Checkout completed, invoice paid/failed, subscription updated/deleted |
| Retry | SDK network retries=2; webhook handler errors return 500 for Stripe redelivery; no local webhook retry scheduler |
| Idempotency | Event ID ledger; current-subscription matching; invoice/type unique row. No idempotency key for customer/Checkout/cancellation API calls. |
| Tests | Provider calls mocked in subscription service/handler tests; no live/local Stripe CLI configuration in repository |
| Local behavior | Requires Stripe variables in process environment. Compose files do not currently pass them into app/worker containers. |

### SMTP email

- Configuration: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`; optional `SUPPORT_EMAIL` is read but not defined in base settings.
- Data: account email, invoice/subscription links/status text. Password reset uses Django auth email templates.
- Error/retry: mail wrapper converts header/SMTP/other failures to `EmailDeliveryError`; Celery tasks retry all exceptions up to three times with backoff. Tests use locmem backend.
- No delivery provider webhook, bounce handling, or audit log beyond `StripeInvoiceNotification`.

### Redis

- Protocol/client: Django Redis cache backend, `channels_redis`, `redis` sync/async clients, and Celery Redis broker.
- Configuration: `REDIS_PROTOCOL`, `REDIS_PASSWORD`, `REDIS_HOST`, `REDIS_PORT`, plus three DB indices.
- Authentication: password embedded in constructed Redis URL; do not log it.
- Application serialization: strings, sets, and hashes with decoded responses; Channels/Celery use their libraries’ formats.
- Failure handling: startup broker retry is enabled; application Redis calls generally propagate. No fallback chat mode.

### MySQL

`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` configure the only durable database. Django ORM/migrations are the protocol. No read replicas, failover, or connection health probe are configured.

### AWS S3 and CloudWatch

- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` configure boto3/watchtower through standard provider resolution.
- S3 import commands receive bucket/key options, download JSON, and write users/topics/messages. No upload workflow exists.
- Production logging sends INFO+ to a fixed CloudWatch log group with stream name derived from `APP_NAME`; `SKIP_CLOUDWATCH` replaces the logging configuration for checks/environments without AWS.
- Import tests/mocks and CloudWatch integration tests are absent.

### Sentry

Production initializes `sentry_sdk` with `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_ENVIRONMENT`, Django/Celery integrations, and continuous profiling experiment. Warning+ logs also use Sentry’s event handler. A missing DSN disables transport according to the SDK, but this repository does not test initialization.

### Google Analytics

`chat_connect/templates/base.html` loads Google Tag Manager’s `gtag.js` and configures one measurement ID for every page using the base template, including auth/chat/subscription pages. No consent gate or environment flag appears in code. This directly contradicts public “no tracking” copy.

### GitHub Actions, SSH, and NGINX

- CI installs the Pipenv environment and runs chat tests/coverage, migration drift, and a production deployment check.
- Manual deployment uses `appleboy/ssh-action`, fetches/resets VPS `master`, rebuilds/restarts Compose, compiles messages, optionally flushes Redis/runs migrations/collectstatic, then restarts host NGINX.
- `nginx.conf` existed untracked in the analyzed working tree. Its proxy section lacks WebSocket `Upgrade`/`Connection` headers; whether the VPS uses it is unconfirmed.

## Authentication and authorization

- **HTTP account auth:** Django database passwords and database-backed sessions; password validators are disabled in development but active in base/production.
- **CSRF:** standard middleware protects form POSTs. Stripe webhook is exempt because the SDK signature is its authentication. No CORS package/config exists.
- **WebSocket auth:** `AuthMiddlewareStack` reuses Django session. Anonymous connections trust cookies; the cookies are HTTP-only but not signed by application code and can be manually supplied by a client.
- **Authorization:** `login_required` guards billing pages; subscription ownership is derived from `request.user`; private sends check connection membership. Public groups/messages have no role permission.
- **Trusted data:** session user, verified Stripe event, and database row are intended trusted sources. Guest cookies, group names, target IDs, message text, request Host-derived absolute URLs, and all browser flags are untrusted.
- **Sensitive checks:** do not replace `user_has_pro_access(consumer.user)` with cookie/user-ID lookup; do not activate subscription from success-page parameters; keep webhook signature verification before parsing/dispatch.

## Events and asynchronous communication

| Event/channel | Producer | Consumer | Ordering/idempotency |
|---|---|---|---|
| WebSocket action JSON | Browser | `dispatch_action` | Per-connection arrival order; no sequence IDs/retry |
| Channels `chat.message`, notifications | handlers/tasks | consumer event methods | Redis channel-layer semantics; no durable delivery/history |
| Celery bot tick | Beat | worker | Periodic, probabilistic, no task-level uniqueness |
| Invoice email task | webhook transaction on commit | worker | Notification uniqueness helps dedupe; concurrent sends still possible |
| Cancellation email task | deletion handler | worker | Webhook event claim limits enqueue; no delivery ledger |
| Stripe webhook | Stripe | HTTP view/service | Event-ID claim; provider redelivery on non-2xx; stuck processing has no recovery |
| Django signals | — | — | None are implemented; side effects are explicit |

There is no dead-letter queue, task result backend, task audit dashboard configuration, or explicit global event ordering guarantee.
