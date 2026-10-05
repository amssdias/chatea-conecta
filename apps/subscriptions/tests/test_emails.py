from datetime import date
from smtplib import SMTPException
from unittest.mock import Mock, patch

from django.core import mail
from django.core.mail import BadHeaderError
from django.test import SimpleTestCase, override_settings

from apps.subscriptions.emails import (
    EmailDeliveryError,
    EmailRecipientError,
    _get_valid_recipient_email,
    _send_html_email,
)
from apps.subscriptions.emails import (
    send_pro_payment_failed_email,
    send_pro_payment_success_email,
    send_pro_subscription_canceled_email,
)


class GetValidRecipientEmailTests(SimpleTestCase):
    def test_get_valid_recipient_email_returns_user_email(self):
        user = Mock()
        user.id = 10
        user.email = "john@example.com"

        result = _get_valid_recipient_email(user)

        self.assertEqual(result, "john@example.com")

    def test_get_valid_recipient_email_raises_error_when_user_is_missing(self):
        with self.assertRaisesMessage(
                EmailRecipientError,
                "Cannot send email because user is missing.",
        ):
            _get_valid_recipient_email(None)

    def test_get_valid_recipient_email_raises_error_when_user_has_no_email(self):
        user = Mock()
        user.id = 10
        user.email = ""

        with self.assertRaisesMessage(
                EmailRecipientError,
                "Cannot send email because user_id=10 has no email.",
        ):
            _get_valid_recipient_email(user)

    def test_get_valid_recipient_email_raises_error_when_email_is_invalid(self):
        user = Mock()
        user.id = 10
        user.email = "invalid-email"

        with self.assertRaisesMessage(
                EmailRecipientError,
                "Cannot send email because user_id=10 has invalid email=invalid-email.",
        ):
            _get_valid_recipient_email(user)


class SendHtmlEmailTests(SimpleTestCase):

    @patch("apps.subscriptions.emails.EmailMultiAlternatives")
    @patch("apps.subscriptions.emails.render_to_string")
    def test_send_html_email_renders_template_and_sends_email(
            self,
            mock_render_to_string,
            mock_email_multi_alternatives,
    ):
        mock_render_to_string.return_value = "<p>Hello Dias</p>"

        email = Mock()
        email.send.return_value = 1
        mock_email_multi_alternatives.return_value = email

        _send_html_email(
            subject="Test subject",
            template_name="subscriptions/emails/test.html",
            text_message="Plain text message",
            recipient_email="dias@example.com",
            context={"name": "Dias"},
        )

        mock_render_to_string.assert_called_once_with(
            "subscriptions/emails/test.html",
            {"name": "Dias"},
        )

        mock_email_multi_alternatives.assert_called_once_with(
            subject="Test subject",
            body="Plain text message",
            from_email="no-reply@chatea-conecta.com",
            to=["dias@example.com"],
        )

        email.attach_alternative.assert_called_once_with(
            "<p>Hello Dias</p>",
            "text/html",
        )
        email.send.assert_called_once_with(fail_silently=False)

    @patch("apps.subscriptions.emails.EmailMultiAlternatives")
    @patch("apps.subscriptions.emails.render_to_string")
    def test_send_html_email_raises_delivery_error_when_bad_header_error_happens(
            self,
            mock_render_to_string,
            mock_email_multi_alternatives,
    ):
        mock_render_to_string.return_value = "<p>Hello Dias</p>"

        email = Mock()
        email.send.side_effect = BadHeaderError("Invalid header")
        mock_email_multi_alternatives.return_value = email

        with self.assertRaisesMessage(
                EmailDeliveryError,
                "Invalid email header while sending subject=Test subject to=dias@example.com.",
        ):
            _send_html_email(
                subject="Test subject",
                template_name="subscriptions/emails/test.html",
                text_message="Plain text message",
                recipient_email="dias@example.com",
                context={"name": "Dias"},
            )

    @patch("apps.subscriptions.emails.EmailMultiAlternatives")
    @patch("apps.subscriptions.emails.render_to_string")
    def test_send_html_email_raises_delivery_error_when_smtp_error_happens(
            self,
            mock_render_to_string,
            mock_email_multi_alternatives,
    ):
        mock_render_to_string.return_value = "<p>Hello Dias</p>"

        email = Mock()
        email.send.side_effect = SMTPException("SMTP failed")
        mock_email_multi_alternatives.return_value = email

        with self.assertRaisesMessage(
                EmailDeliveryError,
                "SMTP error while sending subject=Test subject to=dias@example.com.",
        ):
            _send_html_email(
                subject="Test subject",
                template_name="subscriptions/emails/test.html",
                text_message="Plain text message",
                recipient_email="dias@example.com",
                context={"name": "Dias"},
            )

    @patch("apps.subscriptions.emails.EmailMultiAlternatives")
    @patch("apps.subscriptions.emails.render_to_string")
    def test_send_html_email_raises_delivery_error_when_unexpected_error_happens(
            self,
            mock_render_to_string,
            mock_email_multi_alternatives,
    ):
        mock_render_to_string.return_value = "<p>Hello Dias</p>"

        email = Mock()
        email.send.side_effect = RuntimeError("Unexpected failure")
        mock_email_multi_alternatives.return_value = email

        with self.assertRaisesMessage(
                EmailDeliveryError,
                "Unexpected error while sending subject=Test subject to=dias@example.com.",
        ):
            _send_html_email(
                subject="Test subject",
                template_name="subscriptions/emails/test.html",
                text_message="Plain text message",
                recipient_email="dias@example.com",
                context={"name": "Dias"},
            )

    @patch("apps.subscriptions.emails.EmailMultiAlternatives")
    @patch("apps.subscriptions.emails.render_to_string")
    def test_send_html_email_raises_delivery_error_when_backend_sends_zero_emails(
            self,
            mock_render_to_string,
            mock_email_multi_alternatives,
    ):
        mock_render_to_string.return_value = "<p>Hello Dias</p>"

        email = Mock()
        email.send.return_value = 0
        mock_email_multi_alternatives.return_value = email

        with self.assertRaisesMessage(
                EmailDeliveryError,
                "Email backend returned 0 sent emails. subject=Test subject, to=dias@example.com.",
        ):
            _send_html_email(
                subject="Test subject",
                template_name="subscriptions/emails/test.html",
                text_message="Plain text message",
                recipient_email="dias@example.com",
                context={"name": "Dias"},
            )


