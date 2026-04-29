from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.services.activity import is_user_online
from apps.chat.services.private_chats import save_user_private_chat_group
from apps.chat.websocket.broadcast import notify_user_offline
from apps.chat.websocket.group_names import get_private_group_name
from apps.chat.websocket.registration import (
    register_user_to_group,
)


async def handle_private_invite(consumer, data):
    user_id_target = data.get("target_user_id")

    if consumer.private_chats.get(user_id_target):
        return

    user_is_online = await is_user_online(user_id_target)
    private_group_id = get_private_group_name(consumer.id, user_id_target)

    if not user_is_online:
        await notify_user_offline(
            channel_layer=consumer.channel_layer,
            receiver_user_id=consumer.id,
            offline_user_id=user_id_target,
            chat_id=private_group_id,
        )
        return

    # Add user to private group created
    await register_user_to_group(consumer, private_group_id)
    await save_user_private_chat_group(consumer.id, user_id_target, private_group_id)

    consumer.private_chats[user_id_target] = private_group_id

    # Notify the other user, so he's added to the private group
    await consumer.channel_layer.group_send(
        USER_NOTIFICATION_GROUP.format(user_id=user_id_target),
        {
            "type": "chat.invite",
            "from_user_id": consumer.id,
            "private_group": private_group_id,
        },
    )
