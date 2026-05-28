from django.contrib.auth.models import AbstractUser

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.users.models.managers.user_manager import CustomUserManager


class User(AbstractUser):
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @property
    def is_pro(self):
        return self.subscription.pro

    @property
    def needs_payment_configuration(self):
        return self.subscription.status == UserSubscriptionStatus.PAST_DUE
