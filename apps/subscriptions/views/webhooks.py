from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.integrations.stripe.webhooks import (
    StripeWebhookError,
    construct_stripe_event,
)
from apps.subscriptions.webhook_handlers.registry import STRIPE_EVENT_HANDLERS


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = construct_stripe_event(
            payload=request.body,
            sig_header=sig_header,
        )
    except StripeWebhookError:
        return HttpResponse(status=400)

    event_type = event["type"]
    event_object = event["data"]["object"]

    handler = STRIPE_EVENT_HANDLERS.get(event_type)

    if handler:
        handler(event_object)

    return HttpResponse(status=200)