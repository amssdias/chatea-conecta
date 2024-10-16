import logging
import random
from typing import Optional, Dict, Set

from django.contrib.auth import get_user_model

from apps.chat.models import UserConversation
from apps.chat.services import DjangoCacheService

User = get_user_model()

logger = logging.getLogger("chat_connect")


class MessageService:

    def __init__(self):
        self.django_cache = DjangoCacheService()

    def get_message_to_send(self) -> Optional[Dict]:
        user_ids = self.django_cache.get_cached_user_ids()
        topic_ids = self.django_cache.get_cached_topic_ids()
        topics_ids_to_choose = topic_ids.copy()
        user_message = {
            "username": None,
            "message": None,
        }

        while True:

            user_id = self._get_random_user_id(user_ids)
            if not user_id:
                logger.info("No more users found to send a message.")
                return None

            # Get a random topic
            topic_id = self._get_random_topic_id(topics_ids_to_choose)
            if not topic_id:
                user_ids.remove(user_id)
                topics_ids_to_choose = topic_ids.copy()
                continue

            # Preload all user conversations for the current topic and user in one query
            user_conversations = set(
                UserConversation.objects.filter(
                    user_id=user_id, conversation_flow__topic_id=topic_id
                ).values_list("conversation_flow_id", flat=True)
            )

            # Get all conversation flows for the topic in one query
            conversations_flows = self.django_cache.get_cached_conversation_flows(
                topic_id
            )

            # Loop through conversation flows and check if user has sent a message for this flow
            for conversation_flow in conversations_flows:

                # If the user already sent a message for this conversation flow, skip it
                if conversation_flow.id in user_conversations:
                    continue

                # If user did not send message yet, send message from this topic
                user_message["message"] = conversation_flow.message
                user_message["username"] = self.django_cache.get_username(user_id)

                # Create the user conversation record
                UserConversation.objects.create(
                    conversation_flow=conversation_flow,
                    user_id=user_id,
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
    def _get_random_user_id(user_ids: Set) -> int:
        return random.choice(list(user_ids)) if user_ids else None

    @staticmethod
    def _get_random_topic_id(topics_ids: Set) -> int:
        return random.choice(list(topics_ids)) if topics_ids else None
