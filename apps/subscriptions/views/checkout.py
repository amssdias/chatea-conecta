import logging

import stripe
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.integrations.stripe.checkout_sessions import retrieve_checkout_session
from apps.subscriptions.services.create_pro_subscription import create_pro_checkout_session
from apps.subscriptions.services.user_subscription import get_user_subscription

logger = logging.getLogger(__name__)


@login_required
@require_POST
def create_pro_checkout_session_view(request):
    session = create_pro_checkout_session(
        user=request.user,
        request=request,
    )

    return redirect(session.url)


@login_required
def checkout_success_view(request):
    session_id = request.GET.get("session_id")
    session_info = None
    status = "missing_session"

    if session_id:
        try:
            session = retrieve_checkout_session(session_id)
        except stripe.StripeError:
            logger.exception(
                "Could not retrieve Stripe Checkout Session. user_id=%s",
                request.user.id,
            )
            status = "unavailable"
        else:
            user_subscription = get_user_subscription(request.user)
            expected_customer_id = (
                user_subscription.stripe_customer_id if user_subscription else None
            )
            session_user_id = getattr(session, "client_reference_id", None)
            session_customer_id = getattr(session, "customer", None)

            if not (
                str(session_user_id) == str(request.user.id)
                or (
                    expected_customer_id and session_customer_id == expected_customer_id
                )
            ):
                return HttpResponseForbidden("Invalid checkout session.")

            local_is_pro = bool(user_subscription and user_subscription.pro)
            status = "active" if local_is_pro else "pending"
            session_info = {
                "status": getattr(session, "status", None),
                "payment_status": getattr(session, "payment_status", None),
                "customer_email": getattr(session, "customer_details", None)
                and getattr(session.customer_details, "email", None),
                "amount_total": getattr(session, "amount_total", None),
                "currency": getattr(session, "currency", None),
                "subscription_id": getattr(session, "subscription", None),
            }

    return render(
        request,
        "subscriptions/checkout_success.html",
        {
            "status": status,
            "session_info": session_info,
        },
    )


@login_required
def checkout_cancel_view(request):
    return render(request, "subscriptions/checkout_cancel.html")
