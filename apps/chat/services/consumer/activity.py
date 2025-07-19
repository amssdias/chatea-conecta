from apps.chat.constants.redis_keys import HAS_USERS, REDIS_USERNAME_KEY
from apps.chat.services import AsyncRedisService
from apps.chat.services.consumer.group import get_group_size


async def update_chat_activity_status():
    """
    Ensures the chat remains active by checking the group size and updating the HAS_USERS key.
    """
    group_size = await get_group_size()

    if group_size:
        await AsyncRedisService.set_if_not_exists(HAS_USERS, "true")
    else:
        await AsyncRedisService.delete_key(HAS_USERS)


async def remove_user_from_active_list(scope):
    """
    Removes the user from the list of active users stored in Redis.

    This operation ensures that the user's session is no longer considered active
    once they disconnect from the WebSocket.
    """

    username = scope.get("cookies", {}).get("username", "").lower()
    await AsyncRedisService.remove_username_from_set(REDIS_USERNAME_KEY, username)
