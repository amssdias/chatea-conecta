from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.websocket.registration import get_private_group_name, register_user_to_group


async def handle_private_invite(consumer, data):
    user_id_target = data.get("target_user_id").replace(" ", "-")

    if consumer.private_chats.get(user_id_target):
        return

    # Add user to private group created
    private_group = await get_private_group_name(consumer.id, user_id_target)
    await register_user_to_group(consumer, private_group)

    consumer.private_chats[user_id_target] = private_group

    # Notify the other user, so he's added to the private group
    await consumer.channel_layer.group_send(
        USER_NOTIFICATION_GROUP.format(username=user_id_target),
        {
            "type": "chat.invite",
            "from_user_id": consumer.id,
            "private_group": private_group,
        }
    )
