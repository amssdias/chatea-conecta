from __future__ import annotations

from django.conf import settings

from apps.integrations.stripe.client import get_stripe_client
from apps.integrations.stripe.utils import from_stripe_timestamp


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


def get_subscription_current_period_end(subscription):
    for item in subscription.items.data:
        if item.price.id == settings.STRIPE_PRO_MONTHLY_PRICE_ID:
            return from_stripe_timestamp(item.current_period_end)

    return None


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
