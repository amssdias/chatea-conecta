from django.utils.translation import gettext as _

from apps.chat.constants.private_chat import (
    FREE_PRIVATE_CHAT_LIMIT,
    PRIVATE_CHAT_LIMIT_REACHED,
)
from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.services.activity import is_user_online
from apps.chat.services.private_chats import save_user_private_chat_group
from apps.chat.services.subscription_access import user_has_pro_access
from apps.chat.websocket.broadcast import notify_user_offline
from apps.chat.websocket.broadcast import send_private_chat_access_denied
from apps.chat.websocket.group_names import get_private_group_name
from apps.chat.websocket.registration import (
    register_user_to_group,
)
from apps.chat.websocket.validation import is_bot_user


async def handle_private_invite(consumer, data):
    user_id_target = data.get("target_user_id")

    if user_id_target is None:
        return

    user_id_target = str(user_id_target)

    if user_id_target == str(consumer.id):
        return

    if consumer.private_chats.get(user_id_target):
        return

    if (
        not await user_has_pro_access(consumer.id)
        and len(consumer.private_chats) >= FREE_PRIVATE_CHAT_LIMIT
    ):
        await send_private_chat_access_denied(
            consumer=consumer,
            reason=PRIVATE_CHAT_LIMIT_REACHED,
            message=_(
                "Free accounts can have up to %(limit)s private chats. "
                "Upgrade to Pro to open more private chats."
            )
            % {"limit": FREE_PRIVATE_CHAT_LIMIT},
            target_user_id=user_id_target,
        )
        return

    user_is_online = await is_user_online(user_id_target)
    private_group_id = get_private_group_name(consumer.id, user_id_target)
    user_is_bot = await is_bot_user(user_id_target)

    if not user_is_online and not user_is_bot:
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

    if user_is_bot:
        return

    # Notify the other user, so he's added to the private group
    await consumer.channel_layer.group_send(
        USER_NOTIFICATION_GROUP.format(user_id=user_id_target),
        {
            "type": "chat.invite",
            "from_user_id": consumer.id,
            "private_group": private_group_id,
        },
    )