@override_settings(SITE_URL="https://chatea-conecta.test/")
class SendProPaymentSuccessEmailTests(SimpleTestCase):
    def setUp(self):
        mail.outbox = []

    def test_send_pro_payment_success_email_sends_email_with_invoice_url(self):
        user = Mock()
        user.id = 10
        user.email = "dias@example.com"

        send_pro_payment_success_email(
            user=user,
            invoice_url="https://stripe.test/invoice/123",
        )

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, "Your Pro payment was processed")
        self.assertEqual(email.from_email, "no-reply@chatea-conecta.com")
        self.assertEqual(email.to, ["dias@example.com"])

        self.assertIn(
            "Thanks for your payment. Your Pro access is now active",
            email.body,
        )
        self.assertIn(
            "Invoice: https://stripe.test/invoice/123",
            email.body,
        )

        self.assertEqual(len(email.alternatives), 1)

        html_message = email.alternatives[0][0]
        html_mimetype = email.alternatives[0][1]

        self.assertEqual(html_mimetype, "text/html")
        self.assertIn("Your Pro subscription is active", html_message)
        self.assertIn("https://stripe.test/invoice/123", html_message)
        self.assertIn("https://chatea-conecta.test", html_message)
        self.assertIn("support@chatea-conecta.test", html_message)

    def test_send_pro_payment_success_email_sends_email_without_invoice_url(self):
        user = Mock()
        user.id = 10
        user.email = "dias@example.com"

        send_pro_payment_success_email(user=user)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, "Your Pro payment was processed")
        self.assertEqual(email.to, ["dias@example.com"])

        self.assertIn(
            "Thanks for your payment. Your Pro access is now active",
            email.body,
        )
        self.assertNotIn("Invoice:", email.body)

        html_message = email.alternatives[0][0]

        self.assertIn("Your Pro subscription is active", html_message)
        self.assertNotIn("https://stripe.test/invoice/123", html_message)


