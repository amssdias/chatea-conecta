from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.services import AsyncRedisService


async def validate_user_connection(scope):
    username = scope["cookies"].get("username", "")
    if not username:
        return None
    lower = username.lower()
    if not await AsyncRedisService.is_user_in_set(REDIS_USERNAME_KEY, lower):
        return None
    return username


def validate_group_payload(data: dict) -> str:
    group = data.get("group", "").lower()
    if not group:
        raise ValueError("Missing group")
    return group
