from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.subscriptions.webhook_handlers.dtos import (
    PaidSubscriptionDTO,
    FailedSubscriptionPaymentDTO,
    StripeSubscriptionSyncDTO,
    StripeSubscriptionDeletedDTO,
)
from apps.subscriptions.webhook_handlers.exceptions import (
    InvalidStripeInvoiceError,
    MissingStripeInvoiceCustomerError,
    MissingStripeInvoiceSubscriptionError,
    MissingStripeSubscriptionCustomerError,
)
from apps.subscriptions.webhook_handlers.mappers import (
    build_paid_subscription_dto_from_invoice,
    build_failed_subscription_payment_dto_from_invoice,
    build_subscription_sync_dto,
    build_subscription_deleted_dto,
)

MODULE_PATH = "apps.subscriptions.webhook_handlers.mappers"


class BuildPaidSubscriptionDTOFromInvoiceTests(SimpleTestCase):
    def setUp(self):
        self.invoice = SimpleNamespace(
            id="in_123",
            customer="cus_123",
        )

        self.subscription = SimpleNamespace(
            id="sub_123",
            status="active",
            start_date=1710000000,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_raises_error_when_invoice_has_no_customer(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
    ):
        self.invoice.customer = None
        mock_get_invoice_subscription_id.return_value = "sub_123"

        with self.assertRaisesMessage(
                InvalidStripeInvoiceError,
                "Missing customer on paid invoice. invoice_id=in_123",
        ):
            build_paid_subscription_dto_from_invoice(self.invoice)

        mock_get_invoice_subscription_id.assert_called_once_with(self.invoice)
        mock_retrieve_subscription.assert_not_called()

    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_raises_error_when_invoice_has_no_subscription_id(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
    ):
        mock_get_invoice_subscription_id.return_value = None

        with self.assertRaisesMessage(
                InvalidStripeInvoiceError,
                "Missing subscription on paid invoice. invoice_id=in_123",
        ):
            build_paid_subscription_dto_from_invoice(self.invoice)

        mock_get_invoice_subscription_id.assert_called_once_with(self.invoice)
        mock_retrieve_subscription.assert_not_called()

    @patch(f"{MODULE_PATH}.get_invoice_url")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_builds_paid_subscription_dto_from_invoice(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
            mock_get_invoice_url,
    ):
        started_at = datetime(2024, 3, 9, tzinfo=timezone.utc)
        canceled_at = None
        ended_at = None

        current_period_start = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_end = datetime(2024, 4, 9, tzinfo=timezone.utc)

        mock_get_subscription_current_period_start.return_value = current_period_start
        mock_get_subscription_current_period_end.return_value = current_period_end
        mock_get_invoice_subscription_id.return_value = "sub_123"
        mock_retrieve_subscription.return_value = self.subscription
        mock_from_stripe_timestamp.side_effect = [
            started_at,
            canceled_at,
            ended_at,
        ]
        mock_get_invoice_url.return_value = "https://stripe.com/invoice/in_123"

        result = build_paid_subscription_dto_from_invoice(self.invoice)

        self.assertIsInstance(result, PaidSubscriptionDTO)
        self.assertEqual(result.stripe_customer_id, "cus_123")
        self.assertEqual(result.stripe_subscription_id, "sub_123")
        self.assertEqual(result.stripe_status, "active")
        self.assertEqual(result.started_at, started_at)
        self.assertEqual(result.current_period_start, current_period_start)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertFalse(result.cancel_at_period_end)
        self.assertIsNone(result.canceled_at)
        self.assertIsNone(result.ended_at)
        self.assertEqual(result.latest_invoice_id, "in_123")
        self.assertEqual(result.invoice_url, "https://stripe.com/invoice/in_123")

        mock_get_invoice_subscription_id.assert_called_once_with(self.invoice)
        mock_retrieve_subscription.assert_called_once_with("sub_123")
        mock_get_subscription_current_period_end.assert_called_once_with(
            self.subscription
        )
        mock_get_subscription_current_period_start.assert_called_once_with(
            self.subscription
        )
        mock_get_invoice_url.assert_called_once_with(self.invoice)

        mock_from_stripe_timestamp.assert_any_call(self.subscription.start_date)
        mock_from_stripe_timestamp.assert_any_call(self.subscription.canceled_at)
        mock_from_stripe_timestamp.assert_any_call(self.subscription.ended_at)
        self.assertEqual(mock_from_stripe_timestamp.call_count, 3)

    @patch(f"{MODULE_PATH}.get_invoice_url")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_builds_dto_for_subscription_canceling_at_period_end(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
            mock_get_invoice_url,
    ):
        self.subscription.status = "active"
        self.subscription.cancel_at_period_end = True

        started_at = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_start = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_end = datetime(2024, 4, 9, tzinfo=timezone.utc)

        mock_get_invoice_subscription_id.return_value = "sub_123"
        mock_retrieve_subscription.return_value = self.subscription
        mock_from_stripe_timestamp.side_effect = [
            started_at,
            None,
            None,
        ]
        mock_get_subscription_current_period_start.return_value = current_period_start
        mock_get_subscription_current_period_end.return_value = current_period_end
        mock_get_invoice_url.return_value = "https://stripe.com/invoice/in_123"

        result = build_paid_subscription_dto_from_invoice(self.invoice)

        self.assertEqual(result.stripe_status, "active")
        self.assertTrue(result.cancel_at_period_end)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertIsNone(result.canceled_at)
        self.assertIsNone(result.ended_at)


class BuildFailedSubscriptionPaymentDTOFromInvoiceTests(SimpleTestCase):
    def setUp(self):
        self.invoice = SimpleNamespace(
            id="in_123",
            customer="cus_123",
        )

        self.subscription = SimpleNamespace(
            id="sub_123",
            status="past_due",
        )

    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_raises_error_when_invoice_has_no_customer(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
    ):
        self.invoice.customer = None

        with self.assertRaisesMessage(
                MissingStripeInvoiceCustomerError,
                "Missing customer on failed invoice payment. invoice_id=in_123",
        ):
            build_failed_subscription_payment_dto_from_invoice(self.invoice)

        mock_get_invoice_subscription_id.assert_not_called()
        mock_retrieve_subscription.assert_not_called()

    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_raises_error_when_invoice_has_no_subscription_id(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
    ):
        mock_get_invoice_subscription_id.return_value = None

        with self.assertRaisesMessage(
                MissingStripeInvoiceSubscriptionError,
                "Missing subscription on failed invoice payment. invoice_id=in_123",
        ):
            build_failed_subscription_payment_dto_from_invoice(self.invoice)

        mock_get_invoice_subscription_id.assert_called_once_with(self.invoice)
        mock_retrieve_subscription.assert_not_called()

    @patch(f"{MODULE_PATH}.get_invoice_url")
    @patch(f"{MODULE_PATH}.retrieve_subscription")
    @patch(f"{MODULE_PATH}.get_invoice_subscription_id")
    def test_builds_failed_subscription_payment_dto_from_invoice(
            self,
            mock_get_invoice_subscription_id,
            mock_retrieve_subscription,
            mock_get_invoice_url,
    ):
        mock_get_invoice_subscription_id.return_value = "sub_123"
        mock_retrieve_subscription.return_value = self.subscription
        mock_get_invoice_url.return_value = "https://stripe.com/invoice/in_123"

        result = build_failed_subscription_payment_dto_from_invoice(self.invoice)

        self.assertIsInstance(result, FailedSubscriptionPaymentDTO)
        self.assertEqual(result.stripe_customer_id, "cus_123")
        self.assertEqual(result.stripe_subscription_id, "sub_123")
        self.assertEqual(result.stripe_status, "past_due")
        self.assertEqual(result.latest_invoice_id, "in_123")
        self.assertEqual(result.invoice_url, "https://stripe.com/invoice/in_123")

        mock_retrieve_subscription.assert_called_once_with("sub_123")
        mock_get_invoice_url.assert_called_once_with(self.invoice)

        self.assertEqual(mock_get_invoice_subscription_id.call_count, 1)
        mock_get_invoice_subscription_id.assert_any_call(self.invoice)


class BuildSubscriptionSyncDTOTests(SimpleTestCase):
    def setUp(self):
        self.subscription = SimpleNamespace(
            id="sub_123",
            customer="cus_123",
            status="active",
            start_date=1710000000,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    def test_builds_subscription_sync_dto(
            self,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
    ):
        started_at = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_start = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_end = datetime(2024, 4, 9, tzinfo=timezone.utc)

        mock_from_stripe_timestamp.side_effect = [
            started_at,
            None,
            None,
        ]
        mock_get_subscription_current_period_start.return_value = current_period_start
        mock_get_subscription_current_period_end.return_value = current_period_end

        result = build_subscription_sync_dto(self.subscription)

        self.assertIsInstance(result, StripeSubscriptionSyncDTO)
        self.assertEqual(result.stripe_customer_id, "cus_123")
        self.assertEqual(result.stripe_subscription_id, "sub_123")
        self.assertEqual(result.stripe_status, "active")
        self.assertEqual(result.started_at, started_at)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertFalse(result.cancel_at_period_end)
        self.assertIsNone(result.canceled_at)
        self.assertIsNone(result.ended_at)

        mock_get_subscription_current_period_end.assert_called_once_with(
            self.subscription
        )

        mock_from_stripe_timestamp.assert_any_call(self.subscription.start_date)
        mock_from_stripe_timestamp.assert_any_call(self.subscription.canceled_at)
        mock_from_stripe_timestamp.assert_any_call(self.subscription.ended_at)
        self.assertEqual(mock_from_stripe_timestamp.call_count, 3)

    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    def test_raises_error_when_subscription_has_no_customer(
            self,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
    ):
        self.subscription.customer = None

        with self.assertRaisesMessage(
                MissingStripeSubscriptionCustomerError,
                "Missing customer on Stripe subscription sync. stripe_subscription_id=sub_123",
        ):
            build_subscription_sync_dto(self.subscription)

        mock_from_stripe_timestamp.assert_not_called()
        mock_get_subscription_current_period_start.assert_not_called()
        mock_get_subscription_current_period_end.assert_not_called()

    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    def test_builds_dto_for_subscription_canceling_at_period_end(
            self,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
    ):
        self.subscription.status = "active"
        self.subscription.cancel_at_period_end = True

        started_at = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_start = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_end = datetime(2024, 4, 9, tzinfo=timezone.utc)

        mock_from_stripe_timestamp.side_effect = [
            started_at,
            None,
            None,
        ]
        mock_get_subscription_current_period_start.return_value = current_period_start
        mock_get_subscription_current_period_end.return_value = current_period_end

        result = build_subscription_sync_dto(self.subscription)

        self.assertEqual(result.stripe_status, "active")
        self.assertTrue(result.cancel_at_period_end)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertIsNone(result.canceled_at)
        self.assertIsNone(result.ended_at)


class BuildSubscriptionDeletedDTOTests(SimpleTestCase):
    def setUp(self):
        self.subscription = SimpleNamespace(
            id="sub_123",
            customer="cus_123",
            canceled_at=1710000000,
            ended_at=1710100000,
            cancel_at_period_end=False,
        )

    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    def test_builds_subscription_deleted_dto(
            self,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
    ):
        canceled_at = datetime(2024, 3, 9, tzinfo=timezone.utc)
        ended_at = datetime(2024, 3, 10, tzinfo=timezone.utc)
        current_period_start = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_end = datetime(2024, 4, 9, tzinfo=timezone.utc)

        mock_from_stripe_timestamp.side_effect = [
            canceled_at,
            ended_at,
        ]
        mock_get_subscription_current_period_start.return_value = current_period_start
        mock_get_subscription_current_period_end.return_value = current_period_end

        result = build_subscription_deleted_dto(self.subscription)

        self.assertIsInstance(result, StripeSubscriptionDeletedDTO)
        self.assertEqual(result.stripe_customer_id, "cus_123")
        self.assertEqual(result.stripe_subscription_id, "sub_123")
        self.assertEqual(result.canceled_at, canceled_at)
        self.assertEqual(result.ended_at, ended_at)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertFalse(result.cancel_at_period_end)

        mock_from_stripe_timestamp.assert_any_call(self.subscription.canceled_at)
        mock_from_stripe_timestamp.assert_any_call(self.subscription.ended_at)
        self.assertEqual(mock_from_stripe_timestamp.call_count, 2)

        mock_get_subscription_current_period_end.assert_called_once_with(
            self.subscription,
        )

    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    def test_raises_error_when_subscription_has_no_customer(
            self,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
    ):
        self.subscription.customer = None

        with self.assertRaisesMessage(
                MissingStripeSubscriptionCustomerError,
                "Missing customer on deleted Stripe subscription. stripe_subscription_id=sub_123",
        ):
            build_subscription_deleted_dto(self.subscription)

        mock_from_stripe_timestamp.assert_not_called()
        mock_get_subscription_current_period_start.assert_not_called()
        mock_get_subscription_current_period_end.assert_not_called()

    @patch(f"{MODULE_PATH}.get_subscription_current_period_end")
    @patch(f"{MODULE_PATH}.get_subscription_current_period_start")
    @patch(f"{MODULE_PATH}.from_stripe_timestamp")
    def test_builds_dto_when_subscription_was_cancel_at_period_end(
            self,
            mock_from_stripe_timestamp,
            mock_get_subscription_current_period_start,
            mock_get_subscription_current_period_end,
    ):
        self.subscription.cancel_at_period_end = True

        canceled_at = datetime(2024, 3, 9, tzinfo=timezone.utc)
        ended_at = datetime(2024, 3, 10, tzinfo=timezone.utc)
        current_period_start = datetime(2024, 3, 9, tzinfo=timezone.utc)
        current_period_end = datetime(2024, 4, 9, tzinfo=timezone.utc)

        mock_from_stripe_timestamp.side_effect = [
            canceled_at,
            ended_at,
        ]
        mock_get_subscription_current_period_start.return_value = current_period_start
        mock_get_subscription_current_period_end.return_value = current_period_end

        result = build_subscription_deleted_dto(self.subscription)

        self.assertTrue(result.cancel_at_period_end)
        self.assertEqual(result.canceled_at, canceled_at)
        self.assertEqual(result.ended_at, ended_at)
        self.assertEqual(result.current_period_end, current_period_end)
