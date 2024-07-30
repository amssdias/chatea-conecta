import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()

class Command(BaseCommand):
    help = "Creates random users"
    file_path = "apps/chat/management/data/random_users.json"

    def __init__(self, *args, **kwargs):
        self.users_created = 0
        self.users_not_created = 0
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options):
        with open(self.file_path, "r", encoding="utf-8") as file:
            # Load the JSON data
            data = json.load(file)

        users = data.get("users", [])
        for user in users:
            try:
                User.objects.create(
                    username=user
                )
                self.users_created += 1
            except Exception as e:
                self.users_not_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {self.users_created} users"
            )
        )
        if self.users_not_created:
            self.stdout.write(
                self.style.NOTICE(
                    f"Not created {self.users_not_created} users"
                )
            )
