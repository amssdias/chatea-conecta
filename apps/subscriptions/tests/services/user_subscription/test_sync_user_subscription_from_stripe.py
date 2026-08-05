from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
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
    def test_syncs_user_subscription_from_stripe(
            self,
            mock_map_stripe_subscription_status,
    ):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
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

        mock_map_stripe_subscription_status.return_value = UserSubscriptionStatus.ACTIVE.value

        with patch.object(UserSubscription, "save", autospec=True) as mock_save:
            mock_save.side_effect = lambda instance, **kwargs: None
            result = sync_user_subscription_from_stripe(subscription_sync)

        self.assertEqual(result.pk, user_subscription.pk)
        self.assertEqual(result.stripe_subscription_id, "sub_123")
        self.assertEqual(result.status, "active")
        self.assertEqual(result.started_at, started_at)
        self.assertEqual(result.current_period_start, current_period_start)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertFalse(result.cancel_at_period_end)
        self.assertIsNone(result.canceled_at)
        self.assertIsNone(result.ended_at)

        mock_map_stripe_subscription_status.assert_called_once_with(
            "active",
            False,
        )
        mock_save.assert_called_once_with(
            result,
            update_fields=[
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

    def test_keeps_existing_started_at_when_subscription_id_did_not_change(self):
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

        sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, existing_started_at)

    def test_sets_started_at_when_missing_even_if_subscription_id_did_not_change(self):
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

        sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, started_at)

    @patch(f"{MODULE_PATH}.map_stripe_subscription_status")
    def test_ignores_event_for_non_current_subscription(
        self,
        mock_map_stripe_subscription_status,
    ):
        original_started_at = timezone.now() - timedelta(days=90)
        original_period_start = timezone.now() - timedelta(days=5)
        original_period_end = timezone.now() + timedelta(days=25)

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
            status=UserSubscriptionStatus.ACTIVE,
            started_at=original_started_at,
            current_period_start=original_period_start,
            current_period_end=original_period_end,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            stripe_status="canceled",
            started_at=timezone.now() - timedelta(days=365),
            current_period_start=timezone.now() - timedelta(days=180),
            current_period_end=timezone.now() - timedelta(days=150),
            cancel_at_period_end=True,
            canceled_at=timezone.now() - timedelta(days=150),
            ended_at=timezone.now() - timedelta(days=150),
        )

        result = sync_user_subscription_from_stripe(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertIsNone(result)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(user_subscription.started_at, original_started_at)
        self.assertEqual(user_subscription.current_period_start, original_period_start)
        self.assertEqual(user_subscription.current_period_end, original_period_end)
        self.assertFalse(user_subscription.cancel_at_period_end)
        self.assertIsNone(user_subscription.canceled_at)
        self.assertIsNone(user_subscription.ended_at)
        mock_map_stripe_subscription_status.assert_not_called()

    def test_locks_the_user_subscription_row(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )

        with patch.object(
            UserSubscription.objects,
            "select_for_update",
        ) as select_for_update_mock:
            select_for_update_mock.return_value.get.return_value = user_subscription

            sync_user_subscription_from_stripe(subscription_sync)

        select_for_update_mock.assert_called_once_with()
        select_for_update_mock.return_value.get.assert_called_once_with(
            stripe_customer_id="cus_123",
        )

    def test_raises_error_when_user_subscription_does_not_exist(self):
        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_missing",
        )

        with self.assertRaises(UserSubscriptionNotFoundError):
            sync_user_subscription_from_stripe(subscription_sync)
