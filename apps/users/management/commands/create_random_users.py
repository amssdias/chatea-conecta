import boto3
import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.chat.tasks.send_random_chat_messages import logger

User = get_user_model()


class Command(BaseCommand):
    help = "Creates random users from a JSON file, either locally or from S3"

    def __init__(self, *args, **kwargs):
        self.users_created = 0
        self.users_not_created = 0
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="random_users.json",
            help="Specify the file path to import user data from.",
        )
        parser.add_argument(
            "--bucket",
            type=str,
            default=None,
            help="Specify the S3 bucket name.",
        )

    def get_file_content(self, s3_file_key, bucket_name=None):
        """
        Retrieves file content from local or S3, depending on the parameters.
        """
        self.stdout.write(
            self.style.SUCCESS(
                f"Downloading {s3_file_key} from bucket {bucket_name}..."
            )
        )
        s3 = boto3.client("s3")
        try:
            obj = s3.get_object(Bucket=bucket_name, Key=s3_file_key)
            return json.loads(obj["Body"].read().decode("utf-8"))
        except s3.exceptions.NoSuchKey:
            self.stderr.write(
                self.style.ERROR(
                    f"The file {s3_file_key} does not exist in bucket {bucket_name}."
                )
            )
            raise
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Failed to fetch file from S3: {str(e)}")
            )
            raise

    def handle(self, *args, **options):
        file_path = options["file"]
        bucket = options["bucket"]

        # Get file content
        data = self.get_file_content(file_path, bucket)

        # Process the JSON data
        users = data.get("users", [])
        for user in users:
            try:
                profile_data = {
                    "gender": user["gender"],
                    **({"link": user["link"]} if "link" in user else {}),
                }

                User.objects.create_user_with_profile(
                    username=user["username"], profile_data=profile_data
                )
                self.users_created += 1
            except Exception as e:
                logger.error(e)
                self.users_not_created += 1

        # Output results
        self.stdout.write(self.style.SUCCESS(f"Created {self.users_created} users"))
        if self.users_not_created:
            self.stdout.write(
                self.style.NOTICE(f"Not created {self.users_not_created} users")
            )
