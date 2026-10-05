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

    New and previously failed events are atomically claimed before their
    handlers run. Events already being processed or in a terminal state are
    skipped.

    Return True when a registered handler completes successfully. Return False
    when the event is invalid, already claimed, already handled, or ignored.
    """
    event_id = event.id
    event_type = event.type
    event_object = event.data.object

    if not event_id or not event_type or event_object is None:
        logger.warning("Stripe webhook event missing required data.")
        return False

    webhook_event, _ = StripeWebhookEvent.objects.get_or_create(
        stripe_event_id=event_id,
        defaults={
            "event_type": event_type,
        },
    )

    claimed = StripeWebhookEvent.objects.filter(
        pk=webhook_event.pk,
        status__in=[
            StripeWebhookEventStatus.PENDING,
            StripeWebhookEventStatus.FAILED,
        ],
    ).update(
        status=StripeWebhookEventStatus.PROCESSING,
        error_message=None,
        processed_at=None,
    )

    if not claimed:
        logger.info(
            "Stripe webhook event already claimed or handled: %s",
            event_id,
        )
        return False

    handler = STRIPE_EVENT_HANDLERS.get(event_type)
    if handler is None:
        StripeWebhookEvent.objects.filter(
            pk=webhook_event.pk,
            status=StripeWebhookEventStatus.PROCESSING,
        ).update(
            status=StripeWebhookEventStatus.IGNORED,
            processed_at=timezone.now(),
        )
        logger.info("Unhandled Stripe event type ignored: %s", event_type)
        return False

    try:
        handler(event_object)
    except Exception as exc:
        StripeWebhookEvent.objects.filter(
            pk=webhook_event.pk,
            status=StripeWebhookEventStatus.PROCESSING,
        ).update(
            status=StripeWebhookEventStatus.FAILED,
            processed_at=timezone.now(),
            error_message=str(exc),
        )
        logger.exception("Stripe webhook handler error for event %s", event_id)
        raise

    StripeWebhookEvent.objects.filter(
        pk=webhook_event.pk,
        status=StripeWebhookEventStatus.PROCESSING,
    ).update(
        status=StripeWebhookEventStatus.PROCESSED,
        processed_at=timezone.now(),
        error_message=None,
    )
    logger.info("Processed Stripe webhook event: %s", event_id)
    return True
