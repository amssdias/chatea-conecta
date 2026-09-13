from django.utils.translation import gettext as _

from apps.chat.constants.private_chat import (
    FREE_PRIVATE_CHAT_LIMIT,
    PRIVATE_CHAT_ACCESS_PAYMENT_OVERDUE,
    PRIVATE_CHAT_ACCESS_UNLIMITED,
    PRIVATE_CHAT_LIMIT_REACHED,
    PRIVATE_CHAT_PAYMENT_OVERDUE,
)
from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.services.activity import is_user_online
from apps.chat.services.private_chats import (
    get_open_private_chats,
    save_user_private_chat_group,
)
from apps.chat.services.subscription_access import resolve_private_chat_access
from apps.chat.websocket.broadcast import broadcast_private_chat_participant_online
from apps.chat.websocket.broadcast import notify_user_offline
from apps.chat.websocket.broadcast import send_private_chat_access_denied
from apps.chat.websocket.group_names import get_private_group_name
from apps.chat.websocket.registration import (
    register_user_to_group,
)
from apps.chat.websocket.validation import is_bot_user


def _ceiling_denial(access):
    """Pick the reason and wording that fit why this account is capped."""
    if access == PRIVATE_CHAT_ACCESS_PAYMENT_OVERDUE:
        return (
            PRIVATE_CHAT_PAYMENT_OVERDUE,
            _(
                "PRO is paused while your payment is failing, so you are back to "
                "%(limit)s private chats. Update your payment details to lift "
                "the limit."
            )
            % {"limit": FREE_PRIVATE_CHAT_LIMIT},
        )

    return (
        PRIVATE_CHAT_LIMIT_REACHED,
        _(
            "Free accounts can have up to %(limit)s private chats. "
            "Upgrade to Pro to open more private chats."
        )
        % {"limit": FREE_PRIVATE_CHAT_LIMIT},
    )


async def handle_private_invite(consumer, data):
    user_id_target = data.get("target_user_id")

    if user_id_target is None:
        return

    user_id_target = str(user_id_target)

    if user_id_target == str(consumer.id):
        return

    open_private_chats = get_open_private_chats(consumer)

    if open_private_chats.get(user_id_target):
        return

    access = await resolve_private_chat_access(consumer.user)

    if (
        access != PRIVATE_CHAT_ACCESS_UNLIMITED
        and len(open_private_chats) >= FREE_PRIVATE_CHAT_LIMIT
    ):
        reason, message = _ceiling_denial(access)

        await send_private_chat_access_denied(
            consumer=consumer,
            reason=reason,
            message=message,
            target_user_id=user_id_target,
        )
        return

    user_is_online = await is_user_online(user_id_target)
    # Reopening a closed chat has to land back in the original group, not in a
    # second one named after whoever is inviting this time round.
    private_group_id = consumer.private_chats.get(
        user_id_target
    ) or get_private_group_name(consumer.id, user_id_target)
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
    consumer.closed_private_chats.discard(user_id_target)

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

    # If this user had gone offline while the chat was closed, the other side
    # still has it greyed out, and nothing else would ever re-enable it.
    await broadcast_private_chat_participant_online(
        consumer=consumer,
        private_group_id=private_group_id,
    )
