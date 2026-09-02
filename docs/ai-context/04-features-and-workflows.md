# Features and Workflows

> Last analyzed commit: `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` on branch `003-user-pro`  
> Analysis date: 2026-08-02

Status labels assess the repository as implemented and tested, not product desirability.

## Public pages, localization, and SEO

**Purpose and actors.** Any visitor can read the English/Spanish landing, FAQ, privacy, terms, about, contact, and security pages.

**Entry points/components.** `chat_connect/urls.py` uses `i18n_patterns`; `apps/chat/urls.py` maps pages; templates live under `chat_connect/templates/`; `ChatStaticViewSitemap`, `multilingual_sitemap`, `robots_txt`, and `hreflang_context` generate discovery metadata.

**Workflow.** Locale middleware selects language, the route renders a template, and the context processor builds absolute `hreflang` links from `settings.LANGUAGES` and `SITE_URL`. Sitemap/robots/health live outside locale prefixes.

**Rules/failures.** Live chat is excluded from the sitemap and gets `noindex,nofollow`. `ChatStaticViewSitemap.languages` duplicates the configured English/Spanish list rather than reading settings. Production whole-site caching may cache rendered public responses for 15 minutes.

**Tests.** Only basic home/login/logout URL resolution and home rendering are directly tested (`apps/chat/tests/urls/test_urls.py`, `views/test_home_chat.py`). Sitemap, robots, hreflang, static pages, and translations are not covered.

**Status: Mostly complete.** Routes/templates exist, but legal copy contradicts implemented analytics/accounts/payments, and some placeholder contact/jurisdiction text remains in terms templates.

## Guest chat admission and identity

**Purpose and actors.** An anonymous visitor can enter chat with a temporary nickname.

**Entry points/components.** `/[lang]/` landing form; `/[lang]/live-chat/`; `HomeChatView`, `ChatView`, `register_user_on_redis`; `chat_connect/templates/index.html`; cookies and Redis mappings.

**Main workflow.** The visitor submits a nickname. `ChatView` strips it, enforces `USERNAME_REGEX`, rejects active/database duplicates, creates a base-36 Redis ID, registers the lowercase username and mapping keys, renders chat, and sets HTTP-only cookies. A later GET requires both cookies and active-set membership, then refreshes registration.

**Business rules/failures.** Empty/invalid/taken names redirect home with a Django message. Missing/invalid session cookies redirect and are deleted. Age/terms checkboxes are client-only. Redis errors are not caught. The username membership check does not verify that the cookie ID belongs to that username.

**Tests.** `apps/chat/tests/views/test_chat.py` covers validation, duplicate checks, cookies, redirects, guest and authenticated context. It mocks Redis and does not test forged ID/username pairs.

**Status: Partial.** Happy-path behavior is well tested, but guest ownership is not authenticated and can be forged; see `07`.

## Accounts, login/logout, and password flows

**Purpose and actors.** Visitors can create durable accounts; users can log in/out and use Django password management.

**Entry points/components.** `apps/users/urls.py`, built-in `django.contrib.auth.urls`, `SignUpForm`, `SignUpView`, `CustomLoginView`, `CloseChatSessionView`, `create_user_account_from_signup_form`, registration templates.

**Main workflow.** Signup validates Django passwords plus normalized case-insensitive-unique email, atomically creates user/profile/subscription, logs in, registers Redis identity, and either enters chat or redirects to Pro Checkout based on `intent`. Login authenticates through Django, registers the database ID, sets cookies, and enters chat. Logout POST removes the username from Redis when present, ends the Django session, deletes both chat cookies, and redirects home.

**Failures.** Signup form errors render normally; Checkout errors after Pro-intent signup are uncaught and leave the account created/logged in. Login relies on Django form errors. Logout Redis failures are uncaught. Password reset uses SMTP; the password-change form fails template compilation because it defines `{% block content %}` twice (`chat_connect/templates/registration/password_change_form.html`).

**Tests.** Logout is covered in `apps/users/tests/views/test_close_chat_session.py`. Signup, login, password flows, email race/uniqueness, service transaction behavior, and admin password handling have no direct tests. A template-loader check during this analysis confirmed the password-change syntax failure.

**Status: Partial.** Core account creation/login/logout exists; password change is confirmed broken and coverage is narrow.

## Public real-time chat

**Purpose and actors.** Connected guests/accounts exchange ephemeral messages in the shared `chatea` room.

**Entry points/components.** `/ws/chat/`; `ChatConsumer`; `heartbeat`, `register_group`, `send_message`; `ChatSocket`, `ChatView`, `SideBarView`; Channels Redis layer.

**Main workflow.** On browser socket open, `ChatSocket` starts a 30-second heartbeat and registers `Chatea` (normalized to `chatea`). The server accepts identity, marks presence, joins the public and personal notification groups, returns the inflated online count, and broadcasts each submitted message as `chat.message`. Consumer methods convert it to client `send_message`; the browser appends it to the current chat.

