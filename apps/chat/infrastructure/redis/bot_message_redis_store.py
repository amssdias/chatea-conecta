from __future__ import annotations

from apps.chat.constants.bot_message_redis_keys import (
    BOT_MESSAGE_CACHE_LOADED,
    BOT_USER_IDS,
    BOT_USERNAMES,
    BOT_TOPIC_IDS,
    BOT_TOPIC_MESSAGES,
    BOT_MESSAGE_SENT,
    REDIS_BOT_USER_IDS_KEY,
)
from apps.chat.constants.cache_expiration import (
    BOT_MESSAGE_CACHE_TTL,
    BOT_MESSAGE_SENT_TTL,
)
from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


class BotMessageRedisStore:
    """
    Redis storage layer for the bot message service.

    This class knows which Redis keys are used by the bot message system,
    but it does not contain business logic or database queries.
    """

    def __init__(self, redis_service=RedisService):
        self.redis_service = redis_service

    def is_cache_loaded(self) -> bool:
        """
        Return whether bot users, topics and messages were already loaded
        from the database into Redis.
        """
        return self.redis_service.key_exists(BOT_MESSAGE_CACHE_LOADED)

    def mark_cache_as_loaded(self) -> None:
        """
        Mark the bot message cache as loaded.

        This key should have a long TTL because bot users, topics and messages
        do not change very often.
        """
        self.redis_service.set_value(
            redis_key=BOT_MESSAGE_CACHE_LOADED,
            value="1",
            timeout=BOT_MESSAGE_CACHE_TTL,
        )

    def clear_cache_loaded_flag(self) -> None:
        """
        Remove the cache-loaded flag.

        Useful when you want to force the system to reload bot data from
        the database.
        """
        self.redis_service.delete_key(BOT_MESSAGE_CACHE_LOADED)

    def store_bot_users(self, users: dict[int, str]) -> None:
        """
        Store bot user IDs and usernames in Redis.

        Args:
            users: Mapping where the key is the user ID and the value is the username.

        Example:
            {
                1: "john_bot",
                2: "maria_bot",
            }
        """
        if not users:
            return

        user_ids = [str(user_id) for user_id in users.keys()]
        usernames = {str(user_id): username for user_id, username in users.items()}

        self.redis_service.add_to_set(BOT_USER_IDS, *user_ids)
        self.redis_service.store_hash(BOT_USERNAMES, usernames)

        self.redis_service.set_expiration(BOT_USER_IDS, BOT_MESSAGE_CACHE_TTL)
        self.redis_service.set_expiration(BOT_USERNAMES, BOT_MESSAGE_CACHE_TTL)

    def get_random_bot_user_id(self) -> int | None:
        """
        Return one random bot user ID from Redis.
        """
        user_id = self.redis_service.get_random_set_member(BOT_USER_IDS)

        if user_id is None:
            return None

        return int(user_id)

    def get_bot_username(self, user_id: int) -> str | None:
        """
        Return the username for a bot user ID.
        """
        return self.redis_service.get_from_hash(BOT_USERNAMES, user_id)

    def store_topic_ids(self, topic_ids: set[int]) -> None:
        """
        Store topic IDs available for normal bot messages.

        Args:
            topic_ids: Topic IDs that can be selected by the bot message service.
        """
        if not topic_ids:
            return

        self.redis_service.add_to_set(BOT_TOPIC_IDS, *topic_ids)
        self.redis_service.set_expiration(BOT_TOPIC_IDS, BOT_MESSAGE_CACHE_TTL)

    def get_random_topic_id(self) -> int | None:
        """
        Return one random topic ID from Redis.
        """
        topic_id = self.redis_service.get_random_set_member(BOT_TOPIC_IDS)

        if topic_id is None:
            return None

        return int(topic_id)

    def store_topic_messages(
            self,
            topic_id: int,
            messages: dict[int, str],
    ) -> None:
        """
        Store all available bot messages for one topic.

        Args:
            topic_id: Topic ID.
            messages: Mapping where the key is the ConversationFlow ID and
                the value is the message text.

        Example:
            {
                501: "Hello everyone!",
                502: "Anyone from Madrid?",
            }
        """
        if not messages:
            return

        redis_key = BOT_TOPIC_MESSAGES.format(topic_id=topic_id)

        redis_messages = {
            str(message_id): message for message_id, message in messages.items()
        }

        self.redis_service.store_hash(redis_key, redis_messages)
        self.redis_service.set_expiration(
            redis_key,
            BOT_MESSAGE_CACHE_TTL,
        )

    def get_topic_messages(self, topic_id: int) -> dict[int, str]:
        """
        Return all bot messages for one topic.

        Returns:
            Dictionary where the key is the ConversationFlow ID and the value
            is the message text.
        """
        redis_key = BOT_TOPIC_MESSAGES.format(topic_id=topic_id)

        messages = self.redis_service.get_hash(redis_key)

        return {int(message_id): message for message_id, message in messages.items()}

    def message_was_sent(self, message_id: int) -> bool:
        """
        Return whether a message was recently sent by any bot.

        This uses a short-lived Redis key to avoid repeating the same
        conversation message too often in the public chat.
        """
        redis_key = BOT_MESSAGE_SENT.format(message_id=message_id)

        return self.redis_service.key_exists(redis_key)

    def mark_message_as_sent(self, message_id: int) -> None:
        """
        Mark a message as recently sent by any bot.

        The key expires automatically after BOT_MESSAGE_SENT_TTL, allowing the
        same message to be reused later.
        """
        redis_key = BOT_MESSAGE_SENT.format(message_id=message_id)

        self.redis_service.set_value(
            redis_key=redis_key,
            value="1",
            timeout=BOT_MESSAGE_SENT_TTL,
        )

    def register_bot_user(self, user_id: str, username: str) -> None:
        normalized_username = username.lower()

        RedisService.add_to_set(REDIS_ALL_USERNAMES_KEY, normalized_username)
        RedisService.add_to_set(REDIS_BOT_USER_IDS_KEY, user_id)

    def is_bot_user(self, user_id: str) -> bool:
        return RedisService.is_member(REDIS_BOT_USER_IDS_KEY, user_id)
