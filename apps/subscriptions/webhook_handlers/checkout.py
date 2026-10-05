from stripe.checkout import Session

from apps.integrations.stripe.subscriptions import retrieve_subscription
from apps.subscriptions.services.user_subscription import (
    sync_user_subscription_from_checkout,
)
from apps.subscriptions.webhook_handlers.mappers import (
    build_subscription_sync_dto,
)


def handle_checkout_session_completed(session: Session):
    subscription = retrieve_subscription(session.subscription)
    subscription_sync = build_subscription_sync_dto(subscription)

    sync_user_subscription_from_checkout(subscription_sync)
