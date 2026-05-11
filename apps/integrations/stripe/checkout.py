from __future__ import annotations

from apps.integrations.stripe.client import get_stripe_client


def create_subscription_checkout_session(
    price_id: str,
    success_url: str,
    cancel_url: str,
    user_id: int,
    user_email: str,
    stripe_customer_id: str | None = None,
):
    client = get_stripe_client()

    checkout_data = {
        "mode": "subscription",
        "line_items": [
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(user_id),
        "metadata": {
            "user_id": str(user_id),
        },
    }

    if stripe_customer_id:
        checkout_data["customer"] = stripe_customer_id
    else:
        checkout_data["customer_email"] = user_email

    return client.v1.checkout.sessions.create(checkout_data)
