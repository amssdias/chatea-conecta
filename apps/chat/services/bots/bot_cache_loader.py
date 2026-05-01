from __future__ import annotations

from django.contrib.auth import get_user_model

from apps.chat.infrastructure.redis.bot_message_redis_store import (
    BotMessageRedisStore,
)
from apps.chat.models import ConversationFlow, Topic

User = get_user_model()


class BotCacheLoader:
    """
    Loads bot message data from the database into Redis.

    This service is responsible for preparing the Redis cache used by the
    bot message service. It should contain database queries, but not message
    selection logic.
    """

    def __init__(self, redis_store: BotMessageRedisStore | None = None):
        self.redis_store = redis_store or BotMessageRedisStore()

    def load(self) -> None:
        """
        Load all bot users, topics and topic messages into Redis.
        """
        self._load_bot_users()
        self._load_topics_and_messages()
        self.redis_store.mark_cache_as_loaded()

    def _load_bot_users(self) -> None:
        """
        Load all non-staff, non-superuser users that can act as public chat bots.
        """
        users = dict(
            User.objects.filter(
                is_staff=False,
                is_superuser=False,
            ).values_list("id", "username")
        )

        for bot_id, bot_username in users.items():
            self.redis_store.register_bot_user(
                user_id=str(bot_id),
                username=bot_username,
            )

        self.redis_store.store_bot_users(users)

    def _load_topics_and_messages(self) -> None:
        """
        Load all topics and their conversation messages into Redis.
        """
        topic_ids = set(
            Topic.objects.values_list("id", flat=True)
        )

        self.redis_store.store_topic_ids(topic_ids)

        for topic_id in topic_ids:
            messages = self._get_messages_for_topic(topic_id)

            if not messages:
                continue

            self.redis_store.store_topic_messages(
                topic_id=topic_id,
                messages=messages,
            )

    def _get_messages_for_topic(self, topic_id: int) -> dict[int, str]:
        """
        Return all non-promotional conversation messages for one topic.

        Returns:
            Mapping where the key is the ConversationFlow ID and the value is
            the message text.
        """
        return dict(
            ConversationFlow.objects.filter(
                topic_id=topic_id,
                is_promotional=False,
            ).values_list("id", "message")
        )
