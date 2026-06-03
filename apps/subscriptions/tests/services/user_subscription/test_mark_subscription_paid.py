from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.user_subscription import mark_subscription_paid
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class MarkSubscriptionPaidTests(TestCase):
    def build_paid_subscription_dto(
            self,
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            stripe_status="active",
            started_at=None,
            current_period_end=None,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
    ):
        return SimpleNamespace(
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_status=stripe_status,
            started_at=started_at or timezone.now(),
            current_period_end=current_period_end or timezone.now() + timedelta(days=30),
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_marks_subscription_as_paid(self, mock_get_user_subscription_by_customer_id):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id=None,
            status=UserSubscriptionStatus.INACTIVE,
            started_at=None,
            current_period_end=None,
            cancel_at_period_end=True,
            canceled_at=timezone.now(),
            ended_at=timezone.now(),
        )

        started_at = timezone.now() - timedelta(days=1)
        current_period_end = timezone.now() + timedelta(days=30)

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            stripe_status="active",
            started_at=started_at,
            current_period_end=current_period_end,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        with patch.object(user_subscription, "save", wraps=user_subscription.save) as mock_save:
            result = mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(result, user_subscription)
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_123")
        self.assertEqual(user_subscription.started_at, started_at)
        self.assertEqual(user_subscription.current_period_end, current_period_end)
        self.assertFalse(user_subscription.cancel_at_period_end)
        self.assertIsNone(user_subscription.canceled_at)
        self.assertIsNone(user_subscription.ended_at)

        mock_get_user_subscription_by_customer_id.assert_called_once_with("cus_123")
        mock_save.assert_called_once_with(
            update_fields=[
                "stripe_subscription_id",
                "status",
                "started_at",
                "current_period_end",
                "cancel_at_period_end",
                "canceled_at",
                "ended_at",
                "updated_at",
            ],
        )

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_keeps_existing_started_at_when_subscription_id_did_not_change(self,
                                                                           mock_get_user_subscription_by_customer_id):
        existing_started_at = timezone.now() - timedelta(days=90)
        new_started_at = timezone.now()

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
            started_at=existing_started_at,
        )

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            started_at=new_started_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, existing_started_at)

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_updates_started_at_when_subscription_id_changed(self, mock_get_user_subscription_by_customer_id):
        old_started_at = timezone.now() - timedelta(days=90)
        new_started_at = timezone.now()

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            status=UserSubscriptionStatus.ACTIVE,
            started_at=old_started_at,
        )

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
            started_at=new_started_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(user_subscription.started_at, new_started_at)

    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_sets_started_at_when_missing_even_if_subscription_id_did_not_change(
            self,
            mock_get_user_subscription_by_customer_id,
    ):
        started_at = timezone.now()

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
            started_at=None,
        )

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            started_at=started_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, started_at)
