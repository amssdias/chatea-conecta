from django.test import TestCase
from django.urls import reverse


class TestHomeChatView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse("chat:home")
        return super().setUpTestData()

    def test_GET_home_view_status_code(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_GET_home_view_template_used(self):
        response = self.client.get(self.register_url)
        self.assertTemplateUsed(response, "index.html")

    def _test_GET_home_view_cookies_with_username(self):
        response = self.client.get(self.register_url, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)