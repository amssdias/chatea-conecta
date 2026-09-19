import logging

import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.integrations.stripe.billing_portal import create_billing_portal_session
from apps.subscriptions.services.user_subscription import get_user_subscription

logger = logging.getLogger(__name__)


@login_required
@require_POST
def create_billing_portal_session_view(request):
    """Redirect an authenticated customer to Stripe's billing portal."""
    user_subscription = get_user_subscription(request.user)

    if not user_subscription or not user_subscription.stripe_customer_id:
        messages.error(request, _("Your Stripe customer account could not be found."))
        return redirect("subscriptions:detail")

    return_url = request.build_absolute_uri(reverse("subscriptions:detail"))

    try:
        session = create_billing_portal_session(
            stripe_customer_id=user_subscription.stripe_customer_id,
            return_url=return_url,
        )
    except stripe.StripeError:
        logger.exception(
            "Could not create Stripe billing portal session. user_id=%s",
            request.user.id,
        )
        messages.error(
            request,
            _(
                "We could not open billing management right now. Please try again later."
            ),
        )
        return redirect("subscriptions:detail")

    return redirect(session.url)
