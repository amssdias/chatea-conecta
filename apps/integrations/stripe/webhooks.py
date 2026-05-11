from __future__ import annotations

from django.conf import settings
from stripe import SignatureVerificationError
from stripe import Webhook

from apps.integrations.stripe.errors import StripeWebhookError


def construct_stripe_event(*, payload: bytes, sig_header: str | None):
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
