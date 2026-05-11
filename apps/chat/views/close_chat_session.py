from django.shortcuts import redirect
from django.views import View

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


class CloseChatSessionView(View):

    @staticmethod
    def _add_noindex_header(response):
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    def post(self, request):
        username = request.COOKIES.get("username", "")
        if not username:
            response = redirect("chat:home")
            return self._add_noindex_header(response)

        self.remove_username_from_redis(username=username)

        response = redirect("chat:home")
        response.delete_cookie("username")

        return self._add_noindex_header(response)

    @staticmethod
    def remove_username_from_redis(username):
        if RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username):
            RedisService.remove_from_set(REDIS_ALL_USERNAMES_KEY, username)
