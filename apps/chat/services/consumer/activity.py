from apps.chat.constants.redis_keys import REDIS_HAS_ACTIVE_USERS_KEY, REDIS_ALL_USERNAMES_KEY, ID_TO_USERNAME_KEY, \
    USER_NOTIFICATION_GROUP, USERNAME_TO_UUID_KEY
from apps.chat.services import AsyncRedisService
from apps.chat.services.consumer.group import get_group_size


async def update_chat_activity_status():
    """
    Ensures the chat remains active by checking the group size and updating the REDIS_HAS_ACTIVE_USERS_KEY key.
    """
    group_size = await get_group_size()

    if group_size:
        await AsyncRedisService.set_if_not_exists(REDIS_HAS_ACTIVE_USERS_KEY, "true")
    else:
        await AsyncRedisService.delete_key(REDIS_HAS_ACTIVE_USERS_KEY)


async def remove_user_from_active_list(scope):
    """
    Removes the user from the list of active users stored in Redis.

    This operation ensures that the user's session is no longer considered active
    once they disconnect from the WebSocket.
    """

    username = scope.get("cookies", {}).get("username", "").lower()
    await AsyncRedisService.remove_username_from_set(REDIS_ALL_USERNAMES_KEY, username)


async def remove_user_from_redis(scope):
    cookies = scope.get("cookies")

    username = cookies.get("username", "").lower()
    await AsyncRedisService.remove_username_from_set(REDIS_ALL_USERNAMES_KEY, username)

    user_id = cookies.get("user_id")
    await AsyncRedisService.delete_key(ID_TO_USERNAME_KEY.format(user_id=user_id))
    await AsyncRedisService.delete_key(USERNAME_TO_UUID_KEY.format(username=username))


async def broadcast_private_chat_user_offline(consumer, username):
    """
    Broadcast an "offline" presence event to all private chat users of the given user.

    This helper iterates through the current user's active private chats
    (`consumer.private_chats`) and sends a `user.offline` event to each
    partner's personal notification group. On the frontend, users can
    update their UI (e.g., mark the chat as inactive or display a system message).

    Args:
        consumer: The WebSocket consumer instance that holds channel_layer
                  and the mapping of private chats (`private_chats`).
        username: The username of the user who just went offline.
    """

    for private_username, chat_id in consumer.private_chats.items():
        await consumer.channel_layer.group_send(
            USER_NOTIFICATION_GROUP.format(username=private_username),
            {
                "type": "user.offline",
                "private_chat_username": username,
                "user_id": consumer.id,
            },
        )
