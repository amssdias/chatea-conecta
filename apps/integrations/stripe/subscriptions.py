from __future__ import annotations

import logging

from django.conf import settings

from apps.integrations.stripe.client import get_stripe_client
from apps.integrations.stripe.utils import from_stripe_timestamp

logger = logging.getLogger(__name__)


def retrieve_subscription(stripe_subscription_id: str):
    """
    Retrieve a Stripe Subscription object by its Stripe subscription ID.

    Stripe API reference:
    https://docs.stripe.com/api/subscriptions/object?api-version=2026-02-25.clover
    """
    stripe_client = get_stripe_client()

    return stripe_client.v1.subscriptions.retrieve(
        stripe_subscription_id,
    )


def _get_subscription_period_boundary(subscription, field_name):
    """
    Read a billing period boundary from the subscription items.

    The Pro item is preferred, but a subscription whose items do not carry the
    configured Pro price still has a real billing period: a new or legacy Price, a
    misconfigured environment, or an unexpected product would otherwise resolve to
    ``None`` and be read downstream as "no expiry". Falling back to the earliest
    boundary keeps the entitlement bounded by real Stripe data.
    """
    items = list(subscription.items.data)

    if not items:
        return None

    pro_price_id = settings.STRIPE_PRO_MONTHLY_PRICE_ID

    if pro_price_id:
        for item in items:
            if item.price.id == pro_price_id:
                return from_stripe_timestamp(getattr(item, field_name))

    logger.warning(
        "No subscription item matches the configured Pro price; "
        "falling back to the earliest %s across items. "
        "stripe_subscription_id=%s configured_price_id=%s item_price_ids=%s",
        field_name,
        getattr(subscription, "id", None),
        settings.STRIPE_PRO_MONTHLY_PRICE_ID,
        [item.price.id for item in items],
    )

    boundaries = [
        boundary
        for boundary in (
            from_stripe_timestamp(getattr(item, field_name, None)) for item in items
        )
        if boundary
    ]

    if not boundaries:
        return None

    return min(boundaries)


def get_subscription_current_period_end(subscription):
    return _get_subscription_period_boundary(subscription, "current_period_end")


def schedule_stripe_subscription_cancellation(stripe_subscription_id: str):
    """
    Schedule a Stripe subscription to cancel at the end of the current billing period.
    """
    stripe_client = get_stripe_client()

    return stripe_client.v1.subscriptions.update(
        stripe_subscription_id,
        {
            "cancel_at_period_end": True,
        },
    )


def get_subscription_current_period_start(subscription):
    return _get_subscription_period_boundary(subscription, "current_period_start")
