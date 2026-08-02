from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, TestCase

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.create_pro_subscription import (
    CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS,
    build_checkout_session_idempotency_key,
    build_customer_idempotency_key,
    create_pro_checkout_session,
)
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory
from apps.users.tests.factories import UserFactory

MODULE_PATH = "apps.subscriptions.services.create_pro_subscription"


class CreateProCheckoutSessionTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.request = RequestFactory().post("/subscriptions/checkout/pro/")

        self.create_customer_patcher = patch(f"{MODULE_PATH}.create_customer")
        self.create_session_patcher = patch(
            f"{MODULE_PATH}.create_subscription_checkout_session"
        )

        self.mock_create_customer = self.create_customer_patcher.start()
        self.mock_create_session = self.create_session_patcher.start()

        self.mock_create_customer.return_value = SimpleNamespace(id="cus_new")
        self.mock_create_session.return_value = SimpleNamespace(
            id="cs_123",
            url="https://checkout.stripe.com/c/pay/cs_123",
        )

        self.addCleanup(self.create_customer_patcher.stop)
        self.addCleanup(self.create_session_patcher.stop)

    def test_creates_the_stripe_customer_with_a_stable_idempotency_key(self):
        create_pro_checkout_session(user=self.user, request=self.request)

        self.mock_create_customer.assert_called_once_with(
            user_id=self.user.id,
            email=self.user.email,
            idempotency_key=build_customer_idempotency_key(self.user.id),
        )

    def test_passes_an_idempotency_key_when_creating_the_checkout_session(self):
        create_pro_checkout_session(user=self.user, request=self.request)

        _, kwargs = self.mock_create_session.call_args

        self.assertEqual(
            kwargs["idempotency_key"],
            build_checkout_session_idempotency_key(self.user.id),
        )

    def test_repeated_requests_reuse_the_same_checkout_session_idempotency_key(self):
        create_pro_checkout_session(user=self.user, request=self.request)
        create_pro_checkout_session(user=self.user, request=self.request)

        first_call, second_call = self.mock_create_session.call_args_list

        self.assertEqual(
            first_call.kwargs["idempotency_key"],
            second_call.kwargs["idempotency_key"],
        )

    def test_creates_the_customer_only_once_across_repeated_requests(self):
        create_pro_checkout_session(user=self.user, request=self.request)
        create_pro_checkout_session(user=self.user, request=self.request)

        self.mock_create_customer.assert_called_once()

        user_subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(user_subscription.stripe_customer_id, "cus_new")

    def test_reuses_an_existing_stripe_customer(self):
        UserSubscriptionFactory(
            user=self.user,
            stripe_customer_id="cus_existing",
            status=UserSubscriptionStatus.INACTIVE,
        )

        create_pro_checkout_session(user=self.user, request=self.request)

        self.mock_create_customer.assert_not_called()

        _, kwargs = self.mock_create_session.call_args
        self.assertEqual(kwargs["stripe_customer_id"], "cus_existing")

    def test_keeps_the_customer_when_creating_the_checkout_session_fails(self):
        """
        The customer ID is committed before the Checkout Session call, so a failed
        session does not orphan a Stripe customer that no local row points at.
        """
        self.mock_create_session.side_effect = ValueError("Stripe is down")

        with self.assertRaises(ValueError):
            create_pro_checkout_session(user=self.user, request=self.request)

        user_subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(user_subscription.stripe_customer_id, "cus_new")

    def test_raises_when_the_user_already_has_an_active_subscription(self):
        UserSubscriptionFactory(
            user=self.user,
            status=UserSubscriptionStatus.ACTIVE,
            stripe_customer_id="cus_existing",
        )

        with self.assertRaises(ValueError):
            create_pro_checkout_session(user=self.user, request=self.request)

        self.mock_create_customer.assert_not_called()
        self.mock_create_session.assert_not_called()


class IdempotencyKeyTests(TestCase):
    def test_customer_key_is_stable_over_time(self):
        with patch(f"{MODULE_PATH}.timezone") as mock_timezone:
            mock_timezone.now.return_value.timestamp.return_value = 0
            first = build_customer_idempotency_key(7)

            mock_timezone.now.return_value.timestamp.return_value = 10_000_000
            second = build_customer_idempotency_key(7)

        self.assertEqual(first, second)

    def test_customer_key_differs_per_user(self):
        self.assertNotEqual(
            build_customer_idempotency_key(1),
            build_customer_idempotency_key(2),
        )

    def test_checkout_session_key_is_shared_inside_the_window(self):
        window_start = CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS * 100

        with patch(f"{MODULE_PATH}.timezone") as mock_timezone:
            mock_timezone.now.return_value.timestamp.return_value = window_start
            first = build_checkout_session_idempotency_key(7)

            mock_timezone.now.return_value.timestamp.return_value = (
                window_start + CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS - 1
            )
            second = build_checkout_session_idempotency_key(7)

        self.assertEqual(first, second)

    def test_checkout_session_key_changes_across_a_window_boundary(self):
        """
        Windows are fixed buckets, not a sliding window: two requests seconds apart
        but on opposite sides of a boundary get different keys, and Stripe will
        create two sessions. The database lock still prevents duplicate customers.
        """
        window_start = CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS * 100

        with patch(f"{MODULE_PATH}.timezone") as mock_timezone:
            mock_timezone.now.return_value.timestamp.return_value = window_start - 1
            first = build_checkout_session_idempotency_key(7)

            mock_timezone.now.return_value.timestamp.return_value = window_start
            second = build_checkout_session_idempotency_key(7)

        self.assertNotEqual(first, second)

    def test_checkout_session_key_changes_after_the_window(self):
        with patch(f"{MODULE_PATH}.timezone") as mock_timezone:
            mock_timezone.now.return_value.timestamp.return_value = 0
            first = build_checkout_session_idempotency_key(7)

            mock_timezone.now.return_value.timestamp.return_value = (
                CHECKOUT_SESSION_IDEMPOTENCY_WINDOW_SECONDS
            )
            second = build_checkout_session_idempotency_key(7)

        self.assertNotEqual(first, second)

    def test_checkout_session_key_differs_per_user(self):
        self.assertNotEqual(
            build_checkout_session_idempotency_key(1),
            build_checkout_session_idempotency_key(2),
        )
