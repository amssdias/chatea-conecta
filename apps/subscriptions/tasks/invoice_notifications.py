from __future__ import annotations

import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.subscriptions.emails import (
    send_pro_payment_failed_email,
    send_pro_payment_success_email,
)
from apps.subscriptions.models import StripeInvoiceNotification
from apps.subscriptions.models.choices import InvoiceNotificationStatus, EmailType

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_invoice_notification_email_task(
        self,
        notification_id: int,
        user_id: int,
        invoice_url: str | None = None,
):
    notification = StripeInvoiceNotification.objects.get(id=notification_id)

    if notification.status == InvoiceNotificationStatus.SENT:
        return

    user = User.objects.get(id=user_id)

    try:
        if notification.email_type == EmailType.PAYMENT_SUCCEEDED:
            send_pro_payment_success_email(user=user, invoice_url=invoice_url)

        elif notification.email_type == EmailType.PAYMENT_FAILED:
            send_pro_payment_failed_email(user=user, invoice_url=invoice_url)

        else:
            notification.status = InvoiceNotificationStatus.SKIPPED
            notification.error_message = f"Unknown email_type={notification.email_type}"
            notification.save(update_fields=["status", "error_message", "updated_at"])
            return

    except Exception as exc:
        notification.status = InvoiceNotificationStatus.FAILED
        notification.failed_at = timezone.now()
        notification.error_message = str(exc)
        notification.save(
            update_fields=[
                "status",
                "failed_at",
                "error_message",
                "updated_at",
            ]
        )
        raise

    notification.status = InvoiceNotificationStatus.SENT
    notification.sent_at = timezone.now()
    notification.error_message = None
    notification.save(
        update_fields=[
            "status",
            "sent_at",
            "error_message",
            "updated_at",
        ]
    )
