from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse


@patch("apps.chat.views.close_chat_session.redis_connection", autospec=True)
class TestCloseChatSessionView(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("chat:close-chat")
    
    def setUp(self):
        self.client = Client()

    def test_redirect_when_no_username_cookie(self, mock_redis):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("chat:home"))
        mock_redis.sismember.assert_not_called()

    def test_remove_username_from_redis_called(self, mock_redis):
        mock_redis.sismember.return_value = True
        self.client.cookies["username"] = "testuser"
        self.client.post(self.url)
        mock_redis.srem.assert_called_once_with("asgi:usernames", "testuser")

    def test_username_cookie_deleted(self, mock_redis):
        mock_redis.sismember.return_value = False
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)

        cookie = response.cookies.get('username')
        self.assertIsNone(cookie.get("value"))

    def test_no_remove_when_username_not_in_redis(self, mock_redis):
        mock_redis.sismember.return_value = False
        self.client.cookies["username"] = "testuser"
        self.client.post(self.url)
        mock_redis.srem.assert_not_called()

    def test_redirect_when_username_cookie_present(self, mock_redis):
        mock_redis.sismember.return_value = False
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("chat:home"))

    def test_username_lowercased(self, mock_redis):
        mock_redis.sismember.return_value = True
        self.client.cookies["username"] = "TestUser"
        self.client.post(self.url)
        mock_redis.srem.assert_called_once_with("asgi:usernames", "testuser")

    def test_redirect_status_code(self, mock_redis):
        mock_redis.sismember.return_value = False
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_invalid_redis_key(self, mock_redis):
        mock_redis.sismember.return_value = True
    
        self.client.cookies["username"] = "testuser"
        response = self.client.post(self.url)
    
        # Verify that srem was called correctly
        mock_redis.srem.assert_called_once_with("asgi:usernames", "testuser")
        self.assertEqual(response.status_code, 302)

    def test_multiple_users(self, mock_redis):
        mock_redis.sismember.return_value = True
        self.client.cookies["username"] = "user1"
        self.client.post(self.url)
        mock_redis.srem.assert_called_once_with("asgi:usernames", "user1")

        self.client.cookies["username"] = "user2"
        self.client.post(self.url)
        self.assertEqual(mock_redis.srem.call_count, 2)
