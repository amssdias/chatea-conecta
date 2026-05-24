from stripe import Invoice

from apps.subscriptions.emails import send_pro_payment_failed_email, send_pro_payment_success_email
from apps.subscriptions.models import StripeInvoiceNotification
from apps.subscriptions.services.invoice_notifications import mark_invoice_email_as_sent, _can_send_invoice_email
from apps.subscriptions.services.user_subscription import (
    mark_subscription_paid, mark_subscription_payment_failed,
)
from apps.subscriptions.webhook_handlers.mappers import build_paid_subscription_dto_from_invoice, \
    build_failed_subscription_payment_dto_from_invoice


def handle_invoice_paid(invoice: Invoice):
    paid_subscription = build_paid_subscription_dto_from_invoice(invoice)
    if not paid_subscription:
        return

    user_subscription = mark_subscription_paid(paid_subscription)

    if not user_subscription:
        return

    # TODO: Verify if should create email instance before sending
    if _can_send_invoice_email(
            paid_subscription.latest_invoice_id,
            StripeInvoiceNotification.EmailType.PAYMENT_SUCCEEDED,
    ):
        send_pro_payment_success_email(
            user=user_subscription.user,
            invoice_url=paid_subscription.invoice_url,
        )


def handle_invoice_payment_failed(invoice: Invoice):
    failed_payment = build_failed_subscription_payment_dto_from_invoice(invoice)
    if not failed_payment:
        return

    user_subscription = mark_subscription_payment_failed(failed_payment)

    if not user_subscription:
        return

    # TODO: Verify if should create email instance before sending
    if mark_invoice_email_as_sent(
            failed_payment.latest_invoice_id,
            StripeInvoiceNotification.EmailType.PAYMENT_FAILED,
    ):
        send_pro_payment_failed_email(
            user=user_subscription.user,
            invoice_url=failed_payment.invoice_url,
        )
