from apps.subscriptions.emails import send_pro_payment_success_email
from apps.subscriptions.services.user_subscription import (
    activate_subscription_from_checkout_session,
)


def handle_checkout_session_completed(event_object):
    user_subscription = activate_subscription_from_checkout_session(
        session=event_object,
    )

    if user_subscription:
        send_pro_payment_success_email(user=user_subscription.user)
