import logging
from datetime import timedelta

from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django.utils import timezone

from apps.chat.models import UserConversation
from chat_connect.celery import app


logger = logging.getLogger("chat_connect")


@app.task
def clear_user_old_messages():
    logger.info("Starting 'clear_user_old_messages' task.")
    expiration_time = timezone.now() - timedelta(minutes=settings.CLEAR_MESSAGES_EXPIRATION_TIME)

    if not UserConversation.objects.exists():
        logger.info("No user conversations found. Disabling the periodic task 'clear_users_bots_messages'.")

        # DB is empty, signal to stop this task
        task, _ = PeriodicTask.objects.get_or_create(
            name="clear_users_bots_messages",
        )

        if task.enabled:
            task.enabled = False
            task.save()
            logger.info("Periodic task 'clear_users_bots_messages' has been disabled.")
        return True


    user_messages = UserConversation.objects.filter(created_at__lt=expiration_time)
    n_user_messages = user_messages.count()

    if n_user_messages > 0:
        user_messages.delete()
        logger.info(f"Deleted {n_user_messages} user messages older than {expiration_time}.")
    else:
        logger.info(f"No messages older than {expiration_time} found. No deletions performed.")


    logger.info(f"Deleted {n_user_messages} user messages.")