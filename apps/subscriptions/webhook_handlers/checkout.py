from stripe.checkout import Session

from apps.subscriptions.services.user_subscription import save_stripe_subscription_id


def handle_checkout_session_completed(session: Session):
    save_stripe_subscription_id(
        stripe_customer_id=session.customer,
        stripe_subscription_id=session.subscription
    )
