from contextlib import nullcontext
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models.choices import EmailType
from apps.subscriptions.webhook_handlers.dtos import PaidSubscriptionDTO
from apps.subscriptions.webhook_handlers.exceptions import StripeWebhookProcessingError
from apps.subscriptions.webhook_handlers.invoices import handle_invoice_paid


class TestHandleInvoicePaid(TestCase):
    def setUp(self):
        now = timezone.make_aware(datetime(2026, 1, 1, 12, 0, 0))

        self.invoice = SimpleNamespace(id="in_test_123")

        self.paid_subscription = PaidSubscriptionDTO(
            stripe_customer_id="cus_test_123",
            stripe_subscription_id="sub_test_123",
            stripe_status="active",
            started_at=now,
            current_period_end=now,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
            latest_invoice_id="in_test_123",
            invoice_url="https://stripe.test/invoice/in_test_123",
        )

        self.user_subscription = SimpleNamespace(user_id=10)

        self.atomic_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices.transaction.atomic",
        )
        self.atomic_mock.return_value = nullcontext()

        self.build_paid_subscription_dto_from_invoice_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices."
            "build_paid_subscription_dto_from_invoice",
        )

        self.mark_subscription_paid_mock = self._patch(
            "apps.subscriptions.webhook_handlers.invoices.mark_subscription_paid",
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

    def test_marks_subscription_as_paid_and_queues_payment_success_email(self):
        self.build_paid_subscription_dto_from_invoice_mock.return_value = (
            self.paid_subscription
        )
        self.mark_subscription_paid_mock.return_value = self.user_subscription

        handle_invoice_paid(self.invoice)

        self.build_paid_subscription_dto_from_invoice_mock.assert_called_once_with(
            self.invoice
        )
        self.atomic_mock.assert_called_once_with()
        self.mark_subscription_paid_mock.assert_called_once_with(self.paid_subscription)
        self.queue_invoice_email_notification_mock.assert_called_once_with(
            stripe_invoice_id=self.paid_subscription.latest_invoice_id,
            email_type=EmailType.PAYMENT_SUCCEEDED,
            user_id=self.user_subscription.user_id,
            invoice_url=self.paid_subscription.invoice_url,
        )

    def test_raises_error_when_subscription_could_not_be_marked_as_paid(self):
        self.build_paid_subscription_dto_from_invoice_mock.return_value = (
            self.paid_subscription
        )
        self.mark_subscription_paid_mock.return_value = None

        with self.assertRaisesRegex(
                StripeWebhookProcessingError,
                "Could not mark subscription as paid. invoice_id=in_test_123",
        ):
            handle_invoice_paid(self.invoice)

        self.build_paid_subscription_dto_from_invoice_mock.assert_called_once_with(
            self.invoice
        )
        self.atomic_mock.assert_called_once_with()
        self.mark_subscription_paid_mock.assert_called_once_with(self.paid_subscription)
        self.queue_invoice_email_notification_mock.assert_not_called()

    def test_propagates_queue_notification_errors(self):
        self.build_paid_subscription_dto_from_invoice_mock.return_value = (
            self.paid_subscription
        )
        self.mark_subscription_paid_mock.return_value = self.user_subscription
        self.queue_invoice_email_notification_mock.side_effect = RuntimeError(
            "Could not create email notification",
        )

        with self.assertRaisesRegex(
                RuntimeError, "Could not create email notification"
        ):
            handle_invoice_paid(self.invoice)

        self.build_paid_subscription_dto_from_invoice_mock.assert_called_once_with(
            self.invoice
        )
        self.atomic_mock.assert_called_once_with()
        self.mark_subscription_paid_mock.assert_called_once_with(self.paid_subscription)
        self.queue_invoice_email_notification_mock.assert_called_once_with(
            stripe_invoice_id=self.paid_subscription.latest_invoice_id,
            email_type=EmailType.PAYMENT_SUCCEEDED,
            user_id=self.user_subscription.user_id,
            invoice_url=self.paid_subscription.invoice_url,
        )
