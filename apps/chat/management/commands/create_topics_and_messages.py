import json

from django.core.management.base import BaseCommand
from apps.chat.models import Topic, ConversationFlow


class Command(BaseCommand):
    help = "Creates topics and messages"
    file_path = "apps/chat/management/data/topic_messages.json"

    """
        Command to process and save conversation flows from a JSON file.
        
        The command expects a JSON file containing conversation data for multiple topics. 
        Each topic should be a key in the JSON object, with its value being a list of lists. 
        Each inner list should contain two elements:
        1. A message string.
        2. A boolean indicating whether the message is promotional (e.g., designed to draw additional attention or include external content).
        
        ### File Format Example
        
        {
          "greeting": [
            ["Good morning, how is everyone?", false],
            ["Don't miss out on our latest updates: {}", true]
          ],
          "location": [
            ["Where are you joining us from today?", false],
            ["Check out local events happening near you: {}", true]
          ],
          "activity": []
        }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        with open(self.file_path, "r", encoding="utf-8") as file:
            # Load the JSON data
            data = json.load(file)

        for topic_name, messages in data.items():

            topic, created = Topic.objects.get_or_create(name=topic_name)

            conversation_flow_messages = set(ConversationFlow.objects.filter(topic=topic).values_list("message", flat=True))
            conversation_topics = []
            for message, is_promotional in messages:
                if message in conversation_flow_messages:
                    continue

                conversation_topics.append(
                    ConversationFlow(topic=topic, message=message, is_promotional=is_promotional)
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(conversation_topics)} messages of topic -> {topic.name}"
                )
            )
            ConversationFlow.objects.bulk_create(conversation_topics)
