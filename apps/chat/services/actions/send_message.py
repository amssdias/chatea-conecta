from django.core.cache import cache

from apps.chat.constants.message import (
    CHAT_MESSAGE_RATE_CACHE_KEY,
    CHAT_MESSAGE_RATE_LIMIT,
    CHAT_MESSAGE_RATE_LIMIT_CLOSE_CODE,
    CHAT_MESSAGE_RATE_WINDOW_SECONDS,
)
from apps.chat.websocket.broadcast import broadcast_chat_message
from apps.chat.websocket.errors import send_websocket_error
from apps.chat.websocket.exceptions import WebSocketValidationError
from apps.chat.websocket.validation import (
    validate_group_payload,
    validate_message_payload,
)


async def _count_message_in_window(cache_key: str) -> int:
    """
    Count one message in the current fixed window and return the new total.

    The first message creates the key with the window's TTL; later messages
    increment it until it expires and a new window starts.
    """
    if await cache.aadd(cache_key, 1, timeout=CHAT_MESSAGE_RATE_WINDOW_SECONDS):
        return 1

    try:
        return await cache.aincr(cache_key)
    except ValueError:
        # The key expired between ADD and INCR: this message opens a new window.
        # It goes uncounted, which is harmless for a limit this coarse.
        return 1


async def _is_rate_limited(consumer) -> bool:
    """
    Return True once an identity sends more than CHAT_MESSAGE_RATE_LIMIT
    messages inside one window.

    Keyed by the trusted user/guest id, so every socket of the same identity
    shares one quota.
    """
    cache_key = CHAT_MESSAGE_RATE_CACHE_KEY.format(user_id=consumer.id)
    return await _count_message_in_window(cache_key) > CHAT_MESSAGE_RATE_LIMIT


async def handle_send_message(consumer, data):
    try:
        group = validate_group_payload(data)
    except WebSocketValidationError:
        await consumer.close(code=401, reason="No group")
        return None

    if group.startswith("private-") and group not in consumer.groups:
        await send_websocket_error(
            consumer,
            "You are not a member of this private chat.",
        )
        return None

    if await _is_rate_limited(consumer):
        await consumer.close(
            code=CHAT_MESSAGE_RATE_LIMIT_CLOSE_CODE,
            reason="Message rate limit exceeded",
        )
        return None

    try:
        message = validate_message_payload(data)
    except WebSocketValidationError as exc:
        await send_websocket_error(consumer, str(exc))
        return None

    await broadcast_chat_message(consumer, group, message)
