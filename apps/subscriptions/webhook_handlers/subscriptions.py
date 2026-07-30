from __future__ import annotations

from stripe import Subscription

from apps.subscriptions.services.user_subscription import (
    sync_user_subscription_from_stripe,
    mark_subscription_deleted,
)
from apps.subscriptions.tasks.subscription_notifications import (
    send_subscription_canceled_email_task,
)
from apps.subscriptions.webhook_handlers.mappers import (
    build_subscription_sync_dto,
    build_subscription_deleted_dto,
)


def handle_customer_subscription_updated(subscription: Subscription):
    subscription_sync = build_subscription_sync_dto(subscription)

    if not subscription_sync:
        return

    sync_user_subscription_from_stripe(subscription_sync)


def handle_customer_subscription_deleted(subscription: Subscription):
    deleted_subscription = build_subscription_deleted_dto(subscription)

    if not deleted_subscription:
        return

    user_subscription = mark_subscription_deleted(deleted_subscription)
    send_subscription_canceled_email_task.delay(
        user_id=user_subscription.user.id,
        ended_at=user_subscription.ended_at,
    )
