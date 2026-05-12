from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.subscriptions.models import UserSubscription

User = get_user_model()


def get_or_create_user_subscription(user):
    user_subscription, _ = UserSubscription.objects.get_or_create(user=user)
    return user_subscription


def activate_subscription_from_checkout_session(session):
    user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")

    if not user_id:
        return None

    user = User.objects.filter(id=user_id).first()

    if not user:
        return None

    user_subscription = get_or_create_user_subscription(user)

    user_subscription.status = UserSubscription.Status.ACTIVE
    user_subscription.stripe_customer_id = session.get("customer")
    user_subscription.stripe_subscription_id = session.get("subscription")

    if not user_subscription.started_at:
        user_subscription.started_at = timezone.now()

    user_subscription.save(update_fields=[
        "status",
        "stripe_customer_id",
        "stripe_subscription_id",
        "started_at",
        "updated_at",
    ])

    return user_subscription


def mark_subscription_paid_from_invoice(invoice):
    stripe_customer_id = invoice.get("customer")
    stripe_subscription_id = invoice.get("subscription")

    if not stripe_customer_id:
        return None

    user_subscription = UserSubscription.objects.filter(
        stripe_customer_id=stripe_customer_id,
    ).select_related("user").first()

    if not user_subscription:
        return None

    user_subscription.status = UserSubscription.Status.ACTIVE

    if stripe_subscription_id:
        user_subscription.stripe_subscription_id = stripe_subscription_id

    user_subscription.save(update_fields=[
        "status",
        "stripe_subscription_id",
        "updated_at",
    ])

    return user_subscription


def mark_subscription_payment_failed_from_invoice(invoice):
    stripe_customer_id = invoice.get("customer")

    if not stripe_customer_id:
        return None

    user_subscription = UserSubscription.objects.filter(
        stripe_customer_id=stripe_customer_id,
    ).select_related("user").first()

    if not user_subscription:
        return None

    user_subscription.status = UserSubscription.Status.PAST_DUE
    user_subscription.save(update_fields=["status", "updated_at"])

    return user_subscription


def cancel_subscription_from_stripe_subscription(stripe_subscription):
    stripe_customer_id = stripe_subscription.get("customer")

    if not stripe_customer_id:
        return None

    user_subscription = UserSubscription.objects.filter(
        stripe_customer_id=stripe_customer_id,
    ).select_related("user").first()

    if not user_subscription:
        return None

    user_subscription.status = UserSubscription.Status.CANCELED
    user_subscription.canceled_at = timezone.now()
    user_subscription.ended_at = timezone.now()

    user_subscription.save(update_fields=[
        "status",
        "canceled_at",
        "ended_at",
        "updated_at",
    ])

    return user_subscription
