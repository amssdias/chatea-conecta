from __future__ import annotations

from django.db import transaction

from apps.subscriptions.models import StripeInvoiceNotification
from apps.subscriptions.models.choices import InvoiceNotificationStatus
from apps.subscriptions.tasks.invoice_notifications import send_invoice_notification_email_task


def queue_invoice_email_notification(
        stripe_invoice_id: str,
        email_type: str,
        user_id: int,
        invoice_url: str | None = None,
) -> bool:
    if not stripe_invoice_id:
        return False

    notification, created = StripeInvoiceNotification.objects.get_or_create(
        stripe_invoice_id=stripe_invoice_id,
        email_type=email_type,
        defaults={
            "status": InvoiceNotificationStatus.PENDING,
        },
    )

    if not created and notification.status not in [InvoiceNotificationStatus.PENDING, InvoiceNotificationStatus.FAILED]:
        return False

    transaction.on_commit(
        lambda: send_invoice_notification_email_task.delay(
            notification.id,
            user_id,
            invoice_url,
        )
    )

    return True
