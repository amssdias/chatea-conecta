import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.integrations.stripe.webhooks import StripeWebhookError, construct_stripe_event
from apps.subscriptions.services.webhook_handlers import handle_stripe_webhook_event

logger = logging.getLogger(__name__)

@csrf_exempt
def stripe_webhook_view(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = construct_stripe_event(payload=request.body, sig_header=sig_header)
    except StripeWebhookError:
        return HttpResponse(status=400)

    logger.info("Stripe webhook received: %s", event.type)
    handle_stripe_webhook_event(event)
    return HttpResponse(status=200)
