from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.chat.services.guest_session import GUEST_SESSION_COOKIE, issue_guest_token
from apps.chat.views import HomeChatView


class TestHomeChatView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse("chat:home")
        cls.factory = RequestFactory()
        return super().setUpTestData()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_GET_home_view_status_code(self, mock_get_group_size):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_GET_home_view_template_used(self, mock_get_group_size):
        response = self.client.get(self.register_url)
        self.assertTemplateUsed(response, "index.html")

    def test_redirect_when_guest_session_cookie_present(self):
        request = self.factory.get(self.register_url)
        request.COOKIES[GUEST_SESSION_COOKIE] = issue_guest_token("testuser", "u_00001")
        response = HomeChatView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("chat:live-chat"))

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_no_redirect_when_the_guest_session_cookie_is_not_signed(self, mock_get_group_size):
        self.client.cookies[GUEST_SESSION_COOKIE] = "testuser:u_00001"

        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_no_redirect_when_only_a_plaintext_username_cookie_is_present(self, mock_get_group_size):
        self.client.cookies["username"] = "testuser"

        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
