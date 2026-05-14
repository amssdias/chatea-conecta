from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


class CloseChatSessionView(LogoutView):
    next_page = reverse_lazy("chat:home")
    redirect_field_name = None

    def post(self, request, *args, **kwargs):
        username = self.get_chat_username(request)

        if username:
            self.remove_username_from_redis(username=username)

        response = super().post(request, *args, **kwargs)

        response.delete_cookie("username")
        response.delete_cookie("user_id")
        response["X-Robots-Tag"] = "noindex, nofollow"

        return response

    @staticmethod
    def get_chat_username(request):
        cookie_username = request.COOKIES.get("username", "").strip()

        if cookie_username:
            return cookie_username

        if request.user.is_authenticated:
            return request.user.username

        return ""

    @staticmethod
    def remove_username_from_redis(username):
        if RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username):
            RedisService.remove_from_set(REDIS_ALL_USERNAMES_KEY, username)
