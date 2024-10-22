from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse
from django.contrib import messages

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY

@patch("apps.chat.views.chat.RedisService.is_member", autospec=True)
@patch("apps.chat.views.chat.RedisService.add_to_set", autospec=True)
class ChatViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("chat:live-chat")
        cls.username = "testuser"

    def setUp(self):
        self.client = Client()

    def test_get_request_no_username_cookie(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("chat:home"))
        self.assertEqual(response.cookies.get("username").get("value"), None)

        mock_is_member.assert_not_called()

    def test_get_request_invalid_username_redis(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        self.client.cookies["username"] = self.username
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("chat:home"))
        self.assertEqual(response.cookies.get("username").get("value"), None)

        mock_is_member.assert_called_once_with(REDIS_USERNAME_KEY, self.username)

    def test_get_request_valid_username(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = True
        self.client.cookies["username"] = self.username
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")

        context = response.context
        self.assertEqual(context["username"], self.username)
        self.assertIsNone(context["groups"])

        mock_is_member.assert_called_once_with(REDIS_USERNAME_KEY, self.username)

    def test_get_request_ensure_groups_context(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = True
        self.client.cookies["username"] = self.username
        response = self.client.get(self.url)
        context = response.context
    
        self.assertIsNone(context["groups"])

    def test_get_request_when_username_cookie_is_present(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = True
        self.client.cookies["username"] = "anotheruser"
        response = self.client.get(self.url)
    
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], "anotheruser")
    
        mock_is_member.assert_called_once_with(REDIS_USERNAME_KEY, "anotheruser")

    def test_post_request_missing_username(self, mock_add_to_set, mock_is_member):
        response = self.client.post(self.url, {})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "You need to put an username",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )

        mock_is_member.assert_not_called()

    def test_post_request_username_taken(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = True
        response = self.client.post(self.url, {"username": self.username})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username already taken",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )

        mock_is_member.assert_called_once_with(REDIS_USERNAME_KEY, self.username)

    def test_post_request_successful_username_addition(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        response = self.client.post(self.url, {"username": self.username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, self.username)

        mock_add_to_set.assert_called_once_with(REDIS_USERNAME_KEY, self.username)
        mock_is_member.assert_called_once_with(REDIS_USERNAME_KEY, self.username)

    def test_post_request_username_with_spaces(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        response = self.client.post(self.url, {"username": "  userwithspaces  "})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, "userwithspaces")

        mock_add_to_set.assert_called_once_with(REDIS_USERNAME_KEY, "userwithspaces")

    def test_post_request_username_case_sensitivity(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        username = "NewUser"
        response = self.client.post(self.url, {"username": username})

        username_lower = username.lower()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_add_to_set.assert_called_once_with(REDIS_USERNAME_KEY, username_lower)
        mock_is_member.assert_called_once_with(REDIS_USERNAME_KEY, username_lower)

    def test_post_request_empty_username_field(self, mock_add_to_set, mock_is_member):
        response = self.client.post(self.url, {"username": ""})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "You need to put an username",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )

        mock_is_member.assert_not_called()

    def test_post_request_special_characters_in_username(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        username = "user@!$"
        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_add_to_set.assert_called_once_with(REDIS_USERNAME_KEY, username)
