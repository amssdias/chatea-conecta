# subscriptions/emails.py

from django.conf import settings
from django.core.mail import send_mail


def send_pro_payment_success_email(*, user):
    if not user.email:
        return

    send_mail(
        subject="Your Pro subscription is active",
        message=(
            "Thanks for upgrading to Pro. "
            "You can now open unlimited private chats."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_pro_payment_failed_email(*, user):
    if not user.email:
        return

    send_mail(
        subject="Your Pro payment failed",
        message=(
            "We could not process your Pro subscription payment. "
            "Please update your payment method to keep Pro access."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )