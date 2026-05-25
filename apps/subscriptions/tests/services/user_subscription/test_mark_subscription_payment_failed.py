from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
from apps.subscriptions.services.user_subscription import mark_subscription_payment_failed
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class MarkSubscriptionPaymentFailedTests(TestCase):
    def setUp(self):
        self.user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            status="active",
        )

        self.failed_payment = SimpleNamespace(
            stripe_customer_id="cus_123",
            stripe_status="past_due",
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_marks_subscription_payment_as_failed(
            self,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        mock_get_user_subscription_by_customer_id.return_value = self.user_subscription
        mock_map_stripe_subscription_status.return_value = "past_due"

        result = mark_subscription_payment_failed(self.failed_payment)

        self.user_subscription.refresh_from_db()

        self.assertEqual(result, self.user_subscription)
        self.assertEqual(self.user_subscription.status, "past_due")

        mock_get_user_subscription_by_customer_id.assert_called_once_with("cus_123")
        mock_map_stripe_subscription_status.assert_called_once_with(
            "past_due",
            False,
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    @patch("apps.subscriptions.models.UserSubscription.save", autospec=True)
    def test_saves_only_status_and_updated_at_fields(
            self,
            mock_save,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        mock_get_user_subscription_by_customer_id.return_value = self.user_subscription
        mock_map_stripe_subscription_status.return_value = "past_due"

        result = mark_subscription_payment_failed(self.failed_payment)

        self.assertEqual(result, self.user_subscription)
        self.assertEqual(self.user_subscription.status, "past_due")

        mock_save.assert_called_once_with(
            self.user_subscription,
            update_fields=["status", "updated_at"],
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_raises_error_when_user_subscription_does_not_exist(
            self,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        mock_get_user_subscription_by_customer_id.side_effect = UserSubscriptionNotFoundError("Subscription not found")

        with self.assertRaisesMessage(UserSubscriptionNotFoundError, "Subscription not found"):
            mark_subscription_payment_failed(self.failed_payment)

        mock_get_user_subscription_by_customer_id.assert_called_once_with("cus_123")
        mock_map_stripe_subscription_status.assert_not_called()
