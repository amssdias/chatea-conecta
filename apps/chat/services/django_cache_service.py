import logging
from typing import Set

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from faker import Faker

from apps.chat.constants.redis_keys import USER_IDS, TOPIC_IDS
from apps.chat.models import Topic, ConversationFlow

User = get_user_model()
fake = Faker()

logger = logging.getLogger("chat_connect")


class DjangoCacheService:
    USER_MESSAGE_SENT = "user_{user_id}_topic_{topic_id}_message_{message_id}"

    def _get_or_set_cache(
        self, cache_key: str, fetch_function, timeout: int = 300
    ) -> Set[int]:
        """Generic method to get from cache or fetch from DB and cache the result."""
        cached_data = cache.get(cache_key)
        if not cached_data:
            cached_data = fetch_function()
            cache.set(cache_key, cached_data, timeout)
        return cached_data

    def get_cached_user_ids(self) -> Set[int]:
        """Retrieve cached user IDs, or fetch from DB and cache."""
        return self._get_or_set_cache(
            cache_key=USER_IDS,
            fetch_function=lambda: set(User.objects.all().values_list("id", flat=True)),
            timeout=settings.CACHE_TIMEOUT_ONE_DAY,
        )

    def get_cached_topic_ids(self) -> Set[int]:
        """Retrieve cached topic IDs, or fetch from DB and cache."""
        return self._get_or_set_cache(
            cache_key=TOPIC_IDS,
            fetch_function=lambda: set(
                Topic.objects.all().values_list("id", flat=True)
            ),
            timeout=settings.CACHE_TIMEOUT_ONE_DAY,
        )

    def get_cached_conversation_flows(self, topic_id: int):
        """Retrieve cached conversation flows for a topic, or fetch and cache."""
        cache_key = f"conversation_flows_topic_{topic_id}"
        return self._get_or_set_cache(
            cache_key=cache_key,
            fetch_function=lambda: list(
                ConversationFlow.objects.filter(topic_id=topic_id)
            ),
            timeout=settings.CACHE_TIMEOUT_ONE_DAY,
        )

    def get_username(self, user_id: int) -> str:
        """Retrieve cached username or fetch from DB and cache it."""
        cache_key = f"username_{user_id}"
        username = cache.get(cache_key)
        if not username:
            try:
                username = User.objects.get(id=user_id).username
            except User.DoesNotExist:
                new_user = User.objects.create(username=fake.user_name())
                logger.warning(
                    f"Username not found, created new one with id: {new_user.id}"
                )
                username = new_user.username
            cache.set(cache_key, username, timeout=settings.CACHE_TIMEOUT_ONE_MONTH)
        return username

    @staticmethod
    def get_or_create_cache(
        cache_key, model_class, get_or_create_kwargs, timeout=60 * 60 * 24
    ):
        """
        Retrieves an object from the cache or gets it from the database and sets the cache.

        :param cache_key: Key to identify the object in cache.
        :param model_class: Django model class to query.
        :param get_or_create_kwargs: Dict of fields to use with get_or_create.
        :param timeout: Cache timeout in seconds.
        :return: Model instance.
        """
        obj = cache.get(cache_key)

        if not obj:
            obj, _ = model_class.objects.get_or_create(**get_or_create_kwargs)
            cache.set(cache_key, obj, timeout)

        return obj

    def has_user_sent_message(
        self, user_id: int, topic_id: int, message_id: int
    ) -> bool:
        """Check if a user has already sent a specific message for a given topic."""
        cache_key = self.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        return cache.get(cache_key) is not None

    def mark_user_message_sent_in_redis(
        self, user_id: int, topic_id: int, message_id: int, message: str
    ):
        """
        Mark a message as sent by a user for a specific topic in Redis, with an expiration (TTL).
        Each message is stored as a separate key, with a unique expiration time.
        """

        # Create a unique cache key for this user, topic, and message
        cache_key = self.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )

        # Store the message in Redis with a TTL (time-to-live)
        cache.set(cache_key, message, timeout=settings.CACHE_TIMEOUT_ONE_DAY)
