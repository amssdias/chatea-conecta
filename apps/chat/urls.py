from django.urls import path
from django.views.generic import TemplateView

from apps.chat.views.chat_view import ChatView
from apps.chat.views.close_chat_view import CloseChatView

app_name = "chat"

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("live-chat/", ChatView.as_view(), name="live-chat"),
    path("close-chat/", CloseChatView.as_view(), name="close-chat"),
]
