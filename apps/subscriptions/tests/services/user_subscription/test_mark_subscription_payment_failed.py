from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
from apps.subscriptions.services.user_subscription import mark_subscription_payment_failed
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class MarkSubscriptionPaymentFailedTests(TestCase):
    def setUp(self):
        self.user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
        )

        self.failed_payment = SimpleNamespace(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            stripe_status="past_due",
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    def test_marks_subscription_payment_as_failed(
            self,
            mock_map_stripe_subscription_status,
    ):
        mock_map_stripe_subscription_status.return_value = "past_due"

        result = mark_subscription_payment_failed(self.failed_payment)

        self.user_subscription.refresh_from_db()

        self.assertEqual(result.pk, self.user_subscription.pk)
        self.assertEqual(self.user_subscription.status, "past_due")

        mock_map_stripe_subscription_status.assert_called_once_with(
            "past_due",
            False,
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch("apps.subscriptions.models.UserSubscription.save", autospec=True)
    def test_saves_only_status_and_updated_at_fields(
            self,
            mock_save,
            mock_map_stripe_subscription_status,
    ):
        mock_map_stripe_subscription_status.return_value = "past_due"

        result = mark_subscription_payment_failed(self.failed_payment)

        self.assertEqual(result.pk, self.user_subscription.pk)
        self.assertEqual(result.status, "past_due")

        mock_save.assert_called_once_with(
            result,
            update_fields=["status", "updated_at"],
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    def test_ignores_event_for_non_current_subscription(
        self,
        mock_map_stripe_subscription_status,
    ):
        self.user_subscription.stripe_subscription_id = "sub_new"
        self.user_subscription.save(update_fields=["stripe_subscription_id"])

        failed_payment = SimpleNamespace(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            stripe_status="past_due",
        )

        result = mark_subscription_payment_failed(failed_payment)

        self.user_subscription.refresh_from_db()

        self.assertIsNone(result)
        self.assertEqual(self.user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(
            self.user_subscription.status,
            UserSubscriptionStatus.ACTIVE,
        )
        mock_map_stripe_subscription_status.assert_not_called()

    def test_locks_the_user_subscription_row(self):
        with patch.object(
            UserSubscription.objects,
            "select_for_update",
        ) as select_for_update_mock:
            select_for_update_mock.return_value.get.return_value = (
                self.user_subscription
            )

            mark_subscription_payment_failed(self.failed_payment)

        select_for_update_mock.assert_called_once_with()
        select_for_update_mock.return_value.get.assert_called_once_with(
            stripe_customer_id="cus_123",
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    def test_raises_error_when_user_subscription_does_not_exist(
            self,
            mock_map_stripe_subscription_status,
    ):
        failed_payment = SimpleNamespace(
            stripe_customer_id="cus_missing",
            stripe_subscription_id="sub_123",
            stripe_status="past_due",
        )

        with self.assertRaises(UserSubscriptionNotFoundError):
            mark_subscription_payment_failed(failed_payment)

        mock_map_stripe_subscription_status.assert_not_called()
