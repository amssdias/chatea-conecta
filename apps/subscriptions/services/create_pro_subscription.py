from django.conf import settings
from django.urls import reverse

from apps.integrations.stripe.checkout import create_subscription_checkout_session
from apps.subscriptions.services.user_subscription import get_or_create_user_subscription


def create_pro_checkout_session(user, request):
    user_subscription = get_or_create_user_subscription(user)

    success_url = request.build_absolute_uri(
        reverse("subscriptions:checkout_success")
    )
    cancel_url = request.build_absolute_uri(
        reverse("subscriptions:checkout_cancel")
    )

    return create_subscription_checkout_session(
        price_id=settings.STRIPE_PRO_MONTHLY_PRICE_ID,
        success_url=success_url,
        cancel_url=cancel_url,
        user_id=user.id,
        user_email=user.email,
        stripe_customer_id=user_subscription.stripe_customer_id,
    )