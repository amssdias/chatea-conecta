from datetime import datetime, timedelta, timezone as dt_timezone
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from apps.integrations.stripe.subscriptions import (
    get_subscription_current_period_end,
    get_subscription_current_period_start,
)

PRO_PRICE_ID = "price_pro_monthly"

NOW = datetime(2026, 8, 3, tzinfo=dt_timezone.utc)


def build_item(price_id, period_start, period_end):
    return SimpleNamespace(
        price=SimpleNamespace(id=price_id),
        current_period_start=int(period_start.timestamp()),
        current_period_end=int(period_end.timestamp()),
    )


def build_subscription(*items):
    return SimpleNamespace(
        id="sub_123",
        items=SimpleNamespace(data=list(items)),
    )


@override_settings(STRIPE_PRO_MONTHLY_PRICE_ID=PRO_PRICE_ID)
class SubscriptionPeriodBoundaryTests(SimpleTestCase):
    def test_reads_the_period_from_the_pro_item(self):
        period_end = NOW + timedelta(days=30)

        subscription = build_subscription(
            build_item("price_other", NOW, NOW + timedelta(days=90)),
            build_item(PRO_PRICE_ID, NOW, period_end),
        )

        self.assertEqual(
            get_subscription_current_period_end(subscription),
            period_end,
        )
        self.assertEqual(
            get_subscription_current_period_start(subscription),
            NOW,
        )

    def test_falls_back_to_the_earliest_boundary_when_no_item_matches_the_pro_price(
        self,
    ):
        """
        A new Price, a legacy subscriber, or a misconfigured environment must not
        resolve to ``None``: downstream that reads as an unbounded entitlement.
        """
        earliest_end = NOW + timedelta(days=10)

        subscription = build_subscription(
            build_item("price_legacy", NOW + timedelta(days=1), NOW + timedelta(days=40)),
            build_item("price_addon", NOW, earliest_end),
        )

        with self.assertLogs("apps.integrations.stripe.subscriptions", "WARNING"):
            current_period_end = get_subscription_current_period_end(subscription)

        self.assertEqual(current_period_end, earliest_end)

    def test_falls_back_when_the_configured_pro_price_is_not_set(self):
        period_end = NOW + timedelta(days=30)

        subscription = build_subscription(build_item("price_legacy", NOW, period_end))

        with override_settings(STRIPE_PRO_MONTHLY_PRICE_ID=None):
            with self.assertLogs("apps.integrations.stripe.subscriptions", "WARNING"):
                current_period_end = get_subscription_current_period_end(subscription)

        self.assertEqual(current_period_end, period_end)

    def test_returns_none_when_the_subscription_has_no_items(self):
        subscription = build_subscription()

        self.assertIsNone(get_subscription_current_period_end(subscription))
        self.assertIsNone(get_subscription_current_period_start(subscription))

    def test_ignores_a_top_level_period_end_on_the_subscription(self):
        """
        The pinned Clover API does not populate a top-level current_period_end.
        """
        subscription = build_subscription()
        subscription.current_period_end = int((NOW + timedelta(days=30)).timestamp())

        self.assertIsNone(get_subscription_current_period_end(subscription))
