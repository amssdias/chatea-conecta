from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
from apps.subscriptions.services.user_subscription import (
    sync_user_subscription_from_checkout,
)
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class SyncUserSubscriptionFromCheckoutTests(TestCase):
    def build_subscription_sync_dto(
        self,
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_new",
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
            current_period_end=current_period_end
            or timezone.now() + timedelta(days=30),
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

    def test_replaces_current_subscription_with_the_checkout_subscription(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            status=UserSubscriptionStatus.CANCELED,
            started_at=timezone.now() - timedelta(days=365),
            current_period_start=timezone.now() - timedelta(days=365),
            current_period_end=timezone.now() - timedelta(days=335),
            cancel_at_period_end=True,
            canceled_at=timezone.now() - timedelta(days=335),
            ended_at=timezone.now() - timedelta(days=335),
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
            stripe_status="active",
            started_at=timezone.now() - timedelta(days=1),
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        result = sync_user_subscription_from_checkout(subscription_sync)

        user_subscription.refresh_from_db()

        self.assertEqual(result.pk, user_subscription.pk)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(user_subscription.started_at, subscription_sync.started_at)
        self.assertEqual(
            user_subscription.current_period_start,
            subscription_sync.current_period_start,
        )
        self.assertEqual(
            user_subscription.current_period_end,
            subscription_sync.current_period_end,
        )
        self.assertFalse(user_subscription.cancel_at_period_end)
        self.assertIsNone(user_subscription.canceled_at)
        self.assertIsNone(user_subscription.ended_at)

    def test_maps_the_stripe_status(self):
        UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id=None,
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_status="active",
            cancel_at_period_end=False,
        )

        with patch(f"{MODULE_PATH}.map_stripe_subscription_status") as map_mock:
            map_mock.return_value = UserSubscriptionStatus.ACTIVE.value

            result = sync_user_subscription_from_checkout(subscription_sync)

        map_mock.assert_called_once_with("active", False)
        self.assertEqual(result.status, UserSubscriptionStatus.ACTIVE.value)

    def test_saves_the_full_subscription_snapshot(self):
        UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
        )

        with patch.object(UserSubscription, "save", autospec=True) as mock_save:
            mock_save.side_effect = lambda instance, **kwargs: None
            result = sync_user_subscription_from_checkout(subscription_sync)

        mock_save.assert_called_once_with(
            result,
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

    def test_does_not_update_other_user_subscription(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
        )
        other_user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_456",
            stripe_subscription_id=None,
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
        )

        sync_user_subscription_from_checkout(subscription_sync)

        user_subscription.refresh_from_db()
        other_user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertIsNone(other_user_subscription.stripe_subscription_id)

    def test_locks_the_user_subscription_row(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
        )

        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_123",
        )

        with patch.object(
            UserSubscription.objects,
            "select_for_update",
        ) as select_for_update_mock:
            select_for_update_mock.return_value.get.return_value = user_subscription

            sync_user_subscription_from_checkout(subscription_sync)

        select_for_update_mock.assert_called_once_with()
        select_for_update_mock.return_value.get.assert_called_once_with(
            stripe_customer_id="cus_123",
        )

    def test_raises_error_when_user_subscription_does_not_exist_for_customer(self):
        subscription_sync = self.build_subscription_sync_dto(
            stripe_customer_id="cus_missing",
        )

        with self.assertRaises(UserSubscriptionNotFoundError):
            sync_user_subscription_from_checkout(subscription_sync)
