from __future__ import annotations

from stripe import Subscription

from apps.subscriptions.services.user_subscription import (
    sync_user_subscription_from_stripe,
    mark_subscription_deleted,
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

    mark_subscription_deleted(deleted_subscription)
