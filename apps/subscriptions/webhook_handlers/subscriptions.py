
from apps.subscriptions.services.user_subscription import (
    cancel_subscription_from_stripe_subscription,
)


def handle_customer_subscription_deleted(event_object):
    cancel_subscription_from_stripe_subscription(
        stripe_subscription=event_object,
    )
