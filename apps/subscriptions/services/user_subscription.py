import logging
from datetime import datetime

import stripe
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.integrations.stripe.subscriptions import (
    schedule_stripe_subscription_cancellation,
)
from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import (
    UserSubscriptionNotFoundError,
    SubscriptionMissingStripeIdError,
    SubscriptionAlreadyCancellingError,
    SubscriptionCannotBeCancelledError,
    SubscriptionCancellationProviderError,
)
from apps.subscriptions.webhook_handlers.dtos import (
    PaidSubscriptionDTO,
    FailedSubscriptionPaymentDTO,
    StripeSubscriptionSyncDTO,
    StripeSubscriptionDeletedDTO,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def get_user_subscription(user):
    return UserSubscription.objects.filter(user=user).first()


def get_user_subscription_by_customer_id(stripe_customer_id: str):
    try:
        return UserSubscription.objects.get(
            stripe_customer_id=stripe_customer_id,
        )
    except UserSubscription.DoesNotExist as exc:
        raise UserSubscriptionNotFoundError(
            "User subscription not found. " f"stripe_customer_id={stripe_customer_id}, "
        ) from exc


def save_stripe_subscription_id(stripe_customer_id, stripe_subscription_id):
    user_subscription = get_user_subscription_by_customer_id(stripe_customer_id)

    user_subscription.stripe_subscription_id = stripe_subscription_id
    user_subscription.save(update_fields=["stripe_subscription_id"])


def mark_subscription_paid(paid_subscription: PaidSubscriptionDTO) -> UserSubscription:
    user_subscription = get_user_subscription_by_customer_id(paid_subscription.stripe_customer_id)

    user_subscription.status = UserSubscriptionStatus.ACTIVE
    user_subscription.current_period_end = paid_subscription.current_period_end
    user_subscription.cancel_at_period_end = paid_subscription.cancel_at_period_end
    user_subscription.canceled_at = paid_subscription.canceled_at
    user_subscription.ended_at = paid_subscription.ended_at

    subscription_changed = (
            user_subscription.stripe_subscription_id
            != paid_subscription.stripe_subscription_id
    )

    if subscription_changed or not user_subscription.started_at:
        user_subscription.started_at = paid_subscription.started_at

    user_subscription.stripe_subscription_id = paid_subscription.stripe_subscription_id

    user_subscription.save(
        update_fields=[
            "stripe_subscription_id",
            "status",
            "started_at",
            "current_period_end",
            "cancel_at_period_end",
            "canceled_at",
            "ended_at",
            "updated_at",
        ],
    )

    return user_subscription


def mark_subscription_payment_failed(
        failed_payment: FailedSubscriptionPaymentDTO,
) -> UserSubscription:
    user_subscription = get_user_subscription_by_customer_id(
        failed_payment.stripe_customer_id
    )

    user_subscription.status = map_stripe_subscription_status(
        failed_payment.stripe_status,
        False,
    )
    user_subscription.save(update_fields=["status", "updated_at"])

    return user_subscription


def sync_user_subscription_from_stripe(
        subscription_sync: StripeSubscriptionSyncDTO,
) -> UserSubscription:
    user_subscription = get_user_subscription_by_customer_id(
        subscription_sync.stripe_customer_id
    )

    subscription_changed = (
            user_subscription.stripe_subscription_id
            != subscription_sync.stripe_subscription_id
    )

    if subscription_changed or not user_subscription.started_at:
        user_subscription.started_at = subscription_sync.started_at

    user_subscription.stripe_subscription_id = subscription_sync.stripe_subscription_id
    user_subscription.current_period_end = subscription_sync.current_period_end
    user_subscription.cancel_at_period_end = subscription_sync.cancel_at_period_end
    user_subscription.canceled_at = subscription_sync.canceled_at
    user_subscription.ended_at = subscription_sync.ended_at

    user_subscription.status = map_stripe_subscription_status(
        subscription_sync.stripe_status,
        subscription_sync.cancel_at_period_end,
    )

    user_subscription.save(
        update_fields=[
            "stripe_subscription_id",
            "status",
            "started_at",
            "current_period_end",
            "cancel_at_period_end",
            "canceled_at",
            "ended_at",
            "updated_at",
        ],
    )

    return user_subscription


def map_stripe_subscription_status(
        stripe_status: str, cancel_at_period_end: bool
) -> str:
    if stripe_status == "active":
        return UserSubscriptionStatus.ACTIVE

    if stripe_status == "trialing":
        return UserSubscriptionStatus.ACTIVE

    if stripe_status == "past_due":
        return UserSubscriptionStatus.PAST_DUE

    if stripe_status in {"canceled", "unpaid", "incomplete_expired"}:
        return UserSubscriptionStatus.CANCELED

    if stripe_status in {"incomplete", "paused"}:
        return UserSubscriptionStatus.INACTIVE

    return UserSubscriptionStatus.INACTIVE


def mark_subscription_deleted(
        deleted_subscription: StripeSubscriptionDeletedDTO,
) -> UserSubscription:
    user_subscription = get_user_subscription_by_customer_id(
        deleted_subscription.stripe_customer_id
    )

    user_subscription.status = UserSubscriptionStatus.CANCELED
    user_subscription.current_period_end = deleted_subscription.current_period_end
    user_subscription.cancel_at_period_end = deleted_subscription.cancel_at_period_end
    user_subscription.canceled_at = deleted_subscription.canceled_at
    user_subscription.ended_at = (
            deleted_subscription.ended_at
            or deleted_subscription.canceled_at
            or timezone.now()
    )

    user_subscription.save(
        update_fields=[
            "status",
            "current_period_end",
            "cancel_at_period_end",
            "canceled_at",
            "ended_at",
            "updated_at",
        ],
    )

    return user_subscription


def cancel_user_subscription(user):
    """
    Schedule the user's subscription for cancellation at the end of the billing period.

    This updates Stripe first, then updates the local subscription for immediate UI feedback.
    The webhook can later confirm/sync the final Stripe state.
    """
    user_subscription = get_user_subscription(user)

    if not user_subscription:
        raise UserSubscriptionNotFoundError

    if not user_subscription.stripe_subscription_id:
        raise SubscriptionMissingStripeIdError

    if user_subscription.cancel_at_period_end:
        raise SubscriptionAlreadyCancellingError

    if user_subscription.status not in [
        UserSubscriptionStatus.ACTIVE,
        UserSubscriptionStatus.PAST_DUE,
    ]:
        raise SubscriptionCannotBeCancelledError

    try:
        stripe_subscription = schedule_stripe_subscription_cancellation(
            user_subscription.stripe_subscription_id,
        )
    except stripe.StripeError as exc:
        logger.exception(
            "Stripe subscription cancellation failed. user_id=%s subscription_id=%s",
            user.id,
            user_subscription.stripe_subscription_id,
        )
        raise SubscriptionCancellationProviderError from exc

    user_subscription.cancel_at_period_end = True

    current_period_end = getattr(stripe_subscription, "current_period_end", None)

    if current_period_end:
        user_subscription.current_period_end = datetime.fromtimestamp(
            current_period_end,
            tz=timezone.get_current_timezone(),
        )

    user_subscription.save(
        update_fields=[
            "cancel_at_period_end",
            "current_period_end",
            "updated_at",
        ],
    )

    return user_subscription
