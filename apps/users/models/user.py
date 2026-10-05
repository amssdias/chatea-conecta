from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.users.models.managers.user_manager import CustomUserManager


class User(AbstractUser):
    is_bot = models.BooleanField(
        default=False,
        help_text="Designates whether this account is an automated chat bot.",
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @property
    def is_pro(self):
        subscription = getattr(self, "subscription", None)
        return bool(subscription and subscription.pro)

    @property
    def needs_payment_configuration(self):
        subscription = getattr(self, "subscription", None)
        return bool(
            subscription and subscription.status == UserSubscriptionStatus.PAST_DUE
        )
