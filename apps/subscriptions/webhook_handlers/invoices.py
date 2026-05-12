from apps.subscriptions.emails import (
    send_pro_payment_failed_email,
    send_pro_payment_success_email,
)
from apps.subscriptions.services.user_subscription import (
    mark_subscription_paid_from_invoice,
    mark_subscription_payment_failed_from_invoice,
)


def handle_invoice_paid(event_object):
    user_subscription = mark_subscription_paid_from_invoice(
        invoice=event_object,
    )

    if user_subscription:
        send_pro_payment_success_email(user=user_subscription.user)


def handle_invoice_payment_failed(event_object):
    user_subscription = mark_subscription_payment_failed_from_invoice(
        invoice=event_object,
    )

    if user_subscription:
        send_pro_payment_failed_email(user=user_subscription.user)
