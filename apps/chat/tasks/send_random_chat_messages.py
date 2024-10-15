import logging
import random
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.conf import settings
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from apps.chat.caching import get_or_set_cache
from apps.chat.constants.redis_keys import HAS_USERS, TASK_LOCK_KEY
from apps.chat.services import MessageService
from apps.chat.utils.redis_connection import redis_connection
from chat_connect.celery import app

logger = logging.getLogger("chat_connect")


@app.task
def send_random_messages(group):
    logger.info(f"Starting 'send_random_messages' task for group: {group}")

    service = MessageService()
    channel_layer = get_channel_layer()

    add_clear_messages_periodic_task()

    # Make a periodic task instead of while true
    while cache.get(HAS_USERS):

        user_message = service.get_message_to_send()

        if user_message:
            time.sleep(random.randint(1, 3))
            async_to_sync(channel_layer.group_send)(
                group,
                {
                    "type": "chat.message",
                    "message": user_message.get("message"),
                    "username": user_message.get("username"),
                    "group": group,
                },
            )
            logger.info(
                f"Sent message from user '{user_message.get('username')}' to group '{group}'."
            )

    redis_connection.delete(TASK_LOCK_KEY)
    logger.info(f"'send_random_messages' task for group '{group}' completed.")
    return


def add_clear_messages_periodic_task():
    logger.info("Activating the 'clear_users_bots_messages' periodic task.")

    # Cache key for interval schedule
    interval_cache_key = f"interval_{settings.CLEAR_USER_SENT_MESSAGES_TASK_INTERVAL_SCHEDULE_MINUTES}_minutes"
    interval = get_or_set_cache(
        cache_key=interval_cache_key,
        model_class=IntervalSchedule,
        get_or_create_kwargs={
            "every": settings.CLEAR_USER_SENT_MESSAGES_TASK_INTERVAL_SCHEDULE_MINUTES,
            "period": IntervalSchedule.MINUTES
        },
        timeout=settings.CACHE_TIMEOUT_ONE_DAY
    )

    task, _ = PeriodicTask.objects.get_or_create(
        interval=interval,
        name="clear_users_bots_messages",
        task="apps.chat.tasks.clear_messages.clear_user_old_messages",
    )

    if not task.enabled:
        task.enabled = True
        task.save()
        logger.info("Enabled the 'clear_users_bots_messages' periodic task.")
