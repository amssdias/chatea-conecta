from apps.chat.services.activity import mark_user_online
from apps.chat.services.guest_session import arefresh_guest_identity


async def handle_heartbeat(consumer, data):
    """
    Refresh the user's online presence marker in Redis.

    Guests also get their identity mapping extended, so an open session never
    has the ownership record it is validated against expire underneath it.
    """
    await mark_user_online(consumer.id)

    if not consumer.user.is_authenticated:
        await arefresh_guest_identity(consumer.username, consumer.id)
