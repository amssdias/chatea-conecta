from apps.chat.constants.cache_expiration import PRIVATE_CHATS_TTL
from apps.chat.constants.redis_keys import USER_PRIVATE_CHATS_KEY
from apps.chat.services.activity import get_username_by_id, is_user_online
from apps.chat.infrastructure.redis.async_redis_service import AsyncRedisService
from apps.chat.websocket.broadcast import (
    broadcast_private_chat_participant_online,
    send_private_chats_restored,
)
from apps.chat.websocket.registration import register_user_to_group


async def save_user_private_chat_group(
        user_id: str, target_user_id, private_group: str
) -> None:
    """
    Store one private chat group for a user.

    Usually used only for Pro users, so private chats can be restored
    after refresh/reconnect.
    """
    redis_key = USER_PRIVATE_CHATS_KEY.format(user_id=user_id)

    await AsyncRedisService.set_hash_value(
        redis_key=redis_key,
        field=str(target_user_id),
        value=private_group,
        ex=PRIVATE_CHATS_TTL,
    )


def get_open_private_chats(consumer) -> dict:
    """
    Return the private chats that still count against the free-plan ceiling.

    A closed chat stays in `private_chats` so the user remains reachable and
    the other side is still told when they go offline, but it no longer
    occupies one of the free slots.
    """
    closed = consumer.closed_private_chats

    return {
        target_user_id: private_group_id
        for target_user_id, private_group_id in consumer.private_chats.items()
        if target_user_id not in closed
    }


async def remove_user_private_chat_group(user_id: str, target_user_id) -> None:
    """
    Forget one stored private chat for a user.

    Only the stored mapping is dropped. The websocket stays subscribed to the
    channel-layer group, so the chat can still be reopened by an incoming
    message during this connection.
    """
    redis_key = USER_PRIVATE_CHATS_KEY.format(user_id=user_id)

    await AsyncRedisService.delete_hash_field(
        redis_key=redis_key,
        field=str(target_user_id),
    )


async def restore_user_private_chat_groups(consumer) -> None:
    """
    Restore stored private chat groups for the connected user.

    The frontend rebuilds the whole rail from this, so each chat is sent with
    the nickname and presence it needs to be drawn. A chat whose owner mapping
    has expired can no longer be labelled, so it is dropped on both sides
    rather than left counting against the free-plan ceiling invisibly.
    """
    redis_key = USER_PRIVATE_CHATS_KEY.format(user_id=consumer.id)

    private_chats = await AsyncRedisService.get_hash(redis_key)

    if not private_chats:
        return

    restored = {}

    for target_user_id, private_group_id in private_chats.items():
        username = await get_username_by_id(target_user_id)

        if not username:
            await remove_user_private_chat_group(consumer.id, target_user_id)
            continue

        restored[target_user_id] = {
            "privateGroupId": private_group_id,
            "username": username,
            "isOnline": await is_user_online(target_user_id),
        }

    consumer.private_chats = {
        target_user_id: chat["privateGroupId"]
        for target_user_id, chat in restored.items()
    }

    if not restored:
        return

    # Sent before rejoining the groups, so an incoming message cannot race
    # ahead of the rail it belongs in.
    await send_private_chats_restored(
        consumer=consumer,
        private_chats=restored,
    )

    for private_group_id in consumer.private_chats.values():
        await register_user_to_group(consumer, private_group_id)

        await broadcast_private_chat_participant_online(
            consumer=consumer,
            private_group_id=private_group_id,
        )

    await AsyncRedisService.set_expiration(redis_key, PRIVATE_CHATS_TTL)
