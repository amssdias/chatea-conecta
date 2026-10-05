from __future__ import annotations

from apps.integrations.stripe.client import get_stripe_client


def create_customer(
    *,
    user_id: int,
    email: str,
    idempotency_key: str,
):
    """
    Create a Stripe customer for a user.

    The idempotency key is required: a retried or duplicated request must return
    the customer created by the first one instead of creating another.
    """
    client = get_stripe_client()

    return client.v1.customers.create(
        {
            "email": email,
            "metadata": {
                "user_id": str(user_id),
            },
        },
        options={"idempotency_key": idempotency_key},
    )
