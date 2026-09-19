import factory

from apps.subscriptions.models import StripeInvoiceNotification
from apps.subscriptions.models.choices import EmailType, InvoiceNotificationStatus


class StripeInvoiceNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StripeInvoiceNotification

    stripe_invoice_id = factory.Sequence(lambda n: f"in_test_{n}")
    email_type = EmailType.PAYMENT_SUCCEEDED
    status = InvoiceNotificationStatus.PENDING

    sent_at = None
    failed_at = None
    error_message = None
