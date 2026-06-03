from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.subscriptions.models.choices import EmailType
from apps.subscriptions.webhook_handlers.dtos import FailedSubscriptionPaymentDTO
from apps.subscriptions.webhook_handlers.invoices import handle_invoice_payment_failed


class TestHandleInvoicePaymentFailed(TestCase):
    def setUp(self):
        self.invoice = SimpleNamespace(id="in_test_failed_123")

        self.failed_payment = FailedSubscriptionPaymentDTO(
            stripe_customer_id="cus_test_123",
            stripe_subscription_id="sub_test_123",
            stripe_status="past_due",
            latest_invoice_id="in_test_failed_123",
            invoice_url="https://stripe.test/invoice/in_test_failed_123",
        )

        self.user_subscription = SimpleNamespace(user_id=10)

        self.atomic_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices.transaction.atomic",
        )
        self.atomic_mock.return_value = nullcontext()

        self.build_failed_subscription_payment_dto_from_invoice_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices."
            "build_failed_subscription_payment_dto_from_invoice",
        )

        self.mark_subscription_payment_failed_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices."
            "mark_subscription_payment_failed",
        )

        self.queue_invoice_email_notification_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices."
            "queue_invoice_email_notification",
        )

    def _patch(self, target):
        patcher = patch(target)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_marks_subscription_payment_as_failed_and_queues_payment_failed_email(self):
        self.build_failed_subscription_payment_dto_from_invoice_mock.return_value = self.failed_payment
        self.mark_subscription_payment_failed_mock.return_value = self.user_subscription

        handle_invoice_payment_failed(self.invoice)

        self.build_failed_subscription_payment_dto_from_invoice_mock.assert_called_once_with(self.invoice)
        self.atomic_mock.assert_called_once_with()
        self.mark_subscription_payment_failed_mock.assert_called_once_with(self.failed_payment)
        self.queue_invoice_email_notification_mock.assert_called_once_with(
            stripe_invoice_id=self.failed_payment.latest_invoice_id,
            email_type=EmailType.PAYMENT_FAILED,
            user_id=self.user_subscription.user_id,
            invoice_url=self.failed_payment.invoice_url,
        )

    def test_propagates_mark_subscription_payment_failed_errors(self):
        self.build_failed_subscription_payment_dto_from_invoice_mock.return_value = self.failed_payment
        self.mark_subscription_payment_failed_mock.side_effect = RuntimeError(
            "Could not mark subscription payment as failed",
        )

        with self.assertRaisesRegex(
                RuntimeError,
                "Could not mark subscription payment as failed",
        ):
            handle_invoice_payment_failed(self.invoice)

        self.build_failed_subscription_payment_dto_from_invoice_mock.assert_called_once_with(self.invoice)
        self.atomic_mock.assert_called_once_with()
        self.mark_subscription_payment_failed_mock.assert_called_once_with(self.failed_payment)
        self.queue_invoice_email_notification_mock.assert_not_called()

    def test_propagates_queue_notification_errors(self):
        self.build_failed_subscription_payment_dto_from_invoice_mock.return_value = self.failed_payment
        self.mark_subscription_payment_failed_mock.return_value = self.user_subscription
        self.queue_invoice_email_notification_mock.side_effect = RuntimeError(
            "Could not create payment failed email notification",
        )

        with self.assertRaisesRegex(
                RuntimeError,
                "Could not create payment failed email notification",
        ):
            handle_invoice_payment_failed(self.invoice)

        self.build_failed_subscription_payment_dto_from_invoice_mock.assert_called_once_with(self.invoice)
        self.atomic_mock.assert_called_once_with()
        self.mark_subscription_payment_failed_mock.assert_called_once_with(self.failed_payment)
        self.queue_invoice_email_notification_mock.assert_called_once_with(
            stripe_invoice_id=self.failed_payment.latest_invoice_id,
            email_type=EmailType.PAYMENT_FAILED,
            user_id=self.user_subscription.user_id,
            invoice_url=self.failed_payment.invoice_url,
        )
