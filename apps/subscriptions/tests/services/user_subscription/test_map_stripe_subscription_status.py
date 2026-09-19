from django.test import SimpleTestCase

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.user_subscription import map_stripe_subscription_status


class MapStripeSubscriptionStatusTests(SimpleTestCase):
    def test_maps_active_to_active(self):
        result = map_stripe_subscription_status(
            stripe_status="active",
            cancel_at_period_end=False,
        )

        self.assertEqual(result, UserSubscriptionStatus.ACTIVE)

    def test_maps_trialing_to_active(self):
        result = map_stripe_subscription_status(
            stripe_status="trialing",
            cancel_at_period_end=False,
        )

        self.assertEqual(result, UserSubscriptionStatus.ACTIVE)

    def test_maps_past_due_to_past_due(self):
        result = map_stripe_subscription_status(
            stripe_status="past_due",
            cancel_at_period_end=False,
        )

        self.assertEqual(result, UserSubscriptionStatus.PAST_DUE)

    def test_maps_canceled_statuses_to_canceled(self):
        stripe_statuses = [
            "canceled",
            "unpaid",
            "incomplete_expired",
        ]

        for stripe_status in stripe_statuses:
            with self.subTest(stripe_status=stripe_status):
                result = map_stripe_subscription_status(
                    stripe_status=stripe_status,
                    cancel_at_period_end=False,
                )

                self.assertEqual(result, UserSubscriptionStatus.CANCELED)

    def test_maps_inactive_statuses_to_inactive(self):
        stripe_statuses = [
            "incomplete",
            "paused",
        ]

        for stripe_status in stripe_statuses:
            with self.subTest(stripe_status=stripe_status):
                result = map_stripe_subscription_status(
                    stripe_status=stripe_status,
                    cancel_at_period_end=False,
                )

                self.assertEqual(result, UserSubscriptionStatus.INACTIVE)

    def test_maps_unknown_status_to_inactive(self):
        result = map_stripe_subscription_status(
            stripe_status="unknown_status",
            cancel_at_period_end=False,
        )

        self.assertEqual(result, UserSubscriptionStatus.INACTIVE)
