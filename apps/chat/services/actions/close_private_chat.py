from apps.chat.services.private_chats import remove_user_private_chat_group


async def handle_close_private_chat(consumer, data):
    """
    Free the slot a private chat was taking against the free-plan ceiling.

    Neither the channel-layer subscription nor the entry in `private_chats` is
    dropped: the first would make the other participant's next message vanish
    with no trace on either side, and the second would stop them being told
    when this user really does go offline. The chat is only marked as closed,
    which is what the ceiling counts.
    """
    user_id_target = data.get("target_user_id")

    if user_id_target is None:
        return

    user_id_target = str(user_id_target)

    if user_id_target not in consumer.private_chats:
        return

    consumer.closed_private_chats.add(user_id_target)

    # Dropped from Redis as well, so a reconnect does not silently restore a
    # chat the user closed and start counting it again.
    await remove_user_private_chat_group(consumer.id, user_id_target)
