from smtplib import SMTPException

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, EmailMultiAlternatives
from django.core.validators import validate_email
from django.template.loader import render_to_string


class EmailRecipientError(ValueError):
    pass


class EmailDeliveryError(Exception):
    pass


def _get_valid_recipient_email(user) -> str:
    if not user:
        raise EmailRecipientError("Cannot send email because user is missing.")

    if not user.email:
        raise EmailRecipientError(
            f"Cannot send email because user_id={user.id} has no email."
        )

    try:
        validate_email(user.email)
    except ValidationError as exc:
        raise EmailRecipientError(
            f"Cannot send email because user_id={user.id} has invalid email={user.email}."
        ) from exc

    return user.email


def _send_html_email(
        subject: str,
        template_name: str,
        text_message: str,
        recipient_email: str,
        context: dict,
) -> None:
    html_message = render_to_string(template_name, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach_alternative(html_message, "text/html")

    try:
        sent_count = email.send(fail_silently=False)
    except BadHeaderError as exc:
        raise EmailDeliveryError(
            f"Invalid email header while sending subject={subject} to={recipient_email}."
        ) from exc
    except SMTPException as exc:
        raise EmailDeliveryError(
            f"SMTP error while sending subject={subject} to={recipient_email}."
        ) from exc
    except Exception as exc:
        raise EmailDeliveryError(
            f"Unexpected error while sending subject={subject} to={recipient_email}."
        ) from exc

    if sent_count == 0:
        raise EmailDeliveryError(
            f"Email backend returned 0 sent emails. subject={subject}, to={recipient_email}."
        )


def send_pro_payment_success_email(user, invoice_url=None):
    recipient_email = _get_valid_recipient_email(user)

    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    support_email = getattr(settings, "SUPPORT_EMAIL", None) or getattr(
        settings,
        "EMAIL_HOST_USER",
        None,
    )

    context = {
        "invoice_url": invoice_url,
        "site_url": site_url,
        "chat_url": None,
        "subscription_url": None,
        "support_email": support_email,
    }

    text_message = (
        "Thanks for your payment. Your Pro access is now active, "
        "so you can keep enjoying unlimited private chats."
    )

    if invoice_url:
        text_message += f"\n\nInvoice: {invoice_url}"

    _send_html_email(
        subject="Your Pro payment was processed",
        template_name="subscriptions/emails/invoice_paid.html",
        text_message=text_message,
        recipient_email=recipient_email,
        context=context,
    )


def send_pro_payment_failed_email(user, invoice_url=None, payment_update_url=None):
    recipient_email = _get_valid_recipient_email(user)

    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    support_email = getattr(settings, "SUPPORT_EMAIL", None) or getattr(
        settings,
        "EMAIL_HOST_USER",
        None,
    )

    context = {
        "invoice_url": invoice_url,
        "payment_update_url": payment_update_url,
        "site_url": site_url,
        "subscription_url": None,
        "support_email": support_email,
    }

    text_message = (
        "We tried to renew your Pro subscription, but the payment did not go through. "
        "Please update your payment method to avoid losing Pro access."
    )

    if invoice_url:
        text_message += f"\n\nInvoice: {invoice_url}"

    if payment_update_url:
        text_message += f"\n\nUpdate payment method: {payment_update_url}"

    _send_html_email(
        subject="Your Pro payment failed",
        template_name="subscriptions/emails/invoice_payment_failed.html",
        text_message=text_message,
        recipient_email=recipient_email,
        context=context,
    )


def send_pro_subscription_canceled_email(user, ended_at=None):
    recipient_email = _get_valid_recipient_email(user)

    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    support_email = getattr(settings, "SUPPORT_EMAIL", None) or getattr(
        settings,
        "EMAIL_HOST_USER",
        None,
    )

    context = {
        "site_url": site_url,
        "ended_at": ended_at,
        "support_email": support_email,
    }

    text_message = (
        "Your Pro subscription has ended and Pro access was removed. "
        "You can still use Chatea-Conecta with the free plan."
    )

    if site_url:
        text_message += f"\n\nGo to Chatea-Conecta: {site_url}"

    _send_html_email(
        subject="Your Pro subscription has ended",
        template_name="subscriptions/emails/subscription_canceled.html",
        text_message=text_message,
        recipient_email=recipient_email,
        context=context,
    )
