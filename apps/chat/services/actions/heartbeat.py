from apps.chat.services.activity import mark_user_online


async def handle_heartbeat(consumer, data):
    """
    Refresh the user's online presence marker in Redis.
    """
    await mark_user_online(consumer.id)
