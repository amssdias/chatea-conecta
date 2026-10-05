from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from apps.subscriptions.webhook_handlers.checkout import (
    handle_checkout_session_completed,
)

MODULE_PATH = "apps.subscriptions.webhook_handlers.checkout"


class TestHandleCheckoutSessionCompleted(TestCase):
    def setUp(self):
        self.session = SimpleNamespace(
            id="cs_test_123",
            customer="cus_123",
            subscription="sub_new",
        )

        self.stripe_subscription = SimpleNamespace(id="sub_new")
        self.subscription_sync = SimpleNamespace(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_new",
        )

        self.retrieve_subscription_mock = self._patch(
            f"{MODULE_PATH}.retrieve_subscription",
        )
        self.retrieve_subscription_mock.return_value = self.stripe_subscription

        self.build_subscription_sync_dto_mock = self._patch(
            f"{MODULE_PATH}.build_subscription_sync_dto",
        )
        self.build_subscription_sync_dto_mock.return_value = self.subscription_sync

        self.sync_user_subscription_from_checkout_mock = self._patch(
            f"{MODULE_PATH}.sync_user_subscription_from_checkout",
        )

    def _patch(self, target):
        patcher = patch(target)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_retrieves_maps_and_establishes_the_current_subscription(self):
        handle_checkout_session_completed(self.session)

        self.retrieve_subscription_mock.assert_called_once_with("sub_new")
        self.build_subscription_sync_dto_mock.assert_called_once_with(
            self.stripe_subscription,
        )
        self.sync_user_subscription_from_checkout_mock.assert_called_once_with(
            self.subscription_sync,
        )

    def test_propagates_stripe_retrieval_errors(self):
        self.retrieve_subscription_mock.side_effect = RuntimeError(
            "Could not retrieve subscription",
        )

        with self.assertRaisesRegex(RuntimeError, "Could not retrieve subscription"):
            handle_checkout_session_completed(self.session)

        self.build_subscription_sync_dto_mock.assert_not_called()
        self.sync_user_subscription_from_checkout_mock.assert_not_called()

    def test_propagates_mapper_errors(self):
        self.build_subscription_sync_dto_mock.side_effect = RuntimeError(
            "Missing customer on Stripe subscription sync",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Missing customer on Stripe subscription sync",
        ):
            handle_checkout_session_completed(self.session)

        self.retrieve_subscription_mock.assert_called_once_with("sub_new")
        self.sync_user_subscription_from_checkout_mock.assert_not_called()
