import json

from django.core.management.base import BaseCommand
from apps.chat.models import Topic, ConversationFlow


class Command(BaseCommand):
    help = "Creates topics and messages"
    file_path = "apps/chat/management/data/topic_messages.json"

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
            for message in messages:
                if message in conversation_flow_messages:
                    continue

                conversation_topics.append(
                    ConversationFlow(topic=topic, message=message)
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(conversation_topics)} messages of topic -> {topic.name}"
                )
            )
            ConversationFlow.objects.bulk_create(conversation_topics)
