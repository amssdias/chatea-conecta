from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.subscriptions.tests.factories.user_subscription import UserSubscriptionFactory
from apps.users.tests.factories import UserFactory

VIEW_MODULE_PATH = "apps.subscriptions.views.checkout"


def build_session(**overrides):
    session = {
        "id": "cs_123",
        "status": "complete",
        "payment_status": "paid",
        "client_reference_id": None,
        "customer": "cus_me",
        "customer_details": SimpleNamespace(email="me@example.com"),
        "amount_total": 999,
        "currency": "eur",
        "subscription": "sub_123",
    }
    session.update(overrides)

    return SimpleNamespace(**session)


class CheckoutSuccessViewTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        self.url = reverse("subscriptions:checkout_success")

        self.patcher = patch(f"{VIEW_MODULE_PATH}.retrieve_checkout_session")
        self.mock_retrieve = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def given_subscription(self, **kwargs):
        defaults = {
            "user": self.user,
            "stripe_customer_id": "cus_me",
            "status": UserSubscriptionStatus.INACTIVE,
        }
        defaults.update(kwargs)

        return UserSubscriptionFactory(**defaults)

    def get_success(self, session, session_id="cs_123"):
        self.mock_retrieve.return_value = session

        return self.client.get(self.url, {"session_id": session_id})

    # --- Payment state -----------------------------------------------------

    def test_paid_session_with_activated_subscription_is_active(self):
        self.given_subscription(
            status=UserSubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        response = self.get_success(build_session(client_reference_id=str(self.user.id)))

        self.assertEqual(response.context["status"], "active")

    def test_paid_session_awaiting_the_webhook_is_pending(self):
        self.given_subscription()

        response = self.get_success(build_session(client_reference_id=str(self.user.id)))

        self.assertEqual(response.context["status"], "pending")

    def test_abandoned_open_session_is_not_reported_as_paid(self):
        """
        An open session means the user never completed payment. Reporting it as
        'pending' told them a payment was being confirmed that did not exist.
        """
        self.given_subscription()

        response = self.get_success(
            build_session(
                status="open",
                payment_status="unpaid",
                subscription=None,
                client_reference_id=str(self.user.id),
            )
        )

        self.assertEqual(response.context["status"], "not_paid")

    def test_expired_session_is_not_reported_as_paid(self):
        self.given_subscription()

        response = self.get_success(
            build_session(
                status="expired",
                payment_status="unpaid",
                subscription=None,
                client_reference_id=str(self.user.id),
            )
        )

        self.assertEqual(response.context["status"], "not_paid")

    def test_completed_session_without_payment_is_treated_as_paid(self):
        """Fully discounted or trialing subscriptions complete without a charge."""
        self.given_subscription()

        response = self.get_success(
            build_session(
                status="complete",
                payment_status="no_payment_required",
                client_reference_id=str(self.user.id),
            )
        )

        self.assertEqual(response.context["status"], "pending")

    def test_active_subscription_wins_over_an_unpaid_session(self):
        """A renewal already confirmed locally is not downgraded by a stale session ID."""
        self.given_subscription(
            status=UserSubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        response = self.get_success(
            build_session(
                status="open",
                payment_status="unpaid",
                client_reference_id=str(self.user.id),
            )
        )

        self.assertEqual(response.context["status"], "active")

    # --- Rendering ---------------------------------------------------------

    def test_unpaid_page_does_not_claim_a_payment_was_made(self):
        self.given_subscription()

        response = self.get_success(
            build_session(
                status="open",
                payment_status="unpaid",
                subscription=None,
                client_reference_id=str(self.user.id),
            )
        )

        body = response.content.decode()

        self.assertNotIn("Payment successful", body)
        self.assertNotIn("Payment received", body)
        self.assertNotIn("being confirmed", body)
        self.assertIn("Checkout not completed", body)
        self.assertIn("nothing has been charged", body)

    def test_paid_page_still_confirms_the_payment(self):
        self.given_subscription(
            status=UserSubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + timezone.timedelta(days=30),
        )

        response = self.get_success(build_session(client_reference_id=str(self.user.id)))
        body = response.content.decode()

        self.assertIn("Payment successful", body)
        self.assertIn("Go to chat", body)

    def test_unpaid_page_offers_a_retry(self):
        self.given_subscription()

        response = self.get_success(
            build_session(
                status="open",
                payment_status="unpaid",
                client_reference_id=str(self.user.id),
            )
        )

        self.assertContains(
            response,
            reverse("subscriptions:create_pro_checkout_session"),
        )

    def test_amount_is_rendered_in_currency_units(self):
        """
        Stripe reports minor units, and the currency tag used to be split across
        lines, so the page showed a literal `{{ ... }}` next to a 100x amount.
        """
        self.given_subscription()

        response = self.get_success(
            build_session(
                amount_total=999,
                currency="eur",
                client_reference_id=str(self.user.id),
            )
        )
        body = response.content.decode()

        self.assertIn("9.99 EUR", body)
        self.assertNotIn("{{", body)
        self.assertNotIn("999 EUR", body)

    def test_zero_decimal_currency_is_not_divided(self):
        self.given_subscription()

        response = self.get_success(
            build_session(
                amount_total=1200,
                currency="jpy",
                client_reference_id=str(self.user.id),
            )
        )

        self.assertIn("1200 JPY", response.content.decode())

    # --- Ownership ---------------------------------------------------------

    def test_another_users_session_is_rejected(self):
        self.given_subscription()
        other_user = UserFactory()

        response = self.get_success(
            build_session(
                client_reference_id=str(other_user.id),
                customer="cus_them",
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_session_is_accepted_by_matching_customer_id(self):
        self.given_subscription()

        response = self.get_success(
            build_session(client_reference_id=None, customer="cus_me")
        )

        self.assertEqual(response.context["status"], "pending")

    def test_session_is_accepted_by_matching_client_reference_id(self):
        response = self.get_success(
            build_session(client_reference_id=str(self.user.id), customer="cus_other")
        )

        self.assertEqual(response.context["status"], "pending")

    # --- Missing / unavailable ---------------------------------------------

    def test_missing_session_id(self):
        response = self.client.get(self.url)

        self.assertEqual(response.context["status"], "missing_session")
        self.assertIsNone(response.context["session_info"])
        self.mock_retrieve.assert_not_called()

    @patch("apps.subscriptions.views.checkout.logger")
    def test_stripe_error_reports_unavailable(self, mock_logger):
        self.mock_retrieve.side_effect = stripe.APIConnectionError("boom")

        response = self.client.get(self.url, {"session_id": "cs_123"})

        self.assertEqual(response.context["status"], "unavailable")
        self.assertIsNone(response.context["session_info"])

    def test_requires_login(self):
        self.client.logout()

        response = self.client.get(self.url, {"session_id": "cs_123"})

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)
