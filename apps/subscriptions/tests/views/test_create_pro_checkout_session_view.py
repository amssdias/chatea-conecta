from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.subscriptions.services.exceptions import (
    CheckoutConfigurationError,
    CheckoutProviderError,
    SubscriptionAlreadyActiveError,
)
from apps.users.tests.factories import UserFactory

VIEW_MODULE_PATH = "apps.subscriptions.views.checkout"


class CreateProCheckoutSessionViewTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("subscriptions:create_pro_checkout_session")

        self.patcher = patch(f"{VIEW_MODULE_PATH}.create_pro_checkout_session")
        self.mock_create_pro_checkout_session = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def get_messages(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_redirects_to_stripe_on_success(self):
        self.mock_create_pro_checkout_session.return_value = SimpleNamespace(
            url="https://checkout.stripe.com/c/pay/cs_123",
        )

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.stripe.com/c/pay/cs_123")

    def test_provider_error_redirects_with_a_message_instead_of_500(self):
        self.mock_create_pro_checkout_session.side_effect = CheckoutProviderError

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("subscriptions:detail"))
        self.assertIn(
            "We could not start the PRO checkout right now. Please try again later.",
            self.get_messages(response),
        )

    def test_configuration_error_redirects_with_a_message_instead_of_500(self):
        self.mock_create_pro_checkout_session.side_effect = CheckoutConfigurationError

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("subscriptions:detail"))
        self.assertIn(
            "We could not start the PRO checkout right now. Please try again later.",
            self.get_messages(response),
        )

    def test_already_active_redirects_with_an_informational_message(self):
        self.mock_create_pro_checkout_session.side_effect = SubscriptionAlreadyActiveError

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("subscriptions:detail"))
        self.assertIn(
            "You already have an active PRO subscription.",
            self.get_messages(response),
        )
