from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(ACCOUNTS_ENABLED=False)
class AccountsFlagOffTests(TestCase):
    def test_account_and_billing_pages_answer_404(self):
        url_names = [
            "users:login",
            "users:signup",
            "password_reset",
            "password_reset_done",
            "password_reset_complete",
            "password_change",
            "subscriptions:detail",
            "subscriptions:checkout_success",
            "subscriptions:checkout_cancel",
        ]

        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))

                self.assertEqual(response.status_code, 404)

    def test_account_and_billing_posts_answer_404(self):
        url_names = [
            "users:login",
            "users:signup",
            "subscriptions:create_pro_checkout_session",
            "subscriptions:cancel",
            "subscriptions:billing_portal",
        ]

        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.post(reverse(url_name))

                self.assertEqual(response.status_code, 404)

    def test_password_reset_link_answers_404(self):
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb64": "MQ", "token": "set-password"},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_stripe_webhook_answers_404(self):
        response = self.client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 404)

    def test_leaving_the_chat_still_works(self):
        """Guests leave through the logout view, so it cannot be switched off."""
        response = self.client.post(reverse("users:logout"))

        self.assertRedirects(
            response,
            reverse("chat:home"),
            fetch_redirect_response=False,
        )

    def test_admin_login_stays_reachable(self):
        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)


class AccountsFlagOnTests(TestCase):
    def test_login_and_signup_pages_render(self):
        for url_name in ("users:login", "users:signup"):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))

                self.assertEqual(response.status_code, 200)

    def test_billing_page_asks_an_anonymous_visitor_to_log_in(self):
        response = self.client.get(reverse("subscriptions:detail"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response["Location"])

    def test_stripe_webhook_is_routed(self):
        response = self.client.post(
            reverse("stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )

        self.assertNotEqual(response.status_code, 404)
