from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.user_subscription import mark_subscription_deleted
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class MarkSubscriptionDeletedTests(TestCase):
    def build_deleted_subscription_dto(
            self,
            stripe_customer_id="cus_123",
            current_period_start=None,
            current_period_end=None,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
    ):
        return SimpleNamespace(
            stripe_customer_id=stripe_customer_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_marks_subscription_as_deleted(self, mock_get_user_subscription_by_customer_id):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            status=UserSubscriptionStatus.ACTIVE,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        current_period_start = timezone.now()
        current_period_end = timezone.now() + timedelta(days=10)
        canceled_at = timezone.now()
        ended_at = timezone.now() + timedelta(days=1)

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=True,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        with patch.object(user_subscription, "save", wraps=user_subscription.save) as mock_save:
            result = mark_subscription_deleted(deleted_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(result, user_subscription)
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.CANCELED)
        self.assertEqual(user_subscription.current_period_end, current_period_end)
        self.assertTrue(user_subscription.cancel_at_period_end)
        self.assertEqual(user_subscription.canceled_at, canceled_at)
        self.assertEqual(user_subscription.ended_at, ended_at)

        mock_get_user_subscription_by_customer_id.assert_called_once_with("cus_123")
        mock_save.assert_called_once_with(
            update_fields=[
                "status",
                "current_period_start",
                "current_period_end",
                "cancel_at_period_end",
                "canceled_at",
                "ended_at",
                "updated_at",
            ],
        )

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_uses_canceled_at_as_ended_at_when_ended_at_is_missing(self, mock_get_user_subscription_by_customer_id):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            status=UserSubscriptionStatus.ACTIVE,
            ended_at=None,
        )

        canceled_at = timezone.now()

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            canceled_at=canceled_at,
            ended_at=None,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        mark_subscription_deleted(deleted_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.ended_at, canceled_at)

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_returns_updated_user_subscription(self, mock_get_user_subscription_by_customer_id):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            status=UserSubscriptionStatus.ACTIVE,
        )

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            ended_at=timezone.now(),
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        result = mark_subscription_deleted(deleted_subscription)

        self.assertEqual(result, user_subscription)
