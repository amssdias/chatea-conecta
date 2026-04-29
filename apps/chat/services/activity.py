from apps.chat.constants.cache_expiration import ONLINE_USER_TTL
from apps.chat.constants.redis_keys import (
    REDIS_HAS_ACTIVE_USERS_KEY,
    REDIS_ALL_USERNAMES_KEY,
    USER_ONLINE_KEY,
)
from apps.chat.infrastructure.redis.async_redis_service import AsyncRedisService


async def get_online_users_count() -> int:
    return await AsyncRedisService.get_group_size(REDIS_ALL_USERNAMES_KEY)


async def update_chat_activity_status():
    """
    Ensures the chat remains active by checking the group size and updating the REDIS_HAS_ACTIVE_USERS_KEY key.
    """
    group_size = await get_online_users_count()

    if group_size:
        await AsyncRedisService.set_if_not_exists(REDIS_HAS_ACTIVE_USERS_KEY, "true")
    else:
        await AsyncRedisService.delete_key(REDIS_HAS_ACTIVE_USERS_KEY)


async def cleanup_user_presence(username, user_id):
    """
    Removes the user's presence-related data from Redis.

    This includes removing the username from the active users set and deleting
    the Redis keys used to map the user ID to the username and the username to
    its generated identifier.

    This is typically used when a user disconnects from the chat.
    """
    await AsyncRedisService.remove_username_from_set(REDIS_ALL_USERNAMES_KEY, username)


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
