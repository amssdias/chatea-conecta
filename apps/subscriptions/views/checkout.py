from __future__ import annotations

import logging
from decimal import Decimal

import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.integrations.stripe.checkout_sessions import retrieve_checkout_session
from apps.subscriptions.services.create_pro_subscription import create_pro_checkout_session
from apps.subscriptions.services.exceptions import (
    CheckoutConfigurationError,
    CheckoutProviderError,
    SubscriptionAlreadyActiveError,
)
from apps.subscriptions.services.user_subscription import get_user_subscription

logger = logging.getLogger(__name__)

CHECKOUT_UNAVAILABLE_MESSAGE = _(
    "We could not start the PRO checkout right now. Please try again later."
)


@login_required
@require_POST
def create_pro_checkout_session_view(request):
    try:
        session = create_pro_checkout_session(
            user=request.user,
            request=request,
        )

    except SubscriptionAlreadyActiveError:
        messages.info(request, _("You already have an active PRO subscription."))
        return redirect("subscriptions:detail")

    except (CheckoutConfigurationError, CheckoutProviderError):
        messages.error(request, CHECKOUT_UNAVAILABLE_MESSAGE)
        return redirect("subscriptions:detail")

    return redirect(session.url)


def _session_was_paid(session) -> bool:
    """
    Whether Stripe considers this Checkout Session settled.

    A session the user opened and abandoned stays `open`, and one that timed out
    becomes `expired`; neither means money moved. `no_payment_required` covers
    fully discounted or trialing subscriptions, which do complete.
    """
    if getattr(session, "status", None) == "complete":
        return True

    return getattr(session, "payment_status", None) in {"paid", "no_payment_required"}


# Stripe reports amounts in the currency's smallest unit, except for currencies
# that have no minor unit at all.
# https://docs.stripe.com/currencies#zero-decimal
ZERO_DECIMAL_CURRENCIES = {
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga",
    "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf",
}


def _format_amount(amount_total, currency) -> str | None:
    """Turn a Stripe minor-unit amount into a human amount (999 -> '9.99')."""
    if amount_total is None:
        return None

    if (currency or "").lower() in ZERO_DECIMAL_CURRENCIES:
        return str(amount_total)

    return f"{Decimal(amount_total) / 100:.2f}"


def _resolve_checkout_status(session, user_subscription) -> str:
    # The webhook already confirmed and activated the subscription locally.
    if user_subscription and user_subscription.pro:
        return "active"

    # Paid at Stripe, but the webhook has not been processed yet.
    if _session_was_paid(session):
        return "pending"

    # Nothing was paid: an abandoned or expired session.
    return "not_paid"


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

            status = _resolve_checkout_status(session, user_subscription)
            session_info = {
                "status": getattr(session, "status", None),
                "payment_status": getattr(session, "payment_status", None),
                "customer_email": getattr(session, "customer_details", None)
                and getattr(session.customer_details, "email", None),
                "amount_total": _format_amount(
                    getattr(session, "amount_total", None),
                    getattr(session, "currency", None),
                ),
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
