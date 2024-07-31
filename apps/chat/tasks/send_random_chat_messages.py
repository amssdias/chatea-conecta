from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.chat.services import MessageService
from chat_connect.celery import app
import time
import random


@app.task
def send_random_messages(group):
    service = MessageService()
    channel_layer = get_channel_layer()

    for _ in range(15):
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
