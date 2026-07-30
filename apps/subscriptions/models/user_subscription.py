from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.subscriptions.models.choices import UserSubscriptionStatus


class UserSubscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    status = models.CharField(
        max_length=20,
        choices=UserSubscriptionStatus.choices,
        default=UserSubscriptionStatus.INACTIVE,
    )

    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)

    started_at = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)

    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def pro(self):
        if self.status == UserSubscriptionStatus.ACTIVE:
            return (
                not self.current_period_end or self.current_period_end > timezone.now()
            )

        if (
                self.status == UserSubscriptionStatus.PAST_DUE
                and self.current_period_end
                and self.current_period_end > timezone.now()
        ):
            return True

        return False
