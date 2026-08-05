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
        """
        Grant Pro only for a paid status backed by a future period end.

        A missing ``current_period_end`` is treated as no entitlement rather than an
        unbounded one: it means the period could not be read from Stripe, and an
        unbounded read would turn that failure into permanent free Pro.
        """
        if self.status not in {
            UserSubscriptionStatus.ACTIVE,
            UserSubscriptionStatus.PAST_DUE,
        }:
            return False

        return bool(
            self.current_period_end and self.current_period_end > timezone.now()
        )
