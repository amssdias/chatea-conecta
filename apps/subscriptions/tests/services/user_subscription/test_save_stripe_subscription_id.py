from django.test import TestCase

from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
from apps.subscriptions.services.user_subscription import save_stripe_subscription_id
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory


class SaveStripeSubscriptionIdTests(TestCase):
    def test_updates_stripe_subscription_id_for_matching_customer(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
        )

        self.assertIsNone(user_subscription.stripe_subscription_id)

        save_stripe_subscription_id(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.stripe_subscription_id, "sub_123")

    def test_does_not_update_other_user_subscription(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
        )
        other_user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_456",
        )

        save_stripe_subscription_id(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )

        user_subscription.refresh_from_db()
        other_user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.stripe_subscription_id, "sub_123")
        self.assertIsNone(other_user_subscription.stripe_subscription_id)

    def test_raises_error_when_user_subscription_does_not_exist_for_customer(self):
        with self.assertRaises(UserSubscriptionNotFoundError):
            save_stripe_subscription_id(
                stripe_customer_id="cus_missing",
                stripe_subscription_id="sub_123",
            )
