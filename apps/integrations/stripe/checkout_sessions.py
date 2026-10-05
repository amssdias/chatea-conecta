from __future__ import annotations

from apps.integrations.stripe.client import get_stripe_client


def retrieve_checkout_session(session_id: str, expand: list[str] | None = None):
    client = get_stripe_client()
    params = {"expand": expand} if expand else {}
    return client.v1.checkout.sessions.retrieve(session_id, params)
