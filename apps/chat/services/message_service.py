import logging
import random
from typing import Optional, Dict, Set

from django.contrib.auth import get_user_model

from apps.chat.services import DjangoCacheService

User = get_user_model()

logger = logging.getLogger("chat_connect")


class MessageService:

    def __init__(self):
        self.django_cache = DjangoCacheService()

    def get_message_to_send(self) -> Optional[Dict]:
        is_promotional = self._should_select_promotional_user()

        user_ids = self.django_cache.get_cached_user_ids(promotional=is_promotional)
        topic_ids = self.django_cache.get_cached_topic_ids(promotional=is_promotional)
        topics_ids_to_choose = topic_ids.copy()
        user_message = {
            "username": None,
            "message": None,
        }

        changed_users = False

        while True:

            user_id = self._get_random_user_id(user_ids)
            if not user_id:
                if not changed_users:
                    user_ids = self.django_cache.get_cached_user_ids(
                        promotional=not is_promotional
                    )
                    topic_ids = self.django_cache.get_cached_topic_ids(
                        promotional=not is_promotional
                    )
                    continue

                logger.warning("No more users found to send a message.")
                return None

            # Get a random topic
            topic_id = self._get_random_topic_id(topics_ids_to_choose)
            if not topic_id:
                user_ids.remove(user_id)
                topics_ids_to_choose = topic_ids.copy()
                continue

            # Get all conversation flows for the topic in one query
            conversations_flows = self.django_cache.get_cached_conversation_flows(
                topic_id
            )

            random.shuffle(conversations_flows)

            # Loop through conversation flows and check if user has sent a message for this flow
            for conversation_id, message in conversations_flows:

                # If the user already sent a message for this conversation flow, skip it
                if self.django_cache.has_user_sent_message(
                    user_id, topic_id, conversation_id
                ):
                    continue

                # If user did not send message yet, send message from this topic
                user_message["message"] = message
                user_message["username"] = self.django_cache.get_username(user_id)

                # Create the user conversation record on Redis
                self.django_cache.mark_user_message_sent_in_redis(
                    user_id=user_id,
                    topic_id=topic_id,
                    message_id=conversation_id,
                    message=message,
                )

                break
            else:
                # If user has sent all possible messages from this topic
                # Remove this topic to get another topic
                topics_ids_to_choose.remove(topic_id)
                continue

            break

        return user_message

    @staticmethod
    def _should_select_promotional_user() -> bool:
        """Return True with 35% chance to select a promotional user."""
        return random.choices([True, False], weights=[0.35, 0.65])[0]

    @staticmethod
    def _get_random_user_id(user_ids: Set) -> int:
        return random.choice(list(user_ids)) if user_ids else None

    @staticmethod
    def _get_random_topic_id(topics_ids: Set) -> int:
        return random.choice(list(topics_ids)) if topics_ids else None
