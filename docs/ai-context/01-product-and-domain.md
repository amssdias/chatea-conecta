# Product and Domain

> Last analyzed commit: `225c22d13f051a73ffa16efe91fbf1eb0ba2829b` on branch `003-user-pro`  
> Analysis date: 2026-08-02

## Product purpose

Chatea Conecta provides immediate browser chat for adults who want to meet people without first creating an account. A visitor chooses a nickname, enters one shared room named `chatea`, sees transient messages, and can open direct chats from another participant’s public message. Account creation adds durable authentication and password recovery; a monthly Stripe-backed Pro entitlement removes the free limit on initiating private chats.

The repository supports these main journeys:

1. A guest accepts the age/terms checkboxes in the browser, submits a nickname, receives Redis-backed cookies, and enters live chat (`chat_connect/templates/index.html`, `apps/chat/views/chat.py`).
2. A user signs up or logs in, receives a Django session plus chat identity cookies, and enters chat (`apps/users/views/signup.py`, `apps/users/views/login.py`).
3. A connected participant exchanges public messages over `/ws/chat/`, then invites another online participant or bot into a private Channels group (`apps/chat/consumers.py`, `apps/chat/services/actions/`).
4. An account holder starts Stripe Checkout. Verified webhooks establish and update the local subscription; the redirect page only reports local `active` or `pending` state (`apps/subscriptions/services/create_pro_subscription.py`, `apps/subscriptions/views/checkout.py`, `apps/subscriptions/webhook_handlers/`).
5. A subscriber reviews status, opens Stripe Billing Portal when payment configuration is needed, or schedules cancellation at period end (`apps/subscriptions/views/detail.py`, `apps/subscriptions/views/billing_portal.py`, `apps/subscriptions/views/cancel.py`).
6. Celery Beat periodically chooses a non-promotional database message and a database user identity, then broadcasts it when anyone is online (`apps/chat/tasks/send_random_chat_messages.py`).

## Domain terminology

| Term | Meaning | Relevant component | Important distinction |
|---|---|---|---|
| Chat identity | The `username`/`user_id` used by the WebSocket consumer | `ChatView`, `ChatConsumer`, Redis mapping keys | For authenticated sockets it comes from the Django session; for guests it comes from client-controlled cookies. It is not a database entity for guests. |
| Active username | Lowercased member of the Redis set `chatconnect:users:usernames` | `apps/chat/services/activity.py` | Used for nickname availability and displayed count; it is not equivalent to a valid heartbeat marker. Bot usernames are also inserted. |
| Online marker | `chatconnect:user:online:{user_id}` string with a 90-second TTL | `mark_user_online`, heartbeat action | Intended to show an active WebSocket. It is separate from the active-username set. |
| Public group | Channels group registered through `register_group`; the browser uses `chatea` | `handle_register_group` | Any non-empty, non-`private-` string is accepted; there is no database room model. |
| Private chat | Predictable Channels group plus per-user Redis hash entry | `get_private_group_name`, `USER_PRIVATE_CHATS_KEY` | The relationship/message content is not persisted in MySQL. Group names preserve inviter/target order and therefore are not canonical by pair. |
| Restored private chat | Private group recovered from a user’s Redis hash after reconnect | `restore_user_private_chat_groups` | Hash TTL is 30 minutes and refreshes on restore. No history is restored. |
| Free private-chat limit | Maximum number of entries an initiating non-Pro consumer may already have | `FREE_PRIVATE_CHAT_LIMIT = 3` | It counts stored/open consumer relationships, not messages. There is no server-side leave action to free a slot during the connection. Incoming invites can add further entries. |
| Pro | Local access predicate derived from `UserSubscription.status` and period end | `UserSubscription.pro`, `User.is_pro` | Not inferred from a Stripe redirect, browser flag, or Stripe response at request time. `past_due` may retain Pro until `current_period_end`. A missing `current_period_end` never grants Pro. |
| Current subscription | Stripe subscription ID currently stored on the one-to-one local subscription | `UserSubscription.stripe_subscription_id` | Invoice paid/failed set it when it is empty; only checkout completion may replace an existing one. Later events for other IDs are ignored. |
| Webhook claim | `StripeWebhookEvent` row moved from `pending`/`failed` to `processing` | `handle_stripe_webhook_event` | Prevents simultaneous processing of the same Stripe event ID. A stuck `processing` row has no timeout recovery. |
| Invoice notification | Delivery record unique by Stripe invoice ID and email type | `StripeInvoiceNotification` | Tracks payment-success/payment-failure email state; cancellation email has no equivalent record. |
| Topic | Named category of automated conversation text | `apps/chat/models/topic.py::Topic` | It is not a user-selectable chat room. |
| Conversation flow | One candidate bot message associated with a topic | `ConversationFlow` | `is_promotional=True` messages are excluded from the active loader; no user conversation history is represented. |
| Bot | Any non-staff, non-superuser database user loaded as an automated sender | `BotCacheLoader._load_bot_users` | There is no bot flag; normal and inactive customer accounts also qualify under current code. |

