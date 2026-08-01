from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.subscriptions.webhook_handlers.subscriptions import (
    handle_customer_subscription_updated,
)

MODULE_PATH = "apps.subscriptions.webhook_handlers.subscriptions"


class TestHandleCustomerSubscriptionUpdated(TestCase):
    def setUp(self):
        self.subscription = SimpleNamespace(id="sub_new", customer="cus_123")

        self.subscription_sync = SimpleNamespace(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
        )

        self.build_subscription_sync_dto_mock = self._patch(
            f"{MODULE_PATH}.build_subscription_sync_dto",
        )
        self.build_subscription_sync_dto_mock.return_value = self.subscription_sync

        self.sync_user_subscription_from_stripe_mock = self._patch(
            f"{MODULE_PATH}.sync_user_subscription_from_stripe",
        )

    def _patch(self, target):
        patcher = patch(target)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_syncs_the_user_subscription_from_the_event(self):
        self.sync_user_subscription_from_stripe_mock.return_value = SimpleNamespace(
            user_id=10,
        )

        handle_customer_subscription_updated(self.subscription)

        self.build_subscription_sync_dto_mock.assert_called_once_with(self.subscription)
        self.sync_user_subscription_from_stripe_mock.assert_called_once_with(
            self.subscription_sync,
        )

    def test_returns_normally_for_stale_subscription_event(self):
        self.sync_user_subscription_from_stripe_mock.return_value = None

        handle_customer_subscription_updated(self.subscription)

        self.build_subscription_sync_dto_mock.assert_called_once_with(self.subscription)
        self.sync_user_subscription_from_stripe_mock.assert_called_once_with(
            self.subscription_sync,
        )

    def test_does_not_sync_when_the_mapper_returns_nothing(self):
        self.build_subscription_sync_dto_mock.return_value = None

        handle_customer_subscription_updated(self.subscription)

        self.sync_user_subscription_from_stripe_mock.assert_not_called()

    def test_propagates_sync_errors(self):
        self.sync_user_subscription_from_stripe_mock.side_effect = RuntimeError(
            "Could not sync user subscription",
        )

        with self.assertRaisesRegex(RuntimeError, "Could not sync user subscription"):
            handle_customer_subscription_updated(self.subscription)
