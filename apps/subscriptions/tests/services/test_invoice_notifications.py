from unittest.mock import patch

from django.test import TestCase

from apps.subscriptions.models import StripeInvoiceNotification
from apps.subscriptions.models.choices import EmailType, InvoiceNotificationStatus
from apps.subscriptions.services.invoice_notifications import (
    queue_invoice_email_notification,
)
from apps.subscriptions.tests.factories import StripeInvoiceNotificationFactory


class TestQueueInvoiceEmailNotification(TestCase):
    def setUp(self):
        self.stripe_invoice_id = "in_test_123"
        self.email_type = EmailType.PAYMENT_SUCCEEDED
        self.user_id = 10
        self.invoice_url = "https://stripe.test/invoice/in_test_123"

    @patch(
        "apps.subscriptions.services.invoice_notifications.send_invoice_notification_email_task.delay"
    )
    def test_creates_pending_notification_and_queues_email_task_on_commit(
            self, delay_mock
    ):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            result = queue_invoice_email_notification(
                stripe_invoice_id=self.stripe_invoice_id,
                email_type=self.email_type,
                user_id=self.user_id,
                invoice_url=self.invoice_url,
            )

        self.assertTrue(result)
        self.assertEqual(len(callbacks), 1)

        notification = StripeInvoiceNotification.objects.get(
            stripe_invoice_id=self.stripe_invoice_id,
            email_type=self.email_type,
        )

        self.assertEqual(notification.status, InvoiceNotificationStatus.PENDING)
        self.assertIsNone(notification.sent_at)
        self.assertIsNone(notification.failed_at)
        self.assertIsNone(notification.error_message)

        delay_mock.assert_called_once_with(
            notification.id,
            self.user_id,
            self.invoice_url,
        )

    @patch(
        "apps.subscriptions.services.invoice_notifications.send_invoice_notification_email_task.delay"
    )
    def test_returns_false_when_stripe_invoice_id_is_missing(self, delay_mock):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            result = queue_invoice_email_notification(
                stripe_invoice_id="",
                email_type=self.email_type,
                user_id=self.user_id,
                invoice_url=self.invoice_url,
            )

        self.assertFalse(result)
        self.assertEqual(len(callbacks), 0)
        self.assertEqual(StripeInvoiceNotification.objects.count(), 0)
        delay_mock.assert_not_called()

    @patch(
        "apps.subscriptions.services.invoice_notifications.send_invoice_notification_email_task.delay"
    )
    def test_returns_false_when_notification_already_exists_and_skipped(self, delay_mock):
        StripeInvoiceNotificationFactory(
            stripe_invoice_id=self.stripe_invoice_id,
            email_type=self.email_type,
            status=InvoiceNotificationStatus.SKIPPED,
        )

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            result = queue_invoice_email_notification(
                stripe_invoice_id=self.stripe_invoice_id,
                email_type=self.email_type,
                user_id=self.user_id,
                invoice_url=self.invoice_url,
            )

        self.assertFalse(result)
        self.assertEqual(len(callbacks), 0)
        self.assertEqual(StripeInvoiceNotification.objects.count(), 1)
        delay_mock.assert_not_called()

    @patch(
        "apps.subscriptions.services.invoice_notifications.send_invoice_notification_email_task.delay"
    )
    def test_allows_same_invoice_with_different_email_type(self, delay_mock):
        StripeInvoiceNotificationFactory(
            stripe_invoice_id=self.stripe_invoice_id,
            email_type=EmailType.PAYMENT_FAILED,
            status=InvoiceNotificationStatus.PENDING,
        )

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            result = queue_invoice_email_notification(
                stripe_invoice_id=self.stripe_invoice_id,
                email_type=EmailType.PAYMENT_SUCCEEDED,
                user_id=self.user_id,
                invoice_url=self.invoice_url,
            )

        self.assertTrue(result)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(StripeInvoiceNotification.objects.count(), 2)

        notification = StripeInvoiceNotification.objects.get(
            stripe_invoice_id=self.stripe_invoice_id,
            email_type=EmailType.PAYMENT_SUCCEEDED,
        )

        self.assertEqual(notification.status, InvoiceNotificationStatus.PENDING)

        delay_mock.assert_called_once_with(
            notification.id,
            self.user_id,
            self.invoice_url,
        )

    @patch(
        "apps.subscriptions.services.invoice_notifications.send_invoice_notification_email_task.delay"
    )
    def test_queues_task_with_none_invoice_url(self, delay_mock):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            result = queue_invoice_email_notification(
                stripe_invoice_id=self.stripe_invoice_id,
                email_type=self.email_type,
                user_id=self.user_id,
                invoice_url=None,
            )

        self.assertTrue(result)
        self.assertEqual(len(callbacks), 1)

        notification = StripeInvoiceNotification.objects.get(
            stripe_invoice_id=self.stripe_invoice_id,
            email_type=self.email_type,
        )

        delay_mock.assert_called_once_with(
            notification.id,
            self.user_id,
            None,
        )