## Actors and permissions

| Actor | Can | Cannot / no special support |
|---|---|---|
| Anonymous visitor | View public pages; submit a guest nickname; use public chat; initiate up to three private chats; receive private invites | Buy/manage Pro without creating/logging into an account; recover a guest identity after Redis/cookies expire; access Django admin |
| Authenticated free user | All chat actions; durable login/password flows; start Checkout; view subscription detail | Initiate a fourth private chat while the consumer mapping has three; receive Pro based only on browser or Checkout redirect |
| Pro user | Initiate more than three private chats while `UserSubscription.pro` is true; manage billing/cancellation | Access a separate premium room or stored history—neither exists |
| Past-due user | Retains Pro only when `current_period_end` exists and is in the future; can open the billing portal from the UI | Retain Pro after the period end under the model predicate |
| Staff | Authenticate to Django admin when model permissions allow; otherwise chat like an ordinary account | No coded moderation/reporting/blocking powers in chat; staff are excluded from bot selection |
| Superuser | Full Django admin permissions | No special real-time moderation protocol; excluded from bot selection |
| Administrator | **Inferred:** a staff/superuser operating `/chatea-admin/`; can manage registered models | There is no separate administrator domain model |
| Bot identity | Appear online in the username set; supply automated public messages; be invited while no heartbeat exists | A bot has no running consumer and receives no private invite notification; promotional messages are not currently selected |

There are no organizations, tenants, business accounts, moderators, block lists, report queues, or object-level ownership permission classes.

## Business rules

### Identity and account rules

- Guest nicknames must match `^[A-Za-z0-9_-]{3,20}$`, must not be in the active Redis username set, and must not match a database username case-insensitively (`apps/chat/views/chat.py::USERNAME_REGEX`, `ChatView._validate_guest_username`).
- Registered usernames use Django `AbstractUser` validation and database uniqueness. Signup requires and normalizes an email; `SignUpForm.clean_email` rejects a case-insensitive match, but the database field itself is not unique (`apps/users/forms/signup.py`).
- Signup creates the user, profile, and inactive `UserSubscription` atomically (`apps/users/services/create_user.py::create_user_account_from_signup_form`). The manager method used by the S3 import creates user then profile without an encompassing transaction.
- Guest cookies are HTTP-only, `SameSite=Lax`, and secure according to `settings.COOKIES_SECURE`. Login cookies omit an explicit SameSite value and therefore use Django’s default (`apps/chat/views/chat.py`, `apps/users/views/login.py`).
- The home template requires age 18 and terms checkboxes in the guest form, but no server-side view, model, or account flow records or validates consent (`chat_connect/templates/index.html`, `apps/chat/views/chat.py`).

### Chat rules

- A socket must have a non-empty ID and username. Authenticated session identity overrides cookies; anonymous identity is read from cookies (`ChatConsumer.connect`).
- Client messages dispatch only when `type` is in `ACTION_MAP`: `heartbeat`, `register_group`, `private_invite`, or `send_message` (`apps/chat/websocket/dispatch.py`).
- A `private-` group cannot be joined via `register_group`; sending to a private group requires membership in `consumer.groups` (`handle_register_group`, `handle_send_message`).
- Public group registration accepts any normalized non-empty string. Sending to a public group does not require prior group membership.
- A private invite to self, a missing target, or an already-open target is ignored. Offline non-bot targets produce an offline event; bots may be invited without being online (`handle_private_invite`).
- Non-Pro initiators are denied when `len(consumer.private_chats) >= 3`; authenticated database state is authoritative for Pro (`user_has_pro_access`).
- Private chat hashes expire after 30 minutes; presence markers expire after 90 seconds; the browser sends heartbeats every 30 seconds (`apps/chat/constants/cache_expiration.py`, `apps/chat/static/js/chatSocket.js`).
- Chat messages have no server-side length, content, or rate validation. The 300-character database limit applies only to `ConversationFlow`, not user messages.

### Subscription and payment rules