@override_settings(SITE_URL="https://chatea-conecta.test/")
class SendProPaymentFailedEmailTests(SimpleTestCase):
    def setUp(self):
        mail.outbox = []

    def test_send_pro_payment_failed_email_sends_email_with_invoice_and_payment_update_urls(
            self,
    ):
        user = Mock()
        user.id = 10
        user.email = "dias@example.com"

        send_pro_payment_failed_email(
            user=user,
            invoice_url="https://stripe.test/invoice/123",
            payment_update_url="https://stripe.test/update-payment-method",
        )

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, "Your Pro payment failed")
        self.assertEqual(email.from_email, "no-reply@chatea-conecta.com")
        self.assertEqual(email.to, ["dias@example.com"])

        self.assertIn(
            "We tried to renew your Pro subscription, but the payment did not go through.",
            email.body,
        )
        self.assertIn(
            "Please update your payment method to avoid losing Pro access.",
            email.body,
        )
        self.assertIn(
            "Invoice: https://stripe.test/invoice/123",
            email.body,
        )
        self.assertIn(
            "Update payment method: https://stripe.test/update-payment-method",
            email.body,
        )

        self.assertEqual(len(email.alternatives), 1)

        html_message = email.alternatives[0][0]
        html_mimetype = email.alternatives[0][1]

        self.assertEqual(html_mimetype, "text/html")
        self.assertIn("We could not process your Pro payment", html_message)
        self.assertIn("https://stripe.test/invoice/123", html_message)
        self.assertIn("https://stripe.test/update-payment-method", html_message)
        self.assertIn("support@chatea-conecta.test", html_message)

    def test_send_pro_payment_failed_email_sends_email_without_optional_urls(self):
        user = Mock()
        user.id = 10
        user.email = "dias@example.com"

        send_pro_payment_failed_email(user=user)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, "Your Pro payment failed")
        self.assertEqual(email.to, ["dias@example.com"])

        self.assertIn(
            "We tried to renew your Pro subscription, but the payment did not go through.",
            email.body,
        )
        self.assertNotIn("Invoice:", email.body)
        self.assertNotIn("Update payment method:", email.body)

        html_message = email.alternatives[0][0]

        self.assertIn("We could not process your Pro payment", html_message)
        self.assertIn("https://chatea-conecta.test", html_message)
        self.assertIn("support@chatea-conecta.test", html_message)
        self.assertNotIn("https://stripe.test/invoice/123", html_message)
        self.assertNotIn("https://stripe.test/update-payment-method", html_message)


@override_settings(
    SITE_URL="https://chatea-conecta.test/",
    LANGUAGE_CODE="en-us",
)
class SendProSubscriptionCanceledEmailTests(SimpleTestCase):
    def setUp(self):
        mail.outbox = []

    def test_send_pro_subscription_canceled_email_sends_email_with_ended_at(self):
        user = Mock()
        user.id = 10
        user.email = "dias@example.com"

        send_pro_subscription_canceled_email(
            user=user,
            ended_at=date(2026, 6, 1),
        )

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, "Your Pro subscription has ended")
        self.assertEqual(email.from_email, "no-reply@chatea-conecta.com")
        self.assertEqual(email.to, ["dias@example.com"])

        self.assertIn(
            "Your Pro subscription has ended and Pro access was removed.",
            email.body,
        )
        self.assertIn(
            "You can still use Chatea-Conecta with the free plan.",
            email.body,
        )
        self.assertIn(
            "Go to Chatea-Conecta: https://chatea-conecta.test",
            email.body,
        )

        self.assertEqual(len(email.alternatives), 1)

        html_message = email.alternatives[0][0]
        html_mimetype = email.alternatives[0][1]

        self.assertEqual(html_mimetype, "text/html")
        self.assertIn("Your Pro access has ended", html_message)
        self.assertIn("Subscription ended", html_message)
        self.assertIn("Ended", html_message)
        self.assertIn("Ended on", html_message)
        self.assertIn("June 1, 2026", html_message)
        self.assertIn("https://chatea-conecta.test", html_message)
        self.assertIn("support@chatea-conecta.test", html_message)

    def test_send_pro_subscription_canceled_email_sends_email_without_ended_at(self):
        user = Mock()
        user.id = 10
        user.email = "dias@example.com"

        send_pro_subscription_canceled_email(user=user)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, "Your Pro subscription has ended")
        self.assertEqual(email.to, ["dias@example.com"])

        self.assertIn(
            "Your Pro subscription has ended and Pro access was removed.",
            email.body,
        )
        self.assertIn(
            "Go to Chatea-Conecta: https://chatea-conecta.test",
            email.body,
        )

        html_message = email.alternatives[0][0]

        self.assertIn("Your Pro access has ended", html_message)
        self.assertIn("Subscription ended", html_message)
        self.assertIn("Ended", html_message)
        self.assertNotIn("Ended on", html_message)
        self.assertNotIn("June 1, 2026", html_message)
        self.assertIn("https://chatea-conecta.test", html_message)
        self.assertIn("support@chatea-conecta.test", html_message)
