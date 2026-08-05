from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory


class UserSubscriptionProTests(TestCase):
    def build_subscription(self, **kwargs):
        return UserSubscriptionFactory.build(**kwargs)

    def test_active_subscription_with_a_future_period_end_is_pro(self):
        subscription = self.build_subscription(
            status=UserSubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=5),
        )

        self.assertTrue(subscription.pro)

    def test_active_subscription_with_a_past_period_end_is_not_pro(self):
        subscription = self.build_subscription(
            status=UserSubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() - timedelta(days=1),
        )

        self.assertFalse(subscription.pro)

    def test_active_subscription_without_a_period_end_is_not_pro(self):
        """
        A missing period end means the billing period could not be read from Stripe.
        Granting Pro would turn that failure into an unlimited entitlement.
        """
        subscription = self.build_subscription(
            status=UserSubscriptionStatus.ACTIVE,
            current_period_end=None,
        )

        self.assertFalse(subscription.pro)

    def test_past_due_subscription_with_a_future_period_end_is_pro(self):
        subscription = self.build_subscription(
            status=UserSubscriptionStatus.PAST_DUE,
            current_period_end=timezone.now() + timedelta(days=5),
        )

        self.assertTrue(subscription.pro)

    def test_past_due_subscription_without_a_period_end_is_not_pro(self):
        subscription = self.build_subscription(
            status=UserSubscriptionStatus.PAST_DUE,
            current_period_end=None,
        )

        self.assertFalse(subscription.pro)

    def test_non_paying_statuses_are_never_pro(self):
        for status in (
            UserSubscriptionStatus.INACTIVE,
            UserSubscriptionStatus.CANCELED,
            UserSubscriptionStatus.EXPIRED,
        ):
            with self.subTest(status=status):
                subscription = self.build_subscription(
                    status=status,
                    current_period_end=timezone.now() + timedelta(days=30),
                )

                self.assertFalse(subscription.pro)
