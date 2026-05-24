from __future__ import annotations

from django.conf import settings

from apps.integrations.stripe.client import get_stripe_client
from apps.integrations.stripe.utils import from_stripe_timestamp


def retrieve_subscription(stripe_subscription_id: str):
    stripe_client = get_stripe_client()

    return stripe_client.v1.subscriptions.retrieve(
        stripe_subscription_id,
    )


def get_subscription_current_period_end(subscription):
    for item in subscription.items.data:
        if item.price.id == settings.STRIPE_PRO_MONTHLY_PRICE_ID:
            return from_stripe_timestamp(item.current_period_end)

    return None
