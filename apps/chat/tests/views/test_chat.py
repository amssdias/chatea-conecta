from unittest.mock import patch

from django.contrib import messages
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
    ID_TO_USERNAME_KEY,
    USERNAME_TO_UUID_KEY,
)
from apps.users.tests.factories.user_factory import UserFactory


@patch("apps.chat.views.chat.RedisService.is_member", autospec=True)
@patch("apps.chat.views.chat.RedisService.add_to_set", autospec=True)
class ChatViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("chat:live-chat")
        cls.username = "testuser"

    def setUp(self):
        self.client = Client()

    @patch("apps.chat.views.chat.RedisService.get_group_size", return_value=5)
    def test_get_request_no_username_cookie(
            self, mock_get_group_size, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("chat:home"))
        self.assertEqual(response.cookies.get("username").get("value"), None)

        mock_is_member.assert_not_called()

    @patch("apps.chat.views.chat.RedisService.get_group_size", return_value=5)
    def test_get_request_invalid_username_redis(
            self, mock_get_group_size, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = 1234
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("chat:home"))
        self.assertEqual(response.cookies.get("username").get("value"), None)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, self.username)

    def test_get_request_valid_username(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = True
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = 1234
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")

        context = response.context
        self.assertEqual(context["username"], self.username)
        self.assertIsNone(context["groups"])

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, self.username)

    def test_get_request_when_username_cookie_is_present(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = True
        self.client.cookies["username"] = "anotheruser"
        self.client.cookies["user_id"] = 1234
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], "anotheruser")

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "anotheruser")

    @patch("apps.chat.views.chat.RedisService.get_group_size", return_value=5)
    def test_post_request_missing_username(
            self, mock_get_group_size, mock_add_to_set, mock_is_member
    ):
        response = self.client.post(self.url, {})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "You need to put an username",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )

        mock_is_member.assert_not_called()

    @patch("apps.chat.views.chat.RedisService.get_group_size", return_value=5)
    def test_post_request_username_taken(
            self, mock_get_group_size, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = True
        response = self.client.post(self.url, {"username": self.username})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username already taken",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, self.username)

    def test_post_request_successful_username_addition(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        response = self.client.post(self.url, {"username": self.username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, self.username)

        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, self.username)
        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, self.username)

    def test_post_request_username_with_spaces(self, mock_add_to_set, mock_is_member):
        mock_is_member.return_value = False
        response = self.client.post(self.url, {"username": "  userwithspaces  "})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, "userwithspaces")

        mock_add_to_set.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY, "userwithspaces"
        )

    def test_post_request_username_case_sensitivity(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        username = "NewUser"
        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)
        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)

    @patch("apps.chat.views.chat.RedisService.get_group_size", return_value=5)
    def test_post_request_empty_username_field(
            self, mock_get_group_size, mock_add_to_set, mock_is_member
    ):
        response = self.client.post(self.url, {"username": ""})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "You need to put an username",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )

        mock_is_member.assert_not_called()

    def test_post_request_special_characters_in_username(
            self, mock_add_to_set, mock_is_member
    ):
        username = "user@!$"

        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("chat:home"))
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_not_called()
        mock_add_to_set.assert_not_called()

    def test_post_request_username_with_underscore_is_allowed(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        username = "test_user"

        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)
        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)

    def test_post_request_username_with_hyphen_is_allowed(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        username = "test-user"

        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)
        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)

    def test_post_request_username_with_underscore_and_hyphen_is_allowed(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        username = "test-user_123"

        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)
        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)

    def test_post_request_username_with_less_than_3_characters_is_rejected(
            self, mock_add_to_set, mock_is_member
    ):
        username = "ab"

        response = self.client.post(self.url, {"username": username})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_not_called()
        mock_add_to_set.assert_not_called()

    def test_post_request_username_with_exactly_3_characters_is_allowed(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        username = "abc"

        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)
        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)

    def test_post_request_username_with_exactly_20_characters_is_allowed(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        username = "a" * 20

        response = self.client.post(self.url, {"username": username})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.cookies["username"].value, username)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)
        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, username)

    def test_post_request_username_with_more_than_20_characters_is_rejected(
            self, mock_add_to_set, mock_is_member
    ):
        username = "a" * 21

        response = self.client.post(self.url, {"username": username})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_not_called()
        mock_add_to_set.assert_not_called()

    def test_post_request_username_with_internal_space_is_rejected(
            self, mock_add_to_set, mock_is_member
    ):
        username = "test user"

        response = self.client.post(self.url, {"username": username})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_not_called()
        mock_add_to_set.assert_not_called()

    def test_post_request_username_with_unicode_letters_is_rejected(
            self, mock_add_to_set, mock_is_member
    ):
        username = "josé123"

        response = self.client.post(self.url, {"username": username})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_not_called()
        mock_add_to_set.assert_not_called()

    def test_post_request_username_with_only_spaces_is_rejected(
            self, mock_add_to_set, mock_is_member
    ):
        response = self.client.post(self.url, {"username": "     "})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "You need to put an username",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_not_called()
        mock_add_to_set.assert_not_called()

    def test_post_request_username_taken_in_database_is_rejected(
            self, mock_add_to_set, mock_is_member
    ):
        mock_is_member.return_value = False
        UserFactory(username="ExistingUser")

        response = self.client.post(self.url, {"username": "existinguser"})

        self.assertRedirects(response, reverse("chat:home"))
        self.assertIn(
            "Username already taken",
            [msg.message for msg in list(messages.get_messages(response.wsgi_request))],
        )
        self.assertNotIn("username", response.cookies)

        mock_is_member.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "existinguser")
        mock_add_to_set.assert_not_called()

    @patch(
        "apps.chat.views.chat.RedisService.create_user_id", return_value="test-user-id"
    )
    @patch("apps.chat.views.chat.RedisService.set_unique")
    def test_post_request_success_sets_user_id_cookie(
            self,
            mock_set_unique,
            mock_create_user_id,
            mock_add_to_set,
            mock_is_member,
    ):
        mock_is_member.return_value = False

        response = self.client.post(self.url, {"username": self.username})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["user_id"].value, "test-user-id")

        mock_create_user_id.assert_called_once()

    @patch(
        "apps.chat.views.chat.RedisService.create_user_id", return_value="test-user-id"
    )
    @patch("apps.chat.views.chat.RedisService.set_unique")
    def test_post_request_success_stores_username_and_user_id_mappings_in_redis(
            self,
            mock_set_unique,
            mock_create_user_id,
            mock_add_to_set,
            mock_is_member,
    ):
        mock_is_member.return_value = False

        response = self.client.post(self.url, {"username": self.username})

        self.assertEqual(response.status_code, 200)

        mock_add_to_set.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            self.username,
        )

        mock_set_unique.assert_any_call(
            ID_TO_USERNAME_KEY.format(user_id="test-user-id"),
            self.username,
        )
        mock_set_unique.assert_any_call(
            USERNAME_TO_UUID_KEY.format(username=self.username),
            "test-user-id",
        )
        self.assertEqual(mock_set_unique.call_count, 2)

    @patch(
        "apps.chat.views.chat.RedisService.create_user_id", return_value="test-user-id"
    )
    @patch("apps.chat.views.chat.RedisService.set_unique")
    def test_post_request_success_returns_expected_context(
            self,
            mock_set_unique,
            mock_create_user_id,
            mock_add_to_set,
            mock_is_member,
    ):
        mock_is_member.return_value = False

        response = self.client.post(self.url, {"username": self.username})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["username"], self.username)
        self.assertEqual(response.context["user_id"], "test-user-id")

    @patch(
        "apps.chat.views.chat.RedisService.create_user_id", return_value="test-user-id"
    )
    @patch("apps.chat.views.chat.RedisService.set_unique")
    def test_post_request_success_sets_httponly_cookies(
            self,
            mock_set_unique,
            mock_create_user_id,
            mock_add_to_set,
            mock_is_member,
    ):
        mock_is_member.return_value = False

        response = self.client.post(self.url, {"username": self.username})

        self.assertTrue(response.cookies["username"]["httponly"])
        self.assertTrue(response.cookies["user_id"]["httponly"])

    @override_settings(COOKIES_SECURE=True)
    @patch(
        "apps.chat.views.chat.RedisService.create_user_id", return_value="test-user-id"
    )
    @patch("apps.chat.views.chat.RedisService.set_unique")
    def test_post_request_success_sets_secure_cookies_when_setting_enabled(
            self,
            mock_set_unique,
            mock_create_user_id,
            mock_add_to_set,
            mock_is_member,
    ):
        mock_is_member.return_value = False

        response = self.client.post(self.url, {"username": self.username})

        self.assertTrue(response.cookies["username"]["secure"])
        self.assertTrue(response.cookies["user_id"]["secure"])

    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.set_unique")
    def test_post_request_username_taken_does_not_create_user_id_or_store_redis_data(
            self,
            mock_set_unique,
            mock_create_user_id,
            mock_add_to_set,
            mock_is_member,
    ):
        mock_is_member.return_value = True

        response = self.client.post(self.url, {"username": self.username})

        self.assertRedirects(response, reverse("chat:home"))

        mock_create_user_id.assert_not_called()
        mock_add_to_set.assert_not_called()
        mock_set_unique.assert_not_called()
