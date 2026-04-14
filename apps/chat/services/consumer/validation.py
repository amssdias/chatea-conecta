from apps.chat.constants.redis_keys import ID_TO_USERNAME_KEY
from apps.chat.services import AsyncRedisService


async def validate_user_connection(user_id):
    if not user_id:
        return None

    username = await AsyncRedisService.get_value(ID_TO_USERNAME_KEY.format(user_id=user_id))
    return username


def validate_group_payload(data: dict) -> str:
    group = data.get("group", "").lower()
    if not group:
        raise ValueError("Missing group")
    return group
