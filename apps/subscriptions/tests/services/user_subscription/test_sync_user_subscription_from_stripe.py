from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.user_subscription import sync_user_subscription_from_stripe
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class SyncUserSubscriptionFromStripeTests(TestCase):
    def build_subscription_sync_dto(
            self,
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            stripe_status="active",
            started_at=None,
            current_period_start=None,
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
            current_period_start=current_period_start or timezone.now(),
            current_period_end=current_period_end or timezone.now() + timedelta(days=30),
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_syncs_user_subscription_from_stripe(
            self,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id=None,
            started_at=None,
            current_period_end=None,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        started_at = timezone.now() - timedelta(days=1)
        current_period_start = timezone.now()
        current_period_end = timezone.now() + timedelta(days=30)

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            stripe_status="active",
            started_at=started_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription
        mock_map_stripe_subscription_status.return_value = UserSubscriptionStatus.ACTIVE.value

        with patch.object(user_subscription, "save", wraps=user_subscription.save) as mock_save:
            result = sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(result, user_subscription)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_123")
        self.assertEqual(user_subscription.status, "active")
        self.assertEqual(user_subscription.started_at, started_at)
        self.assertEqual(user_subscription.current_period_start, current_period_start)
        self.assertEqual(user_subscription.current_period_end, current_period_end)
        self.assertFalse(user_subscription.cancel_at_period_end)
        self.assertIsNone(user_subscription.canceled_at)
        self.assertIsNone(user_subscription.ended_at)

        mock_get_user_subscription_by_customer_id.assert_called_once_with("cus_123")
        mock_map_stripe_subscription_status.assert_called_once_with(
            "active",
            False,
        )
        mock_save.assert_called_once_with(
            update_fields=[
                "stripe_subscription_id",
                "status",
                "started_at",
                "current_period_start",
                "current_period_end",
                "cancel_at_period_end",
                "canceled_at",
                "ended_at",
                "updated_at",
            ],
        )

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_keeps_existing_started_at_when_subscription_id_did_not_change(
            self,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        existing_started_at = timezone.now() - timedelta(days=90)
        new_started_at = timezone.now()

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            started_at=existing_started_at,
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            started_at=new_started_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription
        mock_map_stripe_subscription_status.return_value = UserSubscriptionStatus.ACTIVE.value

        sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, existing_started_at)

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_updates_started_at_when_subscription_id_changed(
            self,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        old_started_at = timezone.now() - timedelta(days=90)
        new_started_at = timezone.now()

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            started_at=old_started_at,
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
            started_at=new_started_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription
        mock_map_stripe_subscription_status.return_value = UserSubscriptionStatus.ACTIVE.value

        sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(user_subscription.started_at, new_started_at)

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    @patch(f"{MODULE_PATH}.get_user_subscription_by_customer_id")
    def test_sets_started_at_when_missing_even_if_subscription_id_did_not_change(
            self,
            mock_get_user_subscription_by_customer_id,
            mock_map_stripe_subscription_status,
    ):
        started_at = timezone.now()

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            started_at=None,
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            started_at=started_at,
        )

        mock_get_user_subscription_by_customer_id.return_value = user_subscription
        mock_map_stripe_subscription_status.return_value = UserSubscriptionStatus.ACTIVE.value

        sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, started_at)
