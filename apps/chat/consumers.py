import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        print("---- CONNECTED ----")
        print(f"scope: {self.scope}")
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name.lower()}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        print("RECEIVED MESSAGE FROM FRONTEND")

        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print(f"MESSAGE: {text_data_json}")

        username = self.scope["cookies"].get("username")
        if not username:
            self.disconnect(1234)
            return

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                "username": username,
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        # Send message to WebSocket (frontend)
        self.send(text_data=json.dumps({"message": message, "username": username}))
