from __future__ import annotations

import random
from typing import TypedDict

from apps.chat.infrastructure.redis.bot_message_redis_store import (
    BotMessageRedisStore,
)
from apps.chat.services.bots.bot_cache_loader import BotCacheLoader


class BotMessage(TypedDict):
    user_id: int
    username: str
    topic_id: int
    message_id: int
    message: str


class BotMessageService:
    """
    Selects the next automatic bot message to send to the public chat.

    This service contains the selection logic, but it does not query the
    database directly. Database loading is delegated to BotCacheLoader, and
    Redis access is delegated to BotMessageRedisStore.
    """

    MAX_TOPIC_ATTEMPTS = 10

    def __init__(
            self,
            redis_store: BotMessageRedisStore | None = None,
            cache_loader: BotCacheLoader | None = None,
    ):
        self.redis_store = redis_store or BotMessageRedisStore()
        self.cache_loader = cache_loader or BotCacheLoader(
            redis_store=self.redis_store,
        )

    def get_message_to_send(self) -> BotMessage | None:
        """
        Return one bot message payload ready to be sent to the chat.

        Returns None when no valid user, topic or message is available.
        """
        self._ensure_cache_is_loaded()

        user_id = self.redis_store.get_random_bot_user_id()
        if user_id is None:
            return None

        username = self.redis_store.get_bot_username(user_id)
        if not username:
            return None

        selected_message = self._select_message()
        if selected_message is None:
            return None

        topic_id, message_id, message = selected_message

        self.redis_store.mark_message_as_sent(message_id)

        return {
            "user_id": user_id,
            "username": username,
            "topic_id": topic_id,
            "message_id": message_id,
            "message": message,
        }

    def _ensure_cache_is_loaded(self) -> None:
        """
        Load bot users, topics and messages into Redis if they are missing.
        """
        if self.redis_store.is_cache_loaded():
            return

        self.cache_loader.load()

    def _select_message(self) -> tuple[int, int, str] | None:
        """
        Select a random message that was not recently sent.

        Returns:
            Tuple with:
                topic_id
                message_id
                message
        """
        for _ in range(self.MAX_TOPIC_ATTEMPTS):
            topic_id = self.redis_store.get_random_topic_id()

            if topic_id is None:
                return None

            messages = self.redis_store.get_topic_messages(topic_id)

            if not messages:
                continue

            selected_message = self._select_unsent_message(messages)

            if selected_message is None:
                continue

            message_id, message = selected_message

            return topic_id, message_id, message

        return None

    def _select_unsent_message(self, messages: dict[int, str]) -> tuple[int, str] | None:
        """
        Select one random message that was not recently sent.

        Args:
            messages: Mapping of ConversationFlow ID to message text.

        Returns:
            Tuple with message_id and message text, or None if all messages
            were recently sent.
        """
        message_items = list(messages.items())
        random.shuffle(message_items)

        for message_id, message in message_items:
            if self.redis_store.message_was_sent(message_id):
                continue

            return message_id, message

        return None
