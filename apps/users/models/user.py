from django.contrib.auth.models import AbstractUser

from apps.users.models.managers.user_manager import CustomUserManager


class User(AbstractUser):
    objects = CustomUserManager()

    def __str__(self):
        return self.email
