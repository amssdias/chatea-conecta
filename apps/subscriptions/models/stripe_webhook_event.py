from django.db import models

from apps.subscriptions.models.choices import StripeWebhookEventStatus


class StripeWebhookEvent(models.Model):
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=120)
    status = models.CharField(
        max_length=20,
        choices=StripeWebhookEventStatus.choices,
        default=StripeWebhookEventStatus.PROCESSED
    )
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StripeInvoiceNotification(models.Model):
    class EmailType(models.TextChoices):
        PAYMENT_SUCCEEDED = "payment_succeeded", "Payment succeeded"
        PAYMENT_FAILED = "payment_failed", "Payment failed"

    stripe_invoice_id = models.CharField(max_length=255)
    email_type = models.CharField(max_length=32, choices=EmailType.choices)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("stripe_invoice_id", "email_type")
