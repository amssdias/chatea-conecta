from django.shortcuts import redirect
from django.views import View

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.services import RedisService


class CloseChatSessionView(View):

    def post(self, request):
        username = request.COOKIES.get("username", "")
        if not username:
            return redirect("chat:home")

        self.remove_username_from_redis(username=username)

        response = redirect("chat:home")
        response.delete_cookie("username")

        return response

    @staticmethod
    def remove_username_from_redis(username):
        if RedisService.is_member(REDIS_USERNAME_KEY, username):
            RedisService.remove_from_set(REDIS_USERNAME_KEY, username)
