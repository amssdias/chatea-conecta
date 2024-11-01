from django.contrib.auth.models import BaseUserManager

from apps.users.models import Profile


class CustomUserManager(BaseUserManager):
    def create_user_with_profile(self, username, profile_data=None, **extra_fields):
        user = self.create(username=username, **extra_fields)
        Profile.objects.create(user=user, **(profile_data or {}))
        return user
