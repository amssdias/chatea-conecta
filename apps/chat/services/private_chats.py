from apps.chat.constants.cache_expiration import PRIVATE_CHATS_TTL
from apps.chat.constants.redis_keys import USER_PRIVATE_CHATS_KEY
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


async def restore_user_private_chat_groups(consumer) -> None:
    """
    Restore stored private chat groups for the connected user.

    Registers the current websocket connection back into each saved
    private group, then notifies the other participants that this user
    is online again.
    """
    redis_key = USER_PRIVATE_CHATS_KEY.format(user_id=consumer.id)

    private_chats = await AsyncRedisService.get_hash(redis_key)

    if not private_chats:
        return

    consumer.private_chats = private_chats

    await send_private_chats_restored(
        consumer=consumer,
        private_chats=private_chats,
    )

    for target_user_id, private_group_id in private_chats.items():
        await register_user_to_group(consumer, private_group_id)

        await broadcast_private_chat_participant_online(
            consumer=consumer,
            private_group_id=private_group_id,
        )

    await AsyncRedisService.set_expiration(redis_key, PRIVATE_CHATS_TTL)
