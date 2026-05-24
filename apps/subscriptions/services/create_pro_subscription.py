from django.conf import settings
from django.urls import reverse

from apps.integrations.stripe.checkout import create_subscription_checkout_session
from apps.integrations.stripe.client import get_stripe_client
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.user_subscription import get_or_create_user_subscription_for_checkout


def create_pro_checkout_session(user, request):
    user_subscription = get_or_create_user_subscription_for_checkout(user)

    if user_subscription.status == UserSubscriptionStatus.ACTIVE:
        raise ValueError("User already has an active subscription.")

    if not user_subscription.stripe_customer_id:
        stripe_client = get_stripe_client()

        customer = stripe_client.v1.customers.create({
            "email": user.email,
            "metadata": {
                "user_id": str(user.id),
            },
        })

        user_subscription.stripe_customer_id = customer.id
        user_subscription.save(update_fields=["stripe_customer_id", "updated_at"])

    success_url = request.build_absolute_uri(
        reverse("subscriptions:checkout_success")
    ) + "?session_id={CHECKOUT_SESSION_ID}"

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
