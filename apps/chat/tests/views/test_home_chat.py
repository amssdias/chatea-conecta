from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.chat.views import HomeChatView


class TestHomeChatView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse("chat:home")
        cls.factory = RequestFactory()
        return super().setUpTestData()

    def test_GET_home_view_status_code(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_GET_home_view_template_used(self):
        response = self.client.get(self.register_url)
        self.assertTemplateUsed(response, "index.html")

    def test_redirect_when_username_cookie_present(self):
        request = self.factory.get(self.register_url)
        request.COOKIES["username"] = "testuser"
        response = HomeChatView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("chat:live-chat"))
