import random
from typing import List, Optional, Dict

from channels.db import database_sync_to_async
from apps.chat.models import UserConversation, ConversationFlow, Topic
from django.contrib.auth import get_user_model

User = get_user_model()


class DatabaseQueries:
    # Celery beat will work with a DB flag
    # If there are still users on the DB, we will continue to send messages
    # If there are no users, we stop sending messages

    @database_sync_to_async
    def get_message_to_send(self) -> Optional[Dict]:
        user_ids = set(User.objects.all().values_list("id", flat=True))
        topics_ids = set(Topic.objects.all().values_list("id", flat=True))
        topics_ids_to_choose = topics_ids.copy()
        user_message = {
            "username": None,
            "message": None,
        }

        while True:

            # Get random user
            user_id = self._get_random_user_id(user_ids)
            if not user_id:
                return None

            # Get a random topic
            topic_id = self._get_random_topic_id(topics_ids_to_choose)
            if not topic_id:
                user_ids.remove(user_id)
                topics_ids_to_choose = topics_ids.copy()
                continue

            # Get messages from this topic
            conversations_flows = ConversationFlow.objects.filter(
                topic_id=topic_id
            ).prefetch_related("user_conversation")

            # Loop through all messages
            for conversation_flow in conversations_flows:

                # Check if user already sent this topic
                # if yes, get next message from this topic
                if conversation_flow.user_conversation.filter(user_id=user_id).exists():
                    continue

                else:
                    # if user did not send message yet, send message from this topic
                    user_message["message"] = conversation_flow.message
                    user_message["username"] = User.objects.get(id=user_id).username
                    # if not, send message from this topic
                    UserConversation.objects.create(
                        conversation_flow=conversation_flow,
                        user_id=user_id,
                    )
                    break

            else:
                # If user already sent all possible messages from this topic
                # Remove this topic to get another topic
                topics_ids_to_choose.remove(topic_id)
                continue

            break

        return user_message

    @staticmethod
    def _get_random_user_id(user_ids: List) -> int:
        return random.choice(list(user_ids)) if user_ids else None

    @staticmethod
    def _get_random_topic_id(topics_ids: List) -> int:
        return random.choice(list(topics_ids)) if topics_ids else None
