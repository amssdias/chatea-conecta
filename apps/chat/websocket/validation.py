from apps.chat.constants.bot_message_redis_keys import REDIS_BOT_USER_IDS_KEY
from apps.chat.constants.message import MAX_CHAT_MESSAGE_LENGTH
from apps.chat.infrastructure.redis.async_redis_service import AsyncRedisService
from apps.chat.websocket.exceptions import WebSocketValidationError


CLIENT_ALLOWED_GROUPS = frozenset({"chatea"})


def validate_group_payload(data: dict) -> str:
    group = data.get("group")

    if not isinstance(group, str):
        raise WebSocketValidationError("Invalid group")

    normalized_group = group.strip().lower()
    if not normalized_group:
        raise WebSocketValidationError("Missing group")

    return normalized_group


def validate_message_payload(data: dict) -> str:
    message = data.get("message")

    if not isinstance(message, str):
        raise WebSocketValidationError("Message must be text")

    if not message.strip():
        raise WebSocketValidationError("Message cannot be empty")

    if len(message) > MAX_CHAT_MESSAGE_LENGTH:
        raise WebSocketValidationError("Message is too long")

    return message


async def is_bot_user(user_id: str) -> bool:
    return await AsyncRedisService.is_member(REDIS_BOT_USER_IDS_KEY, user_id)


def validate_group_registered(group: str):
    # Avoid registrations to user inbox groups and others
    if group not in CLIENT_ALLOWED_GROUPS:
        raise WebSocketValidationError("Invalid group")
