import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY, ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService

User = get_user_model()


class ChatView(View):
    def get(self, request):
        username = self.request.COOKIES.get("username", "")
        user_id = self.request.COOKIES.get("user_id", "")
        if (
                not username or
                not user_id or
                not RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username)
        ):
            response = redirect("chat:home")
            response.delete_cookie("username")
            response.delete_cookie("user_id")
            return response

        user_id = RedisService.get_key(USERNAME_TO_UUID_KEY.format(username=username))
        return render(
            request, "chat/chat.html", context={"username": username, "user_id": user_id, "groups": None}
        )

    def post(self, request):
        username = request.POST.get("username", "").strip()
        if not username:
            messages.error(request, _("You need to put an username"))
            return redirect("chat:home")

        USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_-]{3,20}$")
        if not USERNAME_REGEX.fullmatch(username):
            messages.error(
                request,
                _("Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'"),
            )
            return redirect("chat:home")

        # Check if username already exists in Redis
        if (
                RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username) or
                User.objects.filter(username__iexact=username).exists()
        ):
            messages.error(request, _("Username already taken"))
            return redirect("chat:home")

        # Add the username to the Redis set and unique ID
        user_id = RedisService.create_user_id()
        RedisService.add_to_set(REDIS_ALL_USERNAMES_KEY, username.lower())
        RedisService.set_unique(ID_TO_USERNAME_KEY.format(user_id=user_id), username)
        RedisService.set_unique(USERNAME_TO_UUID_KEY.format(username=username), user_id)

        response = render(
            request,
            "chat/chat.html",
            context={
                "username": username,
                "user_id": user_id,
            },
        )
        response.set_cookie(
            "username", username, httponly=True, secure=settings.COOKIES_SECURE
        )
        response.set_cookie(
            "user_id", user_id, httponly=True, secure=settings.COOKIES_SECURE
        )
        return response
