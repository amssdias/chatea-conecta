from django.contrib.auth.models import UserManager

from apps.users.models import Profile


class CustomUserManager(UserManager):
    def create_user_with_profile(self, username, profile_data=None, **extra_fields):
        """We create this manager with this method, because with signals we cannot pass arguments in a easy way"""
        user = self.create_user(username=username, **extra_fields)
        Profile.objects.create(user=user, **(profile_data or {}))
        return user
