from __future__ import annotations

from celery import shared_task
from django.contrib.auth import get_user_model

from apps.subscriptions.emails import send_pro_subscription_canceled_email

User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_subscription_canceled_email_task(
    self,
    user_id: int,
    ended_at=None,
):
    """Send the cancellation email and retry transient delivery failures."""
    user = User.objects.get(id=user_id)
    send_pro_subscription_canceled_email(user=user, ended_at=ended_at)
