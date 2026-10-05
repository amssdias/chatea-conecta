from django.conf import settings

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY, ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


def register_user_on_redis(username, user_id=None):
    """
    Register a username as active and record which id owns it.

    Callers only reach this after the username was found to be available, or
    after the caller's ownership of it was verified, so the mapping is written
    authoritatively: whoever registers a free nickname takes it over, including
    from a previous guest who released it by leaving.

    The mapping keys share the guest token lifetime, so a signed token can never
    outlive the ownership record it is validated against.
    """
    user_id = user_id if user_id else RedisService.create_user_id()
    RedisService.add_to_set(REDIS_ALL_USERNAMES_KEY, username.lower())
    RedisService.set_value(
        ID_TO_USERNAME_KEY.format(user_id=user_id),
        username,
        timeout=settings.GUEST_SESSION_MAX_AGE,
    )
    RedisService.set_value(
        USERNAME_TO_UUID_KEY.format(username=username.lower()),
        user_id,
        timeout=settings.GUEST_SESSION_MAX_AGE,
    )
    return user_id
