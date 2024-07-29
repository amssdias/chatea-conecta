from django.db import models


class ConversationFlow(models.Model):
    """
    Represents a message in the conversation flow for a specific topic.

    Attributes:
        topic (ForeignKey): The topic to which this conversation flow belongs.
        message (CharField): The content of the message, with a maximum length of 300 characters.
    """

    topic = models.ForeignKey(
        "Topic", related_name="conversation_flows", on_delete=models.CASCADE
    )
    message = models.CharField(max_length=300)

    def __str__(self):
        return f"{self.topic.name} - {self.message}"
