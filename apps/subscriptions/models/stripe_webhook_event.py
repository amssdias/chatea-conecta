from django.db import models

from apps.subscriptions.models.choices import StripeWebhookEventStatus, EmailType, InvoiceNotificationStatus


class StripeWebhookEvent(models.Model):
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20,
        choices=StripeWebhookEventStatus.choices,
        default=StripeWebhookEventStatus.PENDING,
    )
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} · {self.get_status_display()} · {self.stripe_event_id}"


class StripeInvoiceNotification(models.Model):

    stripe_invoice_id = models.CharField(max_length=255)
    email_type = models.CharField(max_length=32, choices=EmailType.choices)

    status = models.CharField(
        max_length=20,
        choices=InvoiceNotificationStatus.choices,
        default=InvoiceNotificationStatus.PENDING,
    )

    sent_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("stripe_invoice_id", "email_type")

    def __str__(self):
        return f"{self.get_email_type_display()} · {self.get_status_display()} · {self.stripe_invoice_id}"
