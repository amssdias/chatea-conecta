from apps.chat.constants.bot_message_redis_keys import REDIS_BOT_USER_IDS_KEY
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

    # Avoid registrations to user inbox groups and others
    if normalized_group not in CLIENT_ALLOWED_GROUPS:
        raise WebSocketValidationError("Invalid group")

    return normalized_group


async def is_bot_user(user_id: str) -> bool:
    return await AsyncRedisService.is_member(REDIS_BOT_USER_IDS_KEY, user_id)
