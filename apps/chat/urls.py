from django.urls import path
from django.views.generic import TemplateView

from apps.chat.views.chat import ChatView
from apps.chat.views.contact import ContactView
from apps.chat.views.content import ContentPageView
from apps.chat.views.home_chat import HomeChatView

app_name = "chat"

urlpatterns = [
    path("", HomeChatView.as_view(), name="home"),
    # ContentPageView, not TemplateView: the FAQ sidebar shows the live headcount.
    path("faq/", ContentPageView.as_view(template_name="pages/faq.html"), name="faq"),
    path("privacy-policy/", TemplateView.as_view(template_name="pages/privacy.html"), name="privacy"),
    path("terms/", TemplateView.as_view(template_name="pages/terms.html"), name="terms"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    # ContactView, not TemplateView: the page carries a working message form.
    path("contact/", ContactView.as_view(), name="contact"),
    path("security/", TemplateView.as_view(template_name="pages/security.html"), name="security"),
    path("live-chat/", ChatView.as_view(), name="live-chat"),
]
