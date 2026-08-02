from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService
from apps.chat.services.guest_session import (
    GUEST_SESSION_COOKIE,
    read_guest_token,
    revoke_guest_identity,
)


class CloseChatSessionView(LogoutView):
    next_page = reverse_lazy("chat:home")
    redirect_field_name = None

    def post(self, request, *args, **kwargs):
        username, user_id = self.get_chat_identity(request)

        if username:
            self.remove_username_from_redis(username=username)
            revoke_guest_identity(username, user_id)

        response = super().post(request, *args, **kwargs)

        response.delete_cookie(GUEST_SESSION_COOKIE)
        response.delete_cookie("username")
        response.delete_cookie("user_id")
        response["X-Robots-Tag"] = "noindex, nofollow"

        return response

    @staticmethod
    def get_chat_identity(request):
        """
        Return the (username, user_id) whose chat session is being closed.

        Guests are identified by their signed token only, so a forged cookie
        cannot free somebody else's nickname or revoke their identity.
        """
        identity = read_guest_token(request.COOKIES.get(GUEST_SESSION_COOKIE, ""))

        if identity:
            return identity

        if request.user.is_authenticated:
            return request.user.username, str(request.user.pk)

        return "", ""

    @staticmethod
    def remove_username_from_redis(username):
        if RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username):
            RedisService.remove_from_set(REDIS_ALL_USERNAMES_KEY, username)
