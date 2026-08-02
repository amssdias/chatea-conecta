from datetime import datetime, timedelta, timezone as dt_timezone
from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import (
    SubscriptionAlreadyCancellingError,
    SubscriptionCancellationProviderError,
    SubscriptionCannotBeCancelledError,
    SubscriptionMissingStripeIdError,
    UserSubscriptionNotFoundError,
)
from apps.subscriptions.services.user_subscription import cancel_user_subscription
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory
from apps.users.tests.factories import UserFactory

MODULE_PATH = "apps.subscriptions.services.user_subscription"


class CancelUserSubscriptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def setUp(self):
        self.get_user_subscription_patcher = patch(
            f"{MODULE_PATH}.get_user_subscription"
        )
        self.schedule_cancellation_patcher = patch(
            f"{MODULE_PATH}.schedule_stripe_subscription_cancellation"
        )

        self.mock_get_user_subscription = self.get_user_subscription_patcher.start()
        self.mock_schedule_stripe_subscription_cancellation = (
            self.schedule_cancellation_patcher.start()
        )

        self.addCleanup(self.get_user_subscription_patcher.stop)
        self.addCleanup(self.schedule_cancellation_patcher.stop)

    def create_user_subscription(self, **kwargs):
        defaults = {
            "user": self.user,
            "status": UserSubscriptionStatus.ACTIVE,
            "stripe_subscription_id": "sub_123",
            "cancel_at_period_end": False,
        }
        defaults.update(kwargs)

        return UserSubscriptionFactory(**defaults)

    def build_stripe_subscription(self, current_period_end=None, price_id=None):
        """
        Build a subscription with the Clover API shape, where the billing period
        lives on the subscription items rather than on the subscription itself.
        """
        items = []

        if current_period_end is not None:
            items.append(
                SimpleNamespace(
                    price=SimpleNamespace(
                        id=price_id or settings.STRIPE_PRO_MONTHLY_PRICE_ID,
                    ),
                    current_period_end=current_period_end,
                ),
            )

        return SimpleNamespace(
            items=SimpleNamespace(data=items),
        )

    def test_schedules_active_subscription_for_cancellation(self):
        user_subscription = self.create_user_subscription()

        current_period_end_timestamp = int(
            (timezone.now() + timedelta(days=10)).timestamp()
        )

        self.mock_get_user_subscription.return_value = user_subscription
        self.mock_schedule_stripe_subscription_cancellation.return_value = (
            self.build_stripe_subscription(
                current_period_end=current_period_end_timestamp,
            )
        )

        with patch.object(
                user_subscription, "save", wraps=user_subscription.save
        ) as mock_save:
            result = cancel_user_subscription(self.user)

        user_subscription.refresh_from_db()

        expected_current_period_end = datetime.fromtimestamp(
            current_period_end_timestamp,
            tz=dt_timezone.utc,
        )

        self.assertEqual(result, user_subscription)
        self.assertTrue(user_subscription.cancel_at_period_end)
        self.assertEqual(
            user_subscription.current_period_end, expected_current_period_end
        )

        self.mock_get_user_subscription.assert_called_once_with(self.user)
        self.mock_schedule_stripe_subscription_cancellation.assert_called_once_with(
            "sub_123"
        )
        mock_save.assert_called_once_with(
            update_fields=[
                "cancel_at_period_end",
                "current_period_end",
                "updated_at",
            ],
        )

    def test_schedules_past_due_subscription_for_cancellation(self):
        user_subscription = self.create_user_subscription(
            status=UserSubscriptionStatus.PAST_DUE,
        )

        self.mock_get_user_subscription.return_value = user_subscription
        self.mock_schedule_stripe_subscription_cancellation.return_value = (
            self.build_stripe_subscription()
        )

        result = cancel_user_subscription(self.user)

        user_subscription.refresh_from_db()

        self.assertEqual(result, user_subscription)
        self.assertTrue(user_subscription.cancel_at_period_end)
        self.mock_schedule_stripe_subscription_cancellation.assert_called_once_with(
            "sub_123"
        )

    def test_keeps_existing_current_period_end_when_stripe_response_has_no_current_period_end(
            self,
    ):
        current_period_end = timezone.now() + timedelta(days=20)

        user_subscription = self.create_user_subscription(
            current_period_end=current_period_end,
        )

        self.mock_get_user_subscription.return_value = user_subscription
        self.mock_schedule_stripe_subscription_cancellation.return_value = (
            self.build_stripe_subscription()
        )

        cancel_user_subscription(self.user)

        user_subscription.refresh_from_db()

        self.assertTrue(user_subscription.cancel_at_period_end)
        self.assertEqual(user_subscription.current_period_end, current_period_end)

    def test_keeps_existing_current_period_end_when_no_item_matches_the_pro_price(self):
        current_period_end = timezone.now() + timedelta(days=20)

        user_subscription = self.create_user_subscription(
            current_period_end=current_period_end,
        )

        self.mock_get_user_subscription.return_value = user_subscription
        self.mock_schedule_stripe_subscription_cancellation.return_value = (
            self.build_stripe_subscription(
                current_period_end=int((timezone.now() + timedelta(days=10)).timestamp()),
                price_id="price_other",
            )
        )

        cancel_user_subscription(self.user)

        user_subscription.refresh_from_db()

        self.assertTrue(user_subscription.cancel_at_period_end)
        self.assertEqual(user_subscription.current_period_end, current_period_end)

    def test_ignores_top_level_current_period_end_on_the_subscription(self):
        """
        The pinned Clover API does not return a top-level current_period_end.
        Reading one would mean reading a field the API no longer populates.
        """
        current_period_end = timezone.now() + timedelta(days=20)

        user_subscription = self.create_user_subscription(
            current_period_end=current_period_end,
        )

        stripe_subscription = self.build_stripe_subscription()
        stripe_subscription.current_period_end = int(
            (timezone.now() + timedelta(days=10)).timestamp()
        )

        self.mock_get_user_subscription.return_value = user_subscription
        self.mock_schedule_stripe_subscription_cancellation.return_value = (
            stripe_subscription
        )

        cancel_user_subscription(self.user)

        user_subscription.refresh_from_db()

        self.assertTrue(user_subscription.cancel_at_period_end)
        self.assertEqual(user_subscription.current_period_end, current_period_end)

    def test_raises_error_when_user_subscription_does_not_exist(self):
        self.mock_get_user_subscription.side_effect = UserSubscriptionNotFoundError

        with self.assertRaises(UserSubscriptionNotFoundError):
            cancel_user_subscription(self.user)

        self.mock_get_user_subscription.assert_called_once_with(self.user)
        self.mock_schedule_stripe_subscription_cancellation.assert_not_called()

    def test_raises_error_when_subscription_has_no_stripe_subscription_id(self):
        user_subscription = self.create_user_subscription(
            stripe_subscription_id=None,
        )

        self.mock_get_user_subscription.return_value = user_subscription

        with self.assertRaises(SubscriptionMissingStripeIdError):
            cancel_user_subscription(self.user)

        self.mock_schedule_stripe_subscription_cancellation.assert_not_called()

    def test_raises_error_when_subscription_is_already_scheduled_for_cancellation(self):
        user_subscription = self.create_user_subscription(
            cancel_at_period_end=True,
        )

        self.mock_get_user_subscription.return_value = user_subscription

        with self.assertRaises(SubscriptionAlreadyCancellingError):
            cancel_user_subscription(self.user)

        self.mock_schedule_stripe_subscription_cancellation.assert_not_called()

    def test_raises_error_when_subscription_status_cannot_be_cancelled(self):
        user_subscription = self.create_user_subscription(
            status=UserSubscriptionStatus.INACTIVE,
        )

        self.mock_get_user_subscription.return_value = user_subscription

        with self.assertRaises(SubscriptionCannotBeCancelledError):
            cancel_user_subscription(self.user)

        self.mock_schedule_stripe_subscription_cancellation.assert_not_called()

    @patch(f"{MODULE_PATH}.logger.exception")
    def test_raises_provider_error_when_stripe_cancellation_fails(self, mock_logger_exception):
        user_subscription = self.create_user_subscription()

        self.mock_get_user_subscription.return_value = user_subscription
        self.mock_schedule_stripe_subscription_cancellation.side_effect = stripe.StripeError(
            "Stripe failed",
        )

        with self.assertRaises(SubscriptionCancellationProviderError):
            cancel_user_subscription(self.user)

        user_subscription.refresh_from_db()

        self.assertFalse(user_subscription.cancel_at_period_end)
        self.mock_schedule_stripe_subscription_cancellation.assert_called_once_with(
            "sub_123"
        )

        mock_logger_exception.assert_called_once_with(
            "Stripe subscription cancellation failed. user_id=%s subscription_id=%s",
            self.user.id,
            "sub_123",
        )
