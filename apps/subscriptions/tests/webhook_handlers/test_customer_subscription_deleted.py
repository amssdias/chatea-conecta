from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.subscriptions.webhook_handlers.subscriptions import (
    handle_customer_subscription_deleted,
)

MODULE_PATH = "apps.subscriptions.webhook_handlers.subscriptions"


class TestHandleCustomerSubscriptionDeleted(TestCase):
    def setUp(self):
        self.subscription = SimpleNamespace(id="sub_old", customer="cus_123")

        self.deleted_subscription = SimpleNamespace(
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_old",
        )

        self.build_subscription_deleted_dto_mock = self._patch(
            f"{MODULE_PATH}.build_subscription_deleted_dto",
        )
        self.build_subscription_deleted_dto_mock.return_value = (
            self.deleted_subscription
        )

        self.mark_subscription_deleted_mock = self._patch(
            f"{MODULE_PATH}.mark_subscription_deleted",
        )

        self.send_subscription_canceled_email_task_mock = self._patch(
            f"{MODULE_PATH}.send_subscription_canceled_email_task",
        )

    def _patch(self, target):
        patcher = patch(target)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def test_sends_cancellation_email_for_the_current_subscription(self):
        user_subscription = SimpleNamespace(user_id=10, ended_at=timezone.now())
        self.mark_subscription_deleted_mock.return_value = user_subscription

        handle_customer_subscription_deleted(self.subscription)

        self.build_subscription_deleted_dto_mock.assert_called_once_with(
            self.subscription,
        )
        self.mark_subscription_deleted_mock.assert_called_once_with(
            self.deleted_subscription,
        )
        self.send_subscription_canceled_email_task_mock.delay.assert_called_once_with(
            user_id=user_subscription.user_id,
            ended_at=user_subscription.ended_at,
        )

    def test_does_not_send_cancellation_email_for_stale_subscription_event(self):
        self.mark_subscription_deleted_mock.return_value = None

        handle_customer_subscription_deleted(self.subscription)

        self.build_subscription_deleted_dto_mock.assert_called_once_with(
            self.subscription,
        )
        self.mark_subscription_deleted_mock.assert_called_once_with(
            self.deleted_subscription,
        )
        self.send_subscription_canceled_email_task_mock.delay.assert_not_called()

    def test_does_nothing_when_the_mapper_returns_nothing(self):
        self.build_subscription_deleted_dto_mock.return_value = None

        handle_customer_subscription_deleted(self.subscription)

        self.mark_subscription_deleted_mock.assert_not_called()
        self.send_subscription_canceled_email_task_mock.delay.assert_not_called()

    def test_propagates_mark_subscription_deleted_errors(self):
        self.mark_subscription_deleted_mock.side_effect = RuntimeError(
            "Could not mark subscription as deleted",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Could not mark subscription as deleted",
        ):
            handle_customer_subscription_deleted(self.subscription)

        self.send_subscription_canceled_email_task_mock.delay.assert_not_called()
