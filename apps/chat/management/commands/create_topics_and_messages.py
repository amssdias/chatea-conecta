import boto3
import json

from django.core.management.base import BaseCommand

from apps.chat.models import Topic, ConversationFlow


class Command(BaseCommand):
    help = "Creates topics and messages from a JSON file stored in S3"

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

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="topic_messages.json",
            help="Specify the file path to import data from.",
        )

        parser.add_argument(
            "--bucket",
            type=str,
            default=None,
            help="Specify the S3 bucket name.",
        )

    def get_file_from_s3(self, s3_file_key, bucket_name):
        """
        Downloads the JSON file from S3 and returns its content.
        """
        s3 = boto3.client("s3")
        try:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Downloading {s3_file_key} from bucket {bucket_name}..."
                )
            )
            obj = s3.get_object(Bucket=bucket_name, Key=s3_file_key)
            file_content = obj["Body"].read().decode("utf-8")
            return json.loads(file_content)

        except s3.exceptions.NoSuchKey:
            self.stderr.write(
                self.style.ERROR(
                    f"The file {s3_file_key} does not exist in bucket {bucket_name}."
                )
            )
            raise

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"An error occurred while downloading the file: {str(e)}"
                )
            )
            raise

    def handle(self, *args, **options):
        file_path = options["file"]
        bucket = options["bucket"]

        data = self.get_file_from_s3(file_path, bucket)

        for topic_name, messages in data.items():
            topic, created = Topic.objects.get_or_create(name=topic_name)
            conversation_flow_messages = set(
                ConversationFlow.objects.filter(topic=topic).values_list(
                    "message", flat=True
                )
            )
            conversation_topics = []
            for message, is_promotional in messages:
                if message in conversation_flow_messages:
                    continue

                conversation_topics.append(
                    ConversationFlow(
                        topic=topic, message=message, is_promotional=is_promotional
                    )
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(conversation_topics)} messages of topic -> {topic.name}"
                )
            )
            ConversationFlow.objects.bulk_create(conversation_topics)
