from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY, ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


def register_user_on_redis(username, user_id=None):
    user_id = user_id if user_id else RedisService.create_user_id()
    RedisService.add_to_set(REDIS_ALL_USERNAMES_KEY, username.lower())
    RedisService.set_unique(ID_TO_USERNAME_KEY.format(user_id=user_id), username)
    RedisService.set_unique(USERNAME_TO_UUID_KEY.format(username=username), user_id)
    return user_id
