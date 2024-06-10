from django.shortcuts import redirect
from django.views import View

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.utils.redis_connection import redis_connection


class CloseChatView(View):

    def post(self, request):
        username = request.COOKIES.get("username", "")
        if not username:
            return redirect("chat:home")

        # Remove username from Redis
        lower_username = username.lower()
        if redis_connection.sismember(REDIS_USERNAME_KEY, lower_username):
            redis_connection.srem("asgi:usernames", lower_username)

        response = redirect("chat:home")
        response.delete_cookie("username")

        return response
