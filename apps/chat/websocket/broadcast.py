from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP


async def notify_group_online_count(consumer, group_name: str, online_count: int):
    """Sends the updated count of online users to all members of a group."""

    await consumer.channel_layer.group_send(
        group_name,
        {
            "type": "notify.users.count",
            "group_size": online_count,
        },
    )


async def broadcast_private_chat_user_offline(consumer):
    """
    Broadcast an "offline" presence event to all private chat users of the given user.

    This helper iterates through the current user's active private chats
    (`consumer.private_chats`) and sends a `user.offline` event to each
    partner's personal notification group. On the frontend, users can
    update their UI (e.g., mark the chat as inactive or display a system message).

    Args:
        consumer: The WebSocket consumer instance that holds channel_layer
                  and the mapping of private chats (`private_chats`).
    """

    for private_username, chat_id in consumer.private_chats.items():
        await consumer.channel_layer.group_send(
            USER_NOTIFICATION_GROUP.format(username=private_username),
            {
                "type": "user.offline",
                "user_id": consumer.id,
            },
        )
