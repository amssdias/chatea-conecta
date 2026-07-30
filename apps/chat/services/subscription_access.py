from __future__ import annotations

from channels.db import database_sync_to_async

from apps.subscriptions.models import UserSubscription


@database_sync_to_async
def user_has_pro_access(user_id: str | int) -> bool:
    """Return whether the database grants Pro access to the given user."""
    try:
        numeric_user_id = int(user_id)
    except (TypeError, ValueError):
        return False

    subscription = UserSubscription.objects.filter(user_id=numeric_user_id).first()
    return bool(subscription and subscription.pro)