**Rules/failures.** A missing/invalid group closes the connection; unknown action sends `error_action`. A `private-` group cannot be registered ordinarily. User messages have no server-side type/length/rate/content validation. Malformed JSON is unhandled. The first message in a visual message cluster is assigned to `innerHTML`, enabling cross-user HTML/script-adjacent DOM injection; subsequent messages use text nodes/link generation.

**Tests.** Action dispatch, group validation, registration, broadcasts, and action handlers are unit tested under `apps/chat/tests/services/actions/` and `websocket/`. `apps/chat/tests/consumers/test_consumer.py` contains only `_test_*` helpers, so no true consumer connection/message test runs. Browser JS has no automated tests.

**Status: Partial.** Transport and units exist, but identity, message sanitization, payload validation, and actual socket coverage are insufficient.

## Private chat, presence, and restoration

**Purpose and actors.** A participant opens a direct transient channel from a public message; free users have limited initiation, Pro users do not.

**Entry points/components.** `private_invite`; `handle_private_invite`; private group/broadcast/registration helpers; `USER_PRIVATE_CHATS_KEY`; sidebar/chat JS.

**Main workflow.** The inviter selects a public message author. Browser pre-checks its sidebar limit, creates a local modal, and sends the target ID. Server ignores self/duplicate requests, checks database Pro access and free count, determines online/bot status, registers/saves the inviter, and sends an invitation to the target’s personal group. The target consumer joins/saves the group and informs its browser. Both can send only while their connection belongs to the private group. On reconnect, the hash is loaded, groups rejoined, the browser mapping restored, and peers notified online.

**Business rules/failures.** Free limit is exactly three existing `consumer.private_chats` entries. Denial sends `private_chat_access_denied` rather than closing. Offline humans return an offline event; bots are allowed. Disconnect notifies peers and leaves Channels groups but retains Redis hashes until 30-minute expiry. Closing a sidebar item removes DOM only; there is no leave/delete action, so the server-side slot remains. Incoming invites are not checked against the receiver’s free limit. Pair group naming is order-dependent.

**Tests.** Private invite online/offline/duplicate/authenticated-Pro-source behavior, private membership rejection, restoration, Redis TTL, broadcasts, and group names are tested. Missing coverage includes explicit free-vs-Pro fourth invite cases, received-over-limit behavior, leave/slot reuse, canonical naming, real multi-consumer exchange, and TTL integration.

**Status: Partial.** Entitlement exists server-side, but counting/close semantics are incomplete and state can become confusing or stale.

## Online counts and connection cleanup

**Purpose and actors.** The UI shows activity and private peers’ online/offline state.

**Entry points/components.** `apps/chat/services/activity.py`, heartbeat action, `ChatConsumer.connect/disconnect`, `HomeChatView`, `notify_group_online_count`.

**Workflow/rules.** A socket sets an online key for 90 seconds and heartbeats every 30. Disconnect removes its username and online marker, leaves groups, and notifies partners. The landing count is randomized to 55–63 when actual active usernames are ≤5; the room count is always actual set size plus 60.

**Failure paths.** No connection reference count exists: one of multiple tabs disconnecting clears shared presence for the other. Failed disconnect cleanup can leave a username indefinitely because the set has no TTL. The online marker eventually expires.

**Tests.** Presence functions and broadcasts are unit tested. Multi-socket behavior and cleanup failure are not.

**Status: Mostly complete by declared behavior, with known consistency limitations.** Count inflation is explicit implementation, not a measurement bug.

## Automated bot traffic and content imports

**Purpose and actors.** Scheduled messages make the public room appear active; operators seed sender accounts and text from S3.

**Entry points/components.** Beat schedule; `send_random_messages_tick`; `BotMessageService`, `BotCacheLoader`, `BotMessageRedisStore`; `Topic`, `ConversationFlow`; `create_random_users`, `create_topics_and_messages` commands.

**Main workflow.** Beat enqueues ticks. A worker checks for any `user:online:*` key, skips about 10% of ticks, loads bot users/topics/non-promotional messages into one-week Redis caches if needed, selects an unsent message within ten topic attempts, marks it for one hour, and broadcasts it to `chatea`.

**Rules/failures.** Every non-staff/non-superuser user—including inactive/real customers—is a bot. Promotional flows are never loaded. S3/import/provider errors are logged/raised; user imports continue per record, while topic import can partially create data. Help text claims local-file support, but both commands always call S3. Concurrent tasks can select the same message before either marker is set.

**Tests.** Cache loader/store/selection have broad unit coverage, explicitly including inactive-user selection and promotional exclusion. The Celery task and both management commands lack direct tests.

**Status: Mostly complete service layer; Partial operational/product definition.** Bot identity classification and import behavior are unsafe/unclear.

## Pro Checkout

**Purpose and actors.** Authenticated free users create a monthly Stripe subscription Checkout session.

**Entry points/components.** `POST /[lang]/subscriptions/checkout/pro/`; signup `intent=pro`; `create_pro_checkout_session`; Stripe customer/Checkout adapters; success/cancel templates.

**Main workflow.** The service gets/creates the local row, rejects `active`, creates/reuses a Stripe customer, builds absolute success/cancel URLs from the request, and creates Checkout with the configured price, user reference, and metadata. The success view retrieves the session, verifies logged-in ownership, then intends to report `active` only if local webhook-updated state grants Pro; otherwise `pending`. Cancel renders a working POST retry form.

