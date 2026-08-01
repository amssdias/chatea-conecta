from __future__ import annotations

from channels.db import database_sync_to_async

from apps.subscriptions.models import UserSubscription


@database_sync_to_async
def user_has_pro_access(user) -> bool:
    """Return whether the database grants Pro access to the given user."""
    if not user.is_authenticated:
        return False

    subscription = UserSubscription.objects.filter(
        user_id=user.pk,
    ).first()

    return bool(subscription and subscription.pro)
