from django.shortcuts import redirect
from django.views.generic import TemplateView


class HomeChatView(TemplateView):
    def get(self, request, *args, **kwargs):
        username = self.request.COOKIES.get("username", "")
        if username:
            return redirect("chat:live-chat")
        return super().get(request, args, kwargs)

            