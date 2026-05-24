from django.conf import settings
from django.core.mail import send_mail


def send_pro_payment_success_email(user, invoice_url=None):
    # TODO: Create email template

    if not user.email:
        return

    message = (
        "Thanks for upgrading to Pro. "
        "You can now open unlimited private chats."
    )

    if invoice_url:
        message += f"\n\nInvoice: {invoice_url}"

    send_mail(
        subject="Your Pro payment was processed",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_pro_payment_failed_email(user, invoice_url=None, payment_update_url=None):
    if not user.email:
        return

    message = (
        "We could not process your Pro subscription payment. "
        "Please update your payment method to keep Pro access."
    )

    if invoice_url:
        message += f"\n\nInvoice: {invoice_url}"

    if payment_update_url:
        message += f"\n\nUpdate payment method: {payment_update_url}"

    send_mail(
        subject="Your Pro payment failed",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_pro_subscription_canceled_email(user):
    if not user.email:
        return

    send_mail(
        subject="Your Pro subscription has ended",
        message="Your Pro subscription has ended and Pro access was removed.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
