from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.integrations.stripe.checkout import create_subscription_checkout_session
from apps.integrations.stripe.customers import create_customer
from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus

# Two Checkout Session requests for the same user inside this window collapse onto
# a single Stripe session. It absorbs double submits, multiple tabs and client
# retries, while still letting a user who abandoned Checkout start a new attempt.
CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS = 10 * 60


def build_customer_idempotency_key(user_id: int) -> str:
    """A user gets one Stripe customer, so the key never varies."""
    return f"chatea:customer:{user_id}"


def build_checkout_session_idempotency_key(user_id: int) -> str:
    window = int(
        timezone.now().timestamp() // CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS
    )

    return f"chatea:checkout-session:{user_id}:{window}"


@transaction.atomic
def _get_user_subscription_with_stripe_customer(user) -> UserSubscription:
    """
    Return the user's subscription, creating its Stripe customer if it has none.

    The row is locked for the whole transaction, so concurrent checkout requests
    are serialized instead of each creating a customer. The customer ID is
    committed before the caller talks to Stripe again, so a later failure cannot
    leave a Stripe customer that no local row points at.
    """
    UserSubscription.objects.get_or_create(user=user)
    user_subscription = UserSubscription.objects.select_for_update().get(user=user)

    if user_subscription.status == UserSubscriptionStatus.ACTIVE:
        raise ValueError("User already has an active subscription.")

    if not user_subscription.stripe_customer_id:
        customer = create_customer(
            user_id=user.id,
            email=user.email,
            idempotency_key=build_customer_idempotency_key(user.id),
        )

        user_subscription.stripe_customer_id = customer.id
        user_subscription.save(update_fields=["stripe_customer_id", "updated_at"])

    return user_subscription


def create_pro_checkout_session(user, request):
    user_subscription = _get_user_subscription_with_stripe_customer(user)

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
        idempotency_key=build_checkout_session_idempotency_key(user.id),
    )
