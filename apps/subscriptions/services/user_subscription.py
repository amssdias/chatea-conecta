import logging
from typing import Optional

import stripe
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.integrations.stripe.subscriptions import (
    get_subscription_current_period_end,
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


def _get_user_subscription_for_update(stripe_customer_id: str) -> UserSubscription:
    try:
        return UserSubscription.objects.select_for_update().get(
            stripe_customer_id=stripe_customer_id,
        )
    except UserSubscription.DoesNotExist as exc:
        raise UserSubscriptionNotFoundError(
            "User subscription not found. " f"stripe_customer_id={stripe_customer_id}, "
        ) from exc


def _resolve_current_period_end(user_subscription: UserSubscription, current_period_end):
    """
    Keep the stored period end when Stripe state could not supply one.

    Overwriting a real period end with ``None`` would widen the entitlement instead of
    narrowing it, so an unreadable period leaves the existing boundary in place.
    """
    if current_period_end:
        return current_period_end

    if user_subscription.current_period_end:
        logger.warning(
            "Stripe event carried no current_period_end; keeping the stored value. "
            "customer_id=%s subscription_id=%s stored_current_period_end=%s",
            user_subscription.stripe_customer_id,
            user_subscription.stripe_subscription_id,
            user_subscription.current_period_end,
        )

    return user_subscription.current_period_end


def _log_ignored_non_current_subscription_event(
    user_subscription: UserSubscription,
    stripe_customer_id: str,
    stripe_subscription_id: str,
) -> None:
    logger.info(
        "Ignoring Stripe event for non-current subscription. "
        "customer_id=%s current_subscription_id=%s event_subscription_id=%s",
        stripe_customer_id,
        user_subscription.stripe_subscription_id,
        stripe_subscription_id,
    )


@transaction.atomic
def sync_user_subscription_from_checkout(
    subscription_sync: StripeSubscriptionSyncDTO,
) -> UserSubscription:
    """
    Establish the subscription coming from Checkout as the current one.

    This is the only place allowed to replace ``stripe_subscription_id``. It writes a
    complete snapshot of the Stripe state so that lifecycle events which arrived
    before Checkout could safely be ignored.
    """
    user_subscription = _get_user_subscription_for_update(
        subscription_sync.stripe_customer_id,
    )

    user_subscription.stripe_subscription_id = subscription_sync.stripe_subscription_id
    user_subscription.status = map_stripe_subscription_status(
        subscription_sync.stripe_status,
        subscription_sync.cancel_at_period_end,
    )
    user_subscription.started_at = subscription_sync.started_at
    user_subscription.current_period_start = subscription_sync.current_period_start
    user_subscription.current_period_end = subscription_sync.current_period_end
    user_subscription.cancel_at_period_end = subscription_sync.cancel_at_period_end
    user_subscription.canceled_at = subscription_sync.canceled_at
    user_subscription.ended_at = subscription_sync.ended_at

    if (
        user_subscription.status == UserSubscriptionStatus.ACTIVE
        and not user_subscription.current_period_end
    ):
        # A snapshot is written verbatim here, so the previous subscription's period end
        # is not carried over. Without a period end the customer has just paid and holds
        # no entitlement, which needs to surface rather than fail quietly.
        logger.error(
            "Checkout produced an active subscription with no current_period_end. "
            "customer_id=%s subscription_id=%s",
            subscription_sync.stripe_customer_id,
            subscription_sync.stripe_subscription_id,
        )

    user_subscription.save(
        update_fields=[
            "stripe_subscription_id",
            "status",
            "started_at",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "canceled_at",
            "ended_at",
            "updated_at",
        ],
    )

    return user_subscription


@transaction.atomic
def mark_subscription_paid(
    paid_subscription: PaidSubscriptionDTO,
) -> Optional[UserSubscription]:
    user_subscription = _get_user_subscription_for_update(
        paid_subscription.stripe_customer_id
    )

    if (
        user_subscription.stripe_subscription_id
        != paid_subscription.stripe_subscription_id
    ):
        _log_ignored_non_current_subscription_event(
            user_subscription,
            paid_subscription.stripe_customer_id,
            paid_subscription.stripe_subscription_id,
        )
        return None

    user_subscription.status = map_stripe_subscription_status(
        paid_subscription.stripe_status,
        paid_subscription.cancel_at_period_end,
    )
    user_subscription.current_period_start = paid_subscription.current_period_start
    user_subscription.current_period_end = _resolve_current_period_end(
        user_subscription,
        paid_subscription.current_period_end,
    )
    user_subscription.cancel_at_period_end = paid_subscription.cancel_at_period_end
    user_subscription.canceled_at = paid_subscription.canceled_at
    user_subscription.ended_at = paid_subscription.ended_at

    if not user_subscription.started_at:
        user_subscription.started_at = paid_subscription.started_at

    user_subscription.save(
        update_fields=[
            "status",
            "started_at",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "canceled_at",
            "ended_at",
            "updated_at",
        ],
    )

    return user_subscription


@transaction.atomic
def mark_subscription_payment_failed(
    failed_payment: FailedSubscriptionPaymentDTO,
) -> Optional[UserSubscription]:
    user_subscription = _get_user_subscription_for_update(
        failed_payment.stripe_customer_id
    )

    if (
        user_subscription.stripe_subscription_id
        != failed_payment.stripe_subscription_id
    ):
        _log_ignored_non_current_subscription_event(
            user_subscription,
            failed_payment.stripe_customer_id,
            failed_payment.stripe_subscription_id,
        )
        return None

    user_subscription.status = map_stripe_subscription_status(
        failed_payment.stripe_status,
        False,
    )
    user_subscription.save(update_fields=["status", "updated_at"])

    return user_subscription


@transaction.atomic
def sync_user_subscription_from_stripe(
    subscription_sync: StripeSubscriptionSyncDTO,
) -> Optional[UserSubscription]:
    user_subscription = _get_user_subscription_for_update(
        subscription_sync.stripe_customer_id
    )

    if (
        user_subscription.stripe_subscription_id
        != subscription_sync.stripe_subscription_id
    ):
        _log_ignored_non_current_subscription_event(
            user_subscription,
            subscription_sync.stripe_customer_id,
            subscription_sync.stripe_subscription_id,
        )
        return None

    if not user_subscription.started_at:
        user_subscription.started_at = subscription_sync.started_at

    user_subscription.current_period_start = subscription_sync.current_period_start
    user_subscription.current_period_end = _resolve_current_period_end(
        user_subscription,
        subscription_sync.current_period_end,
    )
    user_subscription.cancel_at_period_end = subscription_sync.cancel_at_period_end
    user_subscription.canceled_at = subscription_sync.canceled_at
    user_subscription.ended_at = subscription_sync.ended_at

    user_subscription.status = map_stripe_subscription_status(
        subscription_sync.stripe_status,
        subscription_sync.cancel_at_period_end,
    )

    user_subscription.save(
        update_fields=[
            "status",
            "started_at",
            "current_period_start",
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


@transaction.atomic
def mark_subscription_deleted(
    deleted_subscription: StripeSubscriptionDeletedDTO,
) -> Optional[UserSubscription]:
    user_subscription = _get_user_subscription_for_update(
        deleted_subscription.stripe_customer_id
    )

    if (
        user_subscription.stripe_subscription_id
        != deleted_subscription.stripe_subscription_id
    ):
        _log_ignored_non_current_subscription_event(
            user_subscription,
            deleted_subscription.stripe_customer_id,
            deleted_subscription.stripe_subscription_id,
        )
        return None

    user_subscription.status = UserSubscriptionStatus.CANCELED
    user_subscription.current_period_start = deleted_subscription.current_period_start
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
            "current_period_start",
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

    current_period_end = get_subscription_current_period_end(stripe_subscription)

    if current_period_end:
        user_subscription.current_period_end = current_period_end

    user_subscription.save(
        update_fields=[
            "cancel_at_period_end",
            "current_period_end",
            "updated_at",
        ],
    )

    return user_subscription
