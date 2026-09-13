from __future__ import annotations

from channels.db import database_sync_to_async

from apps.chat.constants.private_chat import (
    PRIVATE_CHAT_ACCESS_FREE,
    PRIVATE_CHAT_ACCESS_PAYMENT_OVERDUE,
    PRIVATE_CHAT_ACCESS_UNLIMITED,
)
from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus


@database_sync_to_async
def resolve_private_chat_access(user) -> str:
    """
    Resolve how the private-chat ceiling applies to the given user.

    A past-due subscription keeps its grace period everywhere else, but the
    ceiling comes back here: unlimited private chats while the payment is
    failing is the one benefit worth holding back to get the card fixed. It is
    checked before ``pro`` so the account is told about billing rather than
    being sold an upgrade it already bought.
    """
    if not user.is_authenticated:
        return PRIVATE_CHAT_ACCESS_FREE

    subscription = UserSubscription.objects.filter(
        user_id=user.pk,
    ).first()

    if not subscription:
        return PRIVATE_CHAT_ACCESS_FREE

    if subscription.status == UserSubscriptionStatus.PAST_DUE:
        return PRIVATE_CHAT_ACCESS_PAYMENT_OVERDUE

    if subscription.pro:
        return PRIVATE_CHAT_ACCESS_UNLIMITED

    return PRIVATE_CHAT_ACCESS_FREE
