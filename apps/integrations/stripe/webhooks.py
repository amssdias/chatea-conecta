from __future__ import annotations

from django.conf import settings
from stripe import SignatureVerificationError
from stripe import Webhook

from apps.integrations.stripe.errors import StripeWebhookError


def construct_stripe_event(payload: bytes, sig_header: str | None):
    """
    Build and verify a Stripe webhook event from the raw request payload.

    This validates that the payload is a valid Stripe event and verifies the
    Stripe signature using the configured webhook secret. If the payload or
    signature is invalid, a StripeWebhookError is raised.

    Returns the verified Stripe event object, which can then be used to inspect
    the event type and process the webhook.
    """
    try:
        return Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as exc:
        raise StripeWebhookError("Invalid Stripe webhook payload.") from exc
    except SignatureVerificationError as exc:
        raise StripeWebhookError("Invalid Stripe webhook signature.") from exc
