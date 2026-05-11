from apps.chat.constants.bot_message_redis_keys import REDIS_BOT_USER_IDS_KEY
from apps.chat.constants.cache_expiration import ONLINE_USER_TTL
from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
    USER_ONLINE_KEY,
)
from apps.chat.infrastructure.redis.async_redis_service import AsyncRedisService
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


async def get_online_users_count() -> int:
    return await AsyncRedisService.get_group_size(REDIS_ALL_USERNAMES_KEY)


async def cleanup_user_presence(username, user_id):
    """
    Removes the user's presence-related data from Redis.

    This includes removing the username from the active users set and deleting
    the Redis keys used to map the user ID to the username and the username to
    its generated identifier.

    This is typically used when a user disconnects from the chat.
    """
    await AsyncRedisService.remove_username_from_set(REDIS_ALL_USERNAMES_KEY, username.lower())
    await mark_user_offline(user_id)


async def mark_user_online(user_id: str) -> None:
    """
    Mark a user as online while they have an active websocket connection.

    The TTL acts as a safety net in case the websocket disconnect cleanup
    does not run correctly.
    """
    await AsyncRedisService.set_value(
        USER_ONLINE_KEY.format(user_id=user_id),
        "1",
        ex=ONLINE_USER_TTL,
    )


async def mark_user_offline(user_id: str) -> None:
    """
    Remove the user's online marker.
    """
    await AsyncRedisService.delete_key(USER_ONLINE_KEY.format(user_id=user_id))


async def is_user_online(user_id: str) -> bool:
    """
    Return True if the user currently has an active websocket presence marker.
    """
    return bool(
        await AsyncRedisService.get_value(USER_ONLINE_KEY.format(user_id=user_id))
    )


async def register_username_as_active(username: str) -> None:
    """
    Add the connected user's username back to the active usernames set.

    Used on websocket connect/reconnect so refreshes restore the username
    availability state in Redis.
    """
    await AsyncRedisService.add_to_set(
        REDIS_ALL_USERNAMES_KEY,
        username.lower(),
    )


def has_online_users() -> bool:
    """
    Return True if at least one user currently has an active websocket presence marker.
    """
    pattern = USER_ONLINE_KEY.format(user_id="*")
    return RedisService.has_keys_matching_pattern(pattern)


async def is_bot_user(user_id: str) -> bool:
    return await AsyncRedisService.is_member(REDIS_BOT_USER_IDS_KEY, user_id)
