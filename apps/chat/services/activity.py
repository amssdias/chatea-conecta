from apps.chat.constants.redis_keys import (
    REDIS_HAS_ACTIVE_USERS_KEY,
    REDIS_ALL_USERNAMES_KEY,
    ID_TO_USERNAME_KEY,
    USERNAME_TO_UUID_KEY,
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
    await AsyncRedisService.delete_key(ID_TO_USERNAME_KEY.format(user_id=user_id))
    await AsyncRedisService.delete_key(USERNAME_TO_UUID_KEY.format(username=username))


async def get_username_by_user_id(user_id):
    """
    Returns the username associated with the given user ID from Redis.

    If the user ID is not provided or there is no existing mapping in Redis,
    the function returns ``None``.
    """
    if not user_id:
        return None

    username = await AsyncRedisService.get_value(ID_TO_USERNAME_KEY.format(user_id=user_id))
    return username
