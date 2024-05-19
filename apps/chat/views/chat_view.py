from django.conf import settings

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.utils.redis_connection import redis_connection


class ChatView(View):
    def get(self, request):
        username = self.request.COOKIES.get("username", "")
        if not username:
            return redirect("chat:home")

        return render(request, "chat/chat.html", context={"username": username})

    def post(self, request):
        username = request.POST.get("username")
        if not username:
            messages.error(request, "You need to put an username")
            # Redirect to home page
            return redirect("chat:home")

        # Check if username already exists in Redis
        lower_username = username.lower()
        if redis_connection.sismember(REDIS_USERNAME_KEY, lower_username):
            messages.error(request, "Username already taken")
            return redirect("chat:home")

        # Add the username to the Redis set
        redis_connection.sadd("asgi:usernames", lower_username)

        response = render(request, "chat/chat.html", context={"username": username})
        response.set_cookie("username", username, httponly=True, secure=settings.COOKIES_SECURE)
        return response
