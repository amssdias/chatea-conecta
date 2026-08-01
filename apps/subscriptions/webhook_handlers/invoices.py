from django.db import transaction
from stripe import Invoice

from apps.subscriptions.models.choices import EmailType
from apps.subscriptions.services.invoice_notifications import queue_invoice_email_notification
from apps.subscriptions.services.user_subscription import (
    mark_subscription_paid, mark_subscription_payment_failed,
)
from apps.subscriptions.webhook_handlers.mappers import build_paid_subscription_dto_from_invoice, \
    build_failed_subscription_payment_dto_from_invoice


def handle_invoice_paid(invoice: Invoice):
    paid_subscription = build_paid_subscription_dto_from_invoice(invoice)

    with transaction.atomic():
        user_subscription = mark_subscription_paid(paid_subscription)

        if user_subscription is None:
            return

        queue_invoice_email_notification(
            stripe_invoice_id=paid_subscription.latest_invoice_id,
            email_type=EmailType.PAYMENT_SUCCEEDED,
            user_id=user_subscription.user_id,
            invoice_url=paid_subscription.invoice_url,
        )


def handle_invoice_payment_failed(invoice: Invoice):
    failed_payment = build_failed_subscription_payment_dto_from_invoice(invoice)

    with transaction.atomic():
        user_subscription = mark_subscription_payment_failed(failed_payment)

        if user_subscription is None:
            return

        queue_invoice_email_notification(
            stripe_invoice_id=failed_payment.latest_invoice_id,
            email_type=EmailType.PAYMENT_FAILED,
            user_id=user_subscription.user_id,
            invoice_url=failed_payment.invoice_url,
        )
