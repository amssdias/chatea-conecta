from django.urls import path
from django.views.generic import TemplateView

from apps.chat.views.chat import ChatView
from apps.chat.views.close_chat_session import CloseChatSessionView
from apps.chat.views.home_chat import HomeChatView


app_name = "chat"

urlpatterns = [
    path("", HomeChatView.as_view(), name="home"),
    path("faq/", TemplateView.as_view(template_name="pages/faq.html"), name="faq"),
    path("privacy-policy/", TemplateView.as_view(template_name="pages/privacy.html"), name="privacy"),
    path("live-chat/", ChatView.as_view(), name="live-chat"),
    path("close-chat/", CloseChatSessionView.as_view(), name="close-chat"),
]
