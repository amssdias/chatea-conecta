import json

from apps.chat.constants.consumer import PRIVATE_CHATS_RESTORED
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


async def notify_user_offline(
        channel_layer, receiver_user_id, offline_user_id, chat_id
):
    """
    Notify a user that another user is offline or unavailable.

    Args:
        channel_layer: Channels layer used to send the event.
        receiver_user_id: User that should receive the notification.
        offline_user_id: User that is offline/unavailable.
    """
    await channel_layer.group_send(
        USER_NOTIFICATION_GROUP.format(user_id=receiver_user_id),
        {
            "type": "user.offline",
            "user_id": offline_user_id,
            "chat_id": chat_id,
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

    for private_user_id, chat_id in consumer.private_chats.items():
        await notify_user_offline(
            channel_layer=consumer.channel_layer,
            receiver_user_id=private_user_id,
            offline_user_id=consumer.id,
            chat_id=chat_id,
        )


async def broadcast_private_chat_participant_online(
        consumer, private_group_id: str
) -> None:
    """
    Notify users in a private chat group that the current user is online again.
    """
    await consumer.channel_layer.group_send(
        private_group_id,
        {
            "type": "private.chat.participant.online",
            "user_id": consumer.id,
            "private_group_id": private_group_id,
        },
    )


async def send_private_chats_restored(consumer, private_chats: dict) -> None:
    """
    Send restored private chats to the current websocket connection.

    This is used after reconnect/refresh so the frontend can rebuild its
    local private chats state.
    """
    await consumer.send(
        text_data=json.dumps(
            {
                "type": PRIVATE_CHATS_RESTORED,
                "privateChats": private_chats,
            }
        )
    )


async def broadcast_chat_message(consumer, group: str, message: str) -> None:
    """Broadcast a regular chat message to a room group."""
    await consumer.channel_layer.group_send(
        group,
        {
            "type": "chat.message",
            "message": message,
            "username": consumer.username,
            "user_id": consumer.id,
            "group": group,
        },
    )
