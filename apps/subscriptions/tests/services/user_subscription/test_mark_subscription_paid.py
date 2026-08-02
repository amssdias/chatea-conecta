from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.services.exceptions import UserSubscriptionNotFoundError
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

    def test_marks_subscription_as_paid(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.INACTIVE,
            started_at=None,
            current_period_end=None,
            cancel_at_period_end=True,
            canceled_at=timezone.now(),
            ended_at=timezone.now(),
        )

        started_at = timezone.now() - timedelta(days=1)
        current_period_start = timezone.now()
        current_period_end = timezone.now() + timedelta(days=30)

        paid_subscription = self.build_paid_subscription_dto(
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

        with patch.object(UserSubscription, "save", autospec=True) as mock_save:
            mock_save.side_effect = lambda instance, **kwargs: None
            result = mark_subscription_paid(paid_subscription)

        self.assertEqual(result.pk, user_subscription.pk)
        self.assertEqual(result.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(result.stripe_subscription_id, "sub_123")
        self.assertEqual(result.started_at, started_at)
        self.assertEqual(result.current_period_start, current_period_start)
        self.assertEqual(result.current_period_end, current_period_end)
        self.assertFalse(result.cancel_at_period_end)
        self.assertIsNone(result.canceled_at)
        self.assertIsNone(result.ended_at)

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

    def test_persists_paid_state(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.INACTIVE,
        )

        current_period_end = timezone.now() + timedelta(days=30)

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            current_period_end=current_period_end,
        )

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(user_subscription.current_period_end, current_period_end)

    def test_maps_status_from_stripe_instead_of_always_activating(self):
        """
        The subscription is re-read from Stripe when the invoice event is handled,
        so it may no longer be active by then. The local status must follow the
        retrieved Stripe status rather than being forced to ACTIVE.
        """
        cases = [
            ("active", UserSubscriptionStatus.ACTIVE),
            ("trialing", UserSubscriptionStatus.ACTIVE),
            ("past_due", UserSubscriptionStatus.PAST_DUE),
            ("canceled", UserSubscriptionStatus.CANCELED),
            ("unpaid", UserSubscriptionStatus.CANCELED),
            ("incomplete_expired", UserSubscriptionStatus.CANCELED),
            ("incomplete", UserSubscriptionStatus.INACTIVE),
            ("paused", UserSubscriptionStatus.INACTIVE),
        ]

        for index, (stripe_status, expected_status) in enumerate(cases):
            with self.subTest(stripe_status=stripe_status):
                stripe_customer_id = f"cus_{stripe_status}_{index}"
                stripe_subscription_id = f"sub_{stripe_status}_{index}"

                user_subscription = UserSubscriptionFactory(
                    stripe_customer_id=stripe_customer_id,
                    stripe_subscription_id=stripe_subscription_id,
                    status=UserSubscriptionStatus.INACTIVE,
                )

                paid_subscription = self.build_paid_subscription_dto(
                    stripe_customer_id=stripe_customer_id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_status=stripe_status,
                )

                mark_subscription_paid(paid_subscription)

                user_subscription.refresh_from_db()

                self.assertEqual(user_subscription.status, expected_status)

    def test_does_not_activate_a_subscription_canceled_before_the_event_is_processed(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.CANCELED,
        )

        canceled_at = timezone.now()

        paid_subscription = self.build_paid_subscription_dto(
            stripe_status="canceled",
            cancel_at_period_end=True,
            canceled_at=canceled_at,
            ended_at=canceled_at,
        )

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.status, UserSubscriptionStatus.CANCELED)
        self.assertEqual(user_subscription.canceled_at, canceled_at)
        self.assertEqual(user_subscription.ended_at, canceled_at)

    def test_keeps_existing_started_at_when_subscription_id_did_not_change(self):
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

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, existing_started_at)

    def test_sets_started_at_when_missing_even_if_subscription_id_did_not_change(self):
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

        mark_subscription_paid(paid_subscription)

        user_subscription.refresh_from_db()

        self.assertEqual(user_subscription.started_at, started_at)

    def test_ignores_event_for_non_current_subscription(self):
        original_started_at = timezone.now() - timedelta(days=90)
        original_period_start = timezone.now() - timedelta(days=5)
        original_period_end = timezone.now() + timedelta(days=25)
        original_canceled_at = None
        original_ended_at = None

        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
            status=UserSubscriptionStatus.ACTIVE,
            started_at=original_started_at,
            current_period_start=original_period_start,
            current_period_end=original_period_end,
            cancel_at_period_end=False,
            canceled_at=original_canceled_at,
            ended_at=original_ended_at,
        )

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
            stripe_status="past_due",
            started_at=timezone.now() - timedelta(days=365),
            current_period_start=timezone.now() - timedelta(days=180),
            current_period_end=timezone.now() - timedelta(days=150),
            cancel_at_period_end=True,
            canceled_at=timezone.now() - timedelta(days=150),
            ended_at=timezone.now() - timedelta(days=150),
        )

        result = mark_subscription_paid(paid_subscription)
        user_subscription.refresh_from_db()

        self.assertIsNone(result)
        self.assertEqual(user_subscription.stripe_subscription_id, "sub_new")
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.ACTIVE)
        self.assertEqual(user_subscription.started_at, original_started_at)
        self.assertEqual(user_subscription.current_period_start, original_period_start)
        self.assertEqual(user_subscription.current_period_end, original_period_end)
        self.assertFalse(user_subscription.cancel_at_period_end)
        self.assertEqual(user_subscription.canceled_at, original_canceled_at)
        self.assertEqual(user_subscription.ended_at, original_ended_at)

    def test_ignores_event_when_no_subscription_is_current_yet(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id=None,
            status=UserSubscriptionStatus.INACTIVE,
        )

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )

        result = mark_subscription_paid(paid_subscription)
        user_subscription.refresh_from_db()

        self.assertIsNone(result)
        self.assertIsNone(user_subscription.stripe_subscription_id)
        self.assertEqual(user_subscription.status, UserSubscriptionStatus.INACTIVE)

    def test_locks_the_user_subscription_row(self):
        user_subscription = UserSubscriptionFactory(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            status=UserSubscriptionStatus.INACTIVE,
        )

        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
        )

        with patch.object(
            UserSubscription.objects,
            "select_for_update",
        ) as select_for_update_mock:
            select_for_update_mock.return_value.get.return_value = user_subscription

            mark_subscription_paid(paid_subscription)

        select_for_update_mock.assert_called_once_with()
        select_for_update_mock.return_value.get.assert_called_once_with(
            stripe_customer_id="cus_123",
        )

    def test_raises_error_when_user_subscription_does_not_exist(self):
        paid_subscription = self.build_paid_subscription_dto(
            stripe_customer_id="cus_missing",
        )

        with self.assertRaises(UserSubscriptionNotFoundError):
            mark_subscription_paid(paid_subscription)
