from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
from apps.subscriptions.services.user_subscription import mark_subscription_deleted
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class MarkSubscriptionDeletedTests(TestCase):

    def build_deleted_subscription_dto(
        self,
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
        current_period_start=None,
        current_period_end=None,
        cancel_at_period_end=False,
        canceled_at=None,
        ended_at=None,
    ):
        return SimpleNamespace(
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

    def test_marks_subscription_as_deleted(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
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
            stripe_subscription_id="sub_123",
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            cancel_at_period_end=True,
            canceled_at=canceled_at,
            ended_at=ended_at,
        )

        with patch.object(UserSubscription, "save", autospec=True) as mock_save:
            mock_save.side_effect = lambda instance, **kwargs: None
            result = mark_subscription_deleted(deleted_subscription)

        self.assertEqual(result.pk, user_subscription.pk)
        self.assertEqual(result.status, UserSubscriptionStatus.CANCELED)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertTrue(result.cancel_at_period_end)
        self.assertEqual(result.canceled_at, canceled_at)
        self.assertEqual(result.ended_at, ended_at)

        mock_save.assert_called_once_with(
            result,
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

    def test_persists_canceled_state(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
        )

        ended_at = timezone.now()

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            ended_at=ended_at,
        )

        mark_subscription_deleted(deleted_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.status, UserSubscriptionStatus.CANCELED)
        self.assertEqual(user_subscription.ended_at, ended_at)

    def test_uses_canceled_at_as_ended_at_when_ended_at_is_missing(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
            ended_at=None,
        )

        canceled_at = timezone.now()

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            canceled_at=canceled_at,
            ended_at=None,
        )

        mark_subscription_deleted(deleted_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.ended_at, canceled_at)

    def test_returns_updated_user_subscription(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
        )

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            ended_at=timezone.now(),
        )

        result = mark_subscription_deleted(deleted_subscription)

        self.assertEqual(result.pk, user_subscription.pk)

    def test_ignores_event_for_non_current_subscription(self):
        original_period_start = timezone.now() - timedelta(days=5)
        original_period_end = timezone.now() + timedelta(days=25)

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
            status=UserSubscriptionStatus.ACTIVE,
            current_period_start=original_period_start,
            current_period_end=original_period_end,
            cancel_at_period_end=False,
            canceled_at=None,
            ended_at=None,
        )

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            current_period_start=timezone.now() - timedelta(days=180),
            current_period_end=timezone.now() - timedelta(days=150),
            cancel_at_period_end=True,
            canceled_at=timezone.now() - timedelta(days=150),
            ended_at=timezone.now() - timedelta(days=150),
        )

        result = mark_subscription_deleted(deleted_subscription)

        user_subscription.refresh_from_db()

        self.assertIsNone(result)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(user_subscription.current_period_start, original_period_start)
        self.assertEqual(user_subscription.current_period_end, original_period_end)
        self.assertFalse(user_subscription.cancel_at_period_end)
        self.assertIsNone(user_subscription.canceled_at)
        self.assertIsNone(user_subscription.ended_at)

    def test_locks_the_user_subscription_row(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.ACTIVE,
        )

        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            ended_at=timezone.now(),
        )

        with patch.object(
            UserSubscription.objects,
            "select_for_update",
        ) as select_for_update_mock:
            select_for_update_mock.return_value.get.return_value = user_subscription

            mark_subscription_deleted(deleted_subscription)

        select_for_update_mock.assert_called_once_with()
        select_for_update_mock.return_value.get.assert_called_once_with(
            stripe_customer_id="cus_123",
        )

    def test_raises_error_when_user_subscription_does_not_exist(self):
        deleted_subscription = self.build_deleted_subscription_dto(
            stripe_customer_id="cus_missing",
        )

        with self.assertRaises(UserSubscriptionNotFoundError):
            mark_subscription_deleted(deleted_subscription)
