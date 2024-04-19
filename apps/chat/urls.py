from django.urls import path
from django.views.generic import TemplateView

from apps.chat.views.chat_view import ChatView

app_name = "chat"

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("live-chat/", ChatView.as_view(), name="live-chat"),
]
