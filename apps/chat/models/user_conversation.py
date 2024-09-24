from django.db import models
from django.conf import settings


class UserConversation(models.Model):
    """
    Tracks a user's progress in a conversation flow.

    Attributes:
        user (ForeignKey): The user engaged in the conversation.
        conversation_flow (ForeignKey): The current conversation flow message the user is at.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="conversations", on_delete=models.CASCADE
    )
    conversation_flow = models.ForeignKey(
        "ConversationFlow", related_name="user_conversation", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

