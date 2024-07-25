from django.test import SimpleTestCase
from django.urls import reverse, resolve

from apps.chat.views import ChatView, CloseChatSessionView, HomeChatView


class UrlsTestCase(SimpleTestCase):
    def test_home_url_resolves(self):
        url = reverse("chat:home")
        view_class = resolve(url).func.view_class
        self.assertEqual(view_class, HomeChatView)

    def test_login_url_resolves(self):
        url = reverse("chat:live-chat")
        view_class = resolve(url).func.view_class
        self.assertEqual(view_class, ChatView)

    def test_logout_url_resolves(self):
        url = reverse("chat:close-chat")
        view_class = resolve(url).func.view_class
        self.assertEqual(view_class, CloseChatSessionView)
