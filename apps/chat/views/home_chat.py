import random

from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService
from apps.chat.services.guest_session import GUEST_SESSION_COOKIE, read_guest_token


class HomeChatView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if self.has_chat_session(request):
            return redirect("chat:live-chat")
        return super().get(request, args, kwargs)

    @staticmethod
    def has_chat_session(request):
        """
        Signature check only: whether the guest still owns the nickname is for
        ChatView to decide, and the landing page should not hit Redis for it.
        """
        token = request.COOKIES.get(GUEST_SESSION_COOKIE, "")

        if read_guest_token(token) is not None:
            return True

        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        n_persons = RedisService.get_group_size(REDIS_ALL_USERNAMES_KEY)
        context["n_persons"] = n_persons if n_persons > 5 else random.randint(55, 63)
        return context