**Failure paths.** Stripe errors in creation are uncaught. Concurrent requests have no row lock or provider idempotency key and can create multiple customers/sessions/subscriptions. Missing/retrieval-failed success sessions are assigned `missing_session`/`unavailable`; mismatched sessions return 403. However, `apps/subscriptions/templates/subscriptions/checkout_success.html` is confirmed not to compile: a split `endblocktrans` tag causes Django to treat a later `elif` as nested inside `blocktrans`. Every non-403 success-page render therefore fails before showing status.

**Tests.** No direct tests cover Checkout creation or result/cancel views. Webhook Checkout handler and subscription sync are tested.

**Status: Partial.** Activation safety in the view/service is correct, but the result template is broken and payment initiation needs idempotency, error UX, deployment dependencies, and direct tests.

## Subscription detail, Billing Portal, and cancellation

**Purpose and actors.** Logged-in users inspect access, update payment configuration, and stop renewal.

**Entry points/components.** subscription detail, billing portal, cancel views/templates; `cancel_user_subscription`; Stripe adapters.

**Main workflow.** Detail derives presentation fields from the user’s row. Past-due users get a POST Billing Portal action; active users get a cancellation confirmation. Portal creation uses the stored Stripe customer and returns to detail. Cancellation validates local state/ID, asks Stripe to cancel at period end, then updates the flag/end date for immediate UI feedback.

**Failure paths.** Missing customer/provider portal error yields messages. Cancellation maps service errors to messages and always redirects. Concurrent cancellation is not locked. There is no undo/reactivation workflow. Detail/Checkout result functions are not method-restricted even though used as GET pages.

**Tests.** Cancellation service and view have extensive tests. Detail and Billing Portal have no direct tests.

**Status: Mostly complete, with concurrency and coverage gaps.**

## Stripe webhook synchronization

**Purpose and actors.** Stripe is the external actor that authoritatively drives local entitlement and notification work.

**Entry points/components.** Non-localized `POST /subscriptions/payments/stripe/webhook/`; signature adapter; event claim service; handler registry, mappers, DTOs, row-locked subscription services.

**Main workflow.** The view verifies raw payload/signature. The service validates event shape, creates/gets a unique ledger, atomically claims pending/failed, finds a handler, and invokes it. Checkout establishes current state; subscription updated/deleted mutate only the matching current subscription, while invoice paid/failed also apply to a row that has no subscription ID yet. Success marks the event processed; unknown types are ignored; exceptions mark failed and propagate so Stripe receives a 500/retries.

**Failure paths.** Invalid payload/signature returns 400; non-POST returns 405. Missing local customer makes the handler fail. A worker crash while status is `processing` leaves an unrecoverable claim. Subscription updated/deleted arriving before Checkout are ignored and not replayed afterwards. Invoice paid/failed instead adopt the subscription, so the first billing period's email is not lost when the invoice event wins the race.

**Tests.** Handler mappers, individual handlers, stale-event behavior, locks, and lifecycle services are strong. The orchestration tests are entirely commented in the current untracked `apps/subscriptions/tests/services/test_webhook_handlers.py`; the HTTP webhook view is untested.

**Status: Mostly complete implementation; Partial resilience/verification.**

## Subscription emails

**Purpose and actors.** Account holders receive HTML/text payment success, payment failure, and final cancellation emails.

**Entry points/components.** `apps/subscriptions/emails.py`; invoice notification service/model/task; cancellation task; email templates.

**Main workflow.** Webhook invoice handlers update state and create/reuse a pending notification inside a transaction. After commit, Celery validates the user email, sends the matching template through Django email, records delivery state, and retries exceptions up to three times. Deletion enqueues a cancellation email directly.

**Failure paths.** Missing/invalid email, SMTP/backend errors, missing task user/notification, or template errors cause retries. Payment-failure tasks never pass `payment_update_url`; the template falls back to the local subscription page. Concurrent pending tasks can duplicate delivery. Cancellation mail has no delivery ledger/idempotency model.

**Tests.** Recipient validation, provider errors, templates/context, invoice queuing, handlers, and cancellation enqueueing are tested. Actual Celery retry/state execution is mostly untested.

**Status: Mostly complete.**

## Admin and operational endpoints

**Purpose and actors.** Staff manage domain records; infrastructure checks health; operators deploy/import data.

**Entry points/components.** `/[lang]/chatea-admin/`, model admins, `/health/`, Docker healthcheck, S3 commands, GitHub workflows.

**Rules/failures.** Admin uses Django permissions. `apps/users/admin.py::UserAdmin` subclasses plain `ModelAdmin`, not Django auth `UserAdmin`, so password display/save semantics are likely unsafe and require verification. Health always returns `{"status":"ok"}` and does not test MySQL, Redis, Celery, Stripe, or email.

**Tests.** No admin/import/health integration tests. CI checks migrations/deployment settings but currently runs tests/coverage only for `apps.chat`.

**Status: Partial.** Basic surfaces exist; health depth and operational verification are limited.
