from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY


@patch("apps.chat.views.close_chat_session.RedisService.is_member", autospec=True)
@patch("apps.chat.views.close_chat_session.RedisService.remove_from_set", autospec=True)
class TestCloseChatSessionView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("chat:close-chat")
    
    def setUp(self):
        self.client = Client()

    @patch("apps.chat.views.close_chat_session.RedisService.get_group_size", return_value=5)
    def test_redirect_when_no_username_cookie(self, mock_get_group_size, mock_remove_from_set, mock_is_member):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("chat:home"))
        mock_is_member.assert_not_called()
        mock_remove_from_set.assert_not_called()

    def test_remove_username_from_redis_called(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = True
        self.client.cookies["username"] = "testuser"
        self.client.post(self.url)
        mock_remove_from_set.assert_called_once_with("asgi:usernames", "testuser")

    def test_username_cookie_deleted(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = False
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)

        cookie = response.cookies.get('username')
        self.assertIsNone(cookie.get("value"))

    def test_no_remove_when_username_not_in_redis(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = False
        self.client.cookies["username"] = "testuser"
        self.client.post(self.url)
        mock_remove_from_set.assert_not_called()

    @patch("apps.chat.views.close_chat_session.RedisService.get_group_size", return_value=5)
    def test_redirect_when_username_cookie_present(self, mock_get_group_size,  mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = False
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("chat:home"))

    def test_username_lowercased(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = True
        username = "TestUser"
        self.client.cookies["username"] = username
        self.client.post(self.url)
        mock_remove_from_set.assert_called_once_with(REDIS_USERNAME_KEY, username)

    def test_redirect_status_code(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = False
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_invalid_redis_key(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = True
    
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)

        mock_remove_from_set.assert_called_once_with(REDIS_USERNAME_KEY, "testuser")
        self.assertEqual(response.status_code, 302)

    def test_multiple_users(self, mock_remove_from_set, mock_is_member):
        mock_is_member.return_value = True
        self.client.cookies["username"] = "user1"
        self.client.post(self.url)
        mock_remove_from_set.assert_called_once_with(REDIS_USERNAME_KEY, "user1")

        self.client.cookies["username"] = "user2"
        self.client.post(self.url)
        self.assertEqual(mock_remove_from_set.call_count, 2)
