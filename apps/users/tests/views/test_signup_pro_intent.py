from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.subscriptions.services.exceptions import (
    CheckoutConfigurationError,
    CheckoutProviderError,
)
from apps.users.constants import SignupIntent

User = get_user_model()

VIEW_MODULE_PATH = "apps.users.views.signup"


@patch(f"{VIEW_MODULE_PATH}.register_user_on_redis")
class SignUpProIntentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users:signup")

    def setUp(self):
        self.patcher = patch(f"{VIEW_MODULE_PATH}.create_pro_checkout_session")
        self.mock_create_pro_checkout_session = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def signup_payload(self, **overrides):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "sup3r-s3cret-pass",
            "password2": "sup3r-s3cret-pass",
            "intent": SignupIntent.PRO,
        }
        payload.update(overrides)

        return payload

    def get_messages(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_redirects_to_stripe_when_checkout_starts(self, mock_register):
        self.mock_create_pro_checkout_session.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/c/pay/cs_123",
        )

        response = self.client.post(self.url, self.signup_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.stripe.com/c/pay/cs_123")

    @patch(f"{VIEW_MODULE_PATH}.logger")
    def test_keeps_the_account_and_redirects_when_checkout_fails(self, mock_logger, mock_register):
        self.mock_create_pro_checkout_session.side_effect = CheckoutProviderError

        response = self.client.post(self.url, self.signup_payload())

        self.assertRedirects(response, reverse("subscriptions:detail"))

        user = User.objects.get(username="newuser")

        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(user.pk),
        )

    @patch(f"{VIEW_MODULE_PATH}.logger")
    def test_tells_the_user_the_account_exists_when_checkout_fails(self, mock_logger, mock_register):
        self.mock_create_pro_checkout_session.side_effect = CheckoutConfigurationError

        response = self.client.post(self.url, self.signup_payload())

        self.assertIn(
            "Your account was created, but we could not start the PRO checkout. "
            "You are signed in and can try upgrading again below.",
            self.get_messages(response),
        )

    @patch(f"{VIEW_MODULE_PATH}.logger.exception")
    def test_logs_the_failure_so_it_is_still_visible_to_operators(
        self, mock_logger_exception, mock_register
    ):
        self.mock_create_pro_checkout_session.side_effect = CheckoutProviderError

        self.client.post(self.url, self.signup_payload())

        user = User.objects.get(username="newuser")

        mock_logger_exception.assert_called_once_with(
            "Could not start PRO checkout after signup. user_id=%s",
            user.id,
        )

    @patch(f"{VIEW_MODULE_PATH}.logger")
    def test_session_cookies_are_still_set_when_checkout_fails(self, mock_logger, mock_register):
        self.mock_create_pro_checkout_session.side_effect = CheckoutProviderError

        response = self.client.post(self.url, self.signup_payload())

        self.assertEqual(response.cookies["username"].value, "newuser")
        self.assertIn("user_id", response.cookies)

    @patch(f"{VIEW_MODULE_PATH}.logger")
    def test_signing_up_again_after_a_failed_checkout_is_not_needed(self, mock_logger, mock_register):
        """
        The account survives a checkout failure, so a second signup with the same
        username is rejected by uniqueness. The user must be able to retry checkout
        while signed in instead, which is what the redirect above provides.
        """
        self.mock_create_pro_checkout_session.side_effect = CheckoutProviderError

        self.client.post(self.url, self.signup_payload())
        self.client.logout()

        response = self.client.post(self.url, self.signup_payload())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists", status_code=200)
