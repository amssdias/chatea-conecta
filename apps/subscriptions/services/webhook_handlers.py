from __future__ import annotations

import logging

from django.utils import timezone
from stripe.v2.core import Event

from apps.subscriptions.models import StripeWebhookEvent
from apps.subscriptions.models.choices import StripeWebhookEventStatus
from apps.subscriptions.webhook_handlers.registry import STRIPE_EVENT_HANDLERS

logger = logging.getLogger(__name__)


def handle_stripe_webhook_event(event: Event) -> bool:
    """
    Process a verified Stripe webhook event idempotently.

    The Stripe event is stored using its event ID to avoid processing the same
    event more than once. Already processed or ignored events are skipped, while
    failed events may be retried when Stripe sends the webhook again.

    If a handler exists for the event type, the related Stripe object is passed
    to that handler and the event is marked as processed. Unknown event types are
    marked as ignored.

    Returns True when the event is processed successfully, and False when the
    event is skipped or ignored.
    """
    event_id = event.id
    event_type = event.type
    event_object = event.data.object

    if not event_id or not event_type or event_object is None:
        logger.warning("Stripe webhook event missing required data.")
        return False

    webhook_event, created = StripeWebhookEvent.objects.get_or_create(
        stripe_event_id=event_id,
        defaults={
            "event_type": event_type,
        },
    )

    if not created and webhook_event.status in [
        StripeWebhookEventStatus.PROCESSED,
        StripeWebhookEventStatus.IGNORED,
    ]:
        logger.info("Stripe webhook event already handled: %s", event_id)
        return False

    handler = STRIPE_EVENT_HANDLERS.get(event_type)
    if not handler:
        StripeWebhookEvent.objects.filter(stripe_event_id=event_id).update(
            status=StripeWebhookEventStatus.IGNORED,
            processed_at=timezone.now(),
        )
        logger.info("Unhandled Stripe event type ignored: %s", event_type)
        return False

    try:
        handler(event_object)
        StripeWebhookEvent.objects.filter(stripe_event_id=event_id).update(
            status=StripeWebhookEventStatus.PROCESSED,
            processed_at=timezone.now(),
        )
        logger.info("Processed Stripe webhook event: %s", event_id)
        return True
    except Exception as exc:
        StripeWebhookEvent.objects.filter(stripe_event_id=event_id).update(
            status=StripeWebhookEventStatus.FAILED,
            processed_at=timezone.now(),
            error_message=str(exc),
        )
        logger.exception("Stripe webhook handler error for event %s", event_id)
        raise
