from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
    USERNAME_TO_UUID_KEY, ID_TO_USERNAME_KEY,
)
from apps.users.tests.factories import UserFactory


@override_settings(COOKIES_SECURE=False)
class ChatViewTests(TestCase):
    def setUp(self):
        self.url = reverse("chat:live-chat")
        self.home_url = reverse("chat:home")
        self.username = "testuser"
        self.user_id = "user-uuid-123"

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_username_cookie_is_missing(self, mock_is_member, mock_get_key, mock_get_group_size):
        self.client.cookies["user_id"] = self.user_id

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()
        mock_get_key.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_user_id_cookie_is_missing(self, mock_is_member, mock_get_key, mock_get_group_size):
        self.client.cookies["username"] = self.username

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()
        mock_get_key.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_username_is_not_registered_in_redis(self, mock_is_member, mock_get_key,
                                                                    mock_get_group_size):
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = self.user_id
        mock_is_member.return_value = False

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            self.username,
        )
        mock_get_key.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_renders_chat_when_cookies_are_valid_and_username_exists_in_redis(self, mock_is_member, mock_get_key):
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = self.user_id
        mock_is_member.return_value = True
        mock_get_key.return_value = self.user_id

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], self.username)
        self.assertEqual(response.context["user_id"], self.user_id)
        self.assertIsNone(response.context["groups"])

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            self.username,
        )
        mock_get_key.assert_called_once_with(
            USERNAME_TO_UUID_KEY.format(username=self.username),
        )

    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_uses_user_id_from_redis_instead_of_cookie_user_id(self, mock_is_member, mock_get_key):
        cookie_user_id = "old-cookie-user-id"
        redis_user_id = "fresh-redis-user-id"

        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = cookie_user_id
        mock_is_member.return_value = True
        mock_get_key.return_value = redis_user_id

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_id"], redis_user_id)

        mock_get_key.assert_called_once_with(
            USERNAME_TO_UUID_KEY.format(username=self.username),
        )

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_both_cookies_are_missing(self, mock_is_member, mock_get_key, mock_get_group_size):
        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()
        mock_get_key.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_username_cookie_is_empty(self, mock_is_member, mock_get_key, mock_get_group_size):
        self.client.cookies["username"] = ""
        self.client.cookies["user_id"] = self.user_id

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()
        mock_get_key.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.get_key")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_user_id_cookie_is_empty(self, mock_is_member, mock_get_key, mock_get_group_size):
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = ""

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()
        mock_get_key.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_is_empty(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
            mock_get_group_size,
    ):
        response = self.client.post(
            self.url,
            data={"username": ""},
        )

        self.assertRedirects(response, self.home_url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("You need to put an username", messages)

        mock_is_member.assert_not_called()
        mock_create_user_id.assert_not_called()
        mock_add_to_set.assert_not_called()
        mock_set_unique.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_strips_username_before_validation(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
            mock_get_group_size,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "  testuser  "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], "testuser")
        self.assertEqual(response.context["user_id"], "user-uuid-123")

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "testuser",
        )
        mock_add_to_set.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "testuser",
        )

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_is_too_short(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
            mock_get_group_size,
    ):
        response = self.client.post(
            self.url,
            data={"username": "ab"},
        )

        self.assertRedirects(response, self.home_url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn(
            "Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'",
            messages,
        )

        mock_is_member.assert_not_called()
        mock_create_user_id.assert_not_called()
        mock_add_to_set.assert_not_called()
        mock_set_unique.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_has_invalid_characters(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
            mock_get_group_size,
    ):
        response = self.client.post(
            self.url,
            data={"username": "bad user!"},
        )

        self.assertRedirects(response, self.home_url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn(
            "Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'",
            messages,
        )

        mock_is_member.assert_not_called()
        mock_create_user_id.assert_not_called()
        mock_add_to_set.assert_not_called()
        mock_set_unique.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_already_exists_in_redis(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
            mock_get_group_size,
    ):
        mock_is_member.return_value = True

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertRedirects(response, self.home_url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Username already taken", messages)

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "testuser",
        )
        mock_create_user_id.assert_not_called()
        mock_add_to_set.assert_not_called()
        mock_set_unique.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_already_exists_in_db_case_insensitive(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
            mock_get_group_size,
    ):
        UserFactory(username="TestUser")
        mock_is_member.return_value = False

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertRedirects(response, self.home_url)

        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn("Username already taken", messages)

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "testuser",
        )
        mock_create_user_id.assert_not_called()
        mock_add_to_set.assert_not_called()
        mock_set_unique.assert_not_called()

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_renders_chat_template(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_adds_username_to_redis_set_lowercase(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        self.client.post(
            self.url,
            data={"username": "TestUser"},
        )

        mock_add_to_set.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "testuser",
        )

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_stores_id_to_username_mapping(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        mock_set_unique.assert_any_call(
            ID_TO_USERNAME_KEY.format(user_id="user-uuid-123"),
            "testuser",
        )

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_stores_username_to_uuid_mapping(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        mock_set_unique.assert_any_call(
            USERNAME_TO_UUID_KEY.format(username="testuser"),
            "user-uuid-123",
        )

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_sets_username_and_user_id_cookies(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertEqual(response.cookies["username"].value, "testuser")
        self.assertEqual(response.cookies["user_id"].value, "user-uuid-123")

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_sets_cookies_as_httponly(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertTrue(response.cookies["username"]["httponly"])
        self.assertTrue(response.cookies["user_id"]["httponly"])

    @override_settings(COOKIES_SECURE=True)
    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_sets_secure_cookies_when_setting_is_enabled(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertTrue(response.cookies["username"]["secure"])
        self.assertTrue(response.cookies["user_id"]["secure"])

    @patch("apps.chat.views.chat.RedisService.set_unique")
    @patch("apps.chat.views.chat.RedisService.add_to_set")
    @patch("apps.chat.views.chat.RedisService.create_user_id")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_context_contains_username_and_user_id(
            self,
            mock_is_member,
            mock_create_user_id,
            mock_add_to_set,
            mock_set_unique,
    ):
        mock_is_member.return_value = False
        mock_create_user_id.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertEqual(response.context["username"], "testuser")
        self.assertEqual(response.context["user_id"], "user-uuid-123")
