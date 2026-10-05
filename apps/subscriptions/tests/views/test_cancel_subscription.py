from unittest.mock import patch

from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.subscriptions.services.exceptions import (
    SubscriptionAlreadyCancellingError,
    SubscriptionCancellationProviderError,
    SubscriptionCannotBeCancelledError,
    SubscriptionMissingStripeIdError,
    UserSubscriptionNotFoundError,
)
from apps.users.tests.factories import UserFactory

MODULE_PATH = "apps.subscriptions.views.cancel"


class CancelSubscriptionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def setUp(self):
        self.url = reverse("subscriptions:cancel")
        self.detail_url = reverse("subscriptions:detail")

        self.client.force_login(self.user)

        self.cancel_user_subscription_patcher = patch(
            f"{MODULE_PATH}.cancel_user_subscription"
        )
        self.mock_cancel_user_subscription = (
            self.cancel_user_subscription_patcher.start()
        )

        self.addCleanup(self.cancel_user_subscription_patcher.stop)

    def get_response_messages(self, response):
        return [message.message for message in get_messages(response.wsgi_request)]

    def test_post_calls_cancel_user_subscription_and_redirects_to_detail(self):
        response = self.client.post(self.url)

        self.assertRedirects(response, self.detail_url)
        self.mock_cancel_user_subscription.assert_called_once_with(self.user)

    def test_post_shows_success_message_when_subscription_is_cancelled(self):
        response = self.client.post(self.url)

        messages = self.get_response_messages(response)

        self.assertIn(
            "Your subscription has been scheduled for cancellation. "
            "You can keep using PRO until the end of your current billing period.",
            messages,
        )

    def test_post_shows_error_message_when_user_subscription_does_not_exist(self):
        self.mock_cancel_user_subscription.side_effect = UserSubscriptionNotFoundError

        response = self.client.post(self.url)

        messages = self.get_response_messages(response)

        self.assertRedirects(response, self.detail_url)
        self.assertIn(
            "You do not have a subscription to cancel.",
            messages,
        )

    def test_post_shows_error_message_when_subscription_has_no_stripe_id(self):
        self.mock_cancel_user_subscription.side_effect = (
            SubscriptionMissingStripeIdError
        )

        response = self.client.post(self.url)

        messages = self.get_response_messages(response)

        self.assertRedirects(response, self.detail_url)
        self.assertIn(
            "Your subscription could not be found.",
            messages,
        )

    def test_post_shows_info_message_when_subscription_is_already_cancelling(self):
        self.mock_cancel_user_subscription.side_effect = (
            SubscriptionAlreadyCancellingError
        )

        response = self.client.post(self.url)

        messages = self.get_response_messages(response)

        self.assertRedirects(response, self.detail_url)
        self.assertIn(
            "Your subscription is already scheduled for cancellation.",
            messages,
        )

    def test_post_shows_error_message_when_subscription_cannot_be_cancelled(self):
        self.mock_cancel_user_subscription.side_effect = (
            SubscriptionCannotBeCancelledError
        )

        response = self.client.post(self.url)

        messages = self.get_response_messages(response)

        self.assertRedirects(response, self.detail_url)
        self.assertIn(
            "Only active subscriptions can be cancelled.",
            messages,
        )

    def test_post_shows_error_message_when_provider_cancellation_fails(self):
        self.mock_cancel_user_subscription.side_effect = (
            SubscriptionCancellationProviderError
        )

        response = self.client.post(self.url)

        messages = self.get_response_messages(response)

        self.assertRedirects(response, self.detail_url)
        self.assertIn(
            "We could not cancel your subscription right now. Please try again later.",
            messages,
        )

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.mock_cancel_user_subscription.assert_not_called()

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.LOGIN_URL), response.url)
        self.mock_cancel_user_subscription.assert_not_called()
