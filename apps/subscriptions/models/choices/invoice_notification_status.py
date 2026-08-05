from django.db import models


class EmailType(models.TextChoices):
    PAYMENT_SUCCEEDED = "payment_succeeded", "Payment succeeded"
    PAYMENT_FAILED = "payment_failed", "Payment failed"


class InvoiceNotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"
