from django.db import IntegrityError

from apps.subscriptions.models import StripeInvoiceNotification


def _can_send_invoice_email(invoice_id, email_type: str) -> bool:
    if not invoice_id:
        return True
    _, created = StripeInvoiceNotification.objects.get_or_create(
        stripe_invoice_id=invoice_id,
        email_type=email_type,
    )
    return created


def mark_invoice_email_as_sent(
        stripe_invoice_id: str,
        email_type: str,
) -> bool:
    try:
        StripeInvoiceNotification.objects.create(
            stripe_invoice_id=stripe_invoice_id,
            email_type=email_type,
        )
    except IntegrityError:
        return False

    return True
