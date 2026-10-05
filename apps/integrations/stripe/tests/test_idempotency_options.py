from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.integrations.stripe.checkout import create_subscription_checkout_session
from apps.integrations.stripe.customers import create_customer


class CreateCustomerTests(SimpleTestCase):
    @patch("apps.integrations.stripe.customers.get_stripe_client")
    def test_forwards_the_idempotency_key_to_stripe(self, mock_get_stripe_client):
        client = MagicMock()
        mock_get_stripe_client.return_value = client

        create_customer(
            user_id=42,
            email="user@example.com",
            idempotency_key="chatea:customer:42",
        )

        params, kwargs = client.v1.customers.create.call_args

        self.assertEqual(
            kwargs["options"],
            {"idempotency_key": "chatea:customer:42"},
        )
        self.assertEqual(params[0]["email"], "user@example.com")
        self.assertEqual(params[0]["metadata"], {"user_id": "42"})


class CreateSubscriptionCheckoutSessionTests(SimpleTestCase):
    def call_create(self, mock_get_stripe_client, **overrides):
        client = MagicMock()
        mock_get_stripe_client.return_value = client

        kwargs = {
            "price_id": "price_123",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
            "user_id": 42,
            "user_email": "user@example.com",
        }
        kwargs.update(overrides)

        create_subscription_checkout_session(**kwargs)

        return client.v1.checkout.sessions.create.call_args

    @patch("apps.integrations.stripe.checkout.get_stripe_client")
    def test_forwards_the_idempotency_key_to_stripe(self, mock_get_stripe_client):
        _, kwargs = self.call_create(
            mock_get_stripe_client,
            idempotency_key="chatea:checkout-session:42:900",
        )

        self.assertEqual(
            kwargs["options"],
            {"idempotency_key": "chatea:checkout-session:42:900"},
        )

    @patch("apps.integrations.stripe.checkout.get_stripe_client")
    def test_sends_no_options_when_no_idempotency_key_is_given(
        self, mock_get_stripe_client
    ):
        _, kwargs = self.call_create(mock_get_stripe_client)

        self.assertIsNone(kwargs["options"])