- `UserSubscription` is one-to-one with a user. Stripe customer IDs are unique; Stripe subscription IDs are not (`apps/subscriptions/models/user_subscription.py`).
- `active` and `past_due` both grant Pro only before a future, non-null `current_period_end`. A null period end grants nothing. Other statuses do not grant Pro (`UserSubscription.pro`).
- Stripe statuses map as follows: `active`/`trialing` → `active`; `past_due` → `past_due`; `canceled`/`unpaid`/`incomplete_expired` → `canceled`; `incomplete`/`paused`/unknown → `inactive` (`map_stripe_subscription_status`). The local `expired` choice is never emitted by this mapper.
- Checkout is rejected only for a locally `active` subscription. Missing local subscription/customer records are created; the existing Stripe customer is reused (`create_pro_checkout_session`). Customer creation uses a stable Stripe idempotency key, and Checkout Session creation a per-user windowed key, both under a `select_for_update` lock on the subscription row.
- Only `checkout.session.completed` establishes/replaces the current Stripe subscription ID. Paid, failed, updated, and deleted events affect the record only when their subscription ID matches (`apps/subscriptions/services/user_subscription.py`).
- State-changing webhook services use `transaction.atomic` and `select_for_update`. Email enqueueing for invoice events uses `transaction.on_commit`.
- Cancellation is allowed for `active` and `past_due`, calls Stripe first, then sets `cancel_at_period_end` locally. It does not immediately remove Pro (`cancel_user_subscription`).
- Webhook signatures are verified with `STRIPE_WEBHOOK_SECRET`; unsupported event types are recorded as `ignored` (`apps/integrations/stripe/webhooks.py`, `apps/subscriptions/services/webhook_handlers.py`).
- Webhook event IDs are unique. `pending` and `failed` may be claimed; `processing`, `processed`, and `ignored` are skipped.
- Invoice email delivery is unique by invoice ID and email type. Tasks retry exceptions with exponential backoff and at most three retries (`apps/subscriptions/tasks/invoice_notifications.py`).

### Bot rules

- Bot ticks run every 3 seconds in base/production settings and every 60 seconds in development, target the `chatea` group, stop when no online marker exists, and send with probability `0.9` (`chat_connect/settings/base.py`, `chat_connect/settings/settings_development.py`, `apps/chat/tasks/send_random_chat_messages.py`).
- Bot data caches for one week; a selected message is suppressed for one hour. Selection attempts at most ten topics (`BOT_MESSAGE_CACHE_TTL`, `BOT_MESSAGE_SENT_TTL`, `BotMessageService.MAX_TOPIC_ATTEMPTS`).
- Promotional conversation flows are excluded. `SEND_PROMOTIONAL_MESSAGES` and promotional Redis constants do not currently drive a workflow.

## Important invariants

- Each registered user has at most one profile and one local subscription due to one-to-one database constraints. The signup service creates both; other user-creation paths may omit the subscription.
- `Topic.name` is unique; `(ConversationFlow.topic, ConversationFlow.message)` is unique.
- A Stripe customer ID identifies at most one local subscription. All provider-driven updates locate ownership through that ID.
- The current Stripe subscription ID may be replaced only by checkout synchronization; lifecycle events must not replace it.
- A verified webhook must be claimed before its handler runs; a processed/ignored event ID must not run again.
- A payment/cancellation redirect must not directly grant Pro.
- A private group must not be joinable through the ordinary registration action, and private sends must come from a current group member.
- Temporary chat state is not durable business data. Losing the Channels Redis database loses presence, bot cache, guest mappings, and private-chat restoration, but not users/subscriptions.

## Product boundaries

Confirmed unsupported or absent behavior:

- No persisted user messages, searchable history, delivery receipts, edits, deletion, attachments, reactions, or offline delivery.
- No moderation, reporting, blocking, muting, bans, abuse review, or enforcement of the behavioral text in the public terms pages.
- No server-enforced age/terms consent, despite required guest-form checkboxes and adult positioning.
- No room catalogue, membership model, or user-created persistent rooms; only browser-created Channels group names.
- No REST/GraphQL API, mobile client, token authentication, social login, or third-party identity provider.
- No organization/tenant/business isolation or multi-account billing.
- No subscription reactivation workflow before period end, coupon/trial UI, plan catalogue, refunds, or local invoice history.
- No dedicated bot account type or UI/admin switch controlling bot participation.
- No media upload/storage workflow; S3 is used only by import commands.
- **Contradiction:** public privacy/terms copy says no tracking or personal-data collection, while the application embeds Google Analytics and implements accounts, email, Stripe customer data, Sentry, and CloudWatch (`chat_connect/templates/base.html`, `chat_connect/templates/pages/privacy.html`, `apps/subscriptions/`). Treat the legal copy as stale, not as an implementation guarantee.
