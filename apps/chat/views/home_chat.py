import random

from django.shortcuts import redirect
from django.views.generic import TemplateView

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.services import RedisService


class HomeChatView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        username = self.request.COOKIES.get("username", "")
        if username:
            return redirect("chat:live-chat")
        return super().get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        n_persons = RedisService.get_group_size(REDIS_USERNAME_KEY)
        context["n_persons"] = n_persons if n_persons > 5 else random.randint(55, 63)
        return context
