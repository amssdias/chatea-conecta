from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
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
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_username_cookie_is_missing(self, mock_is_member, mock_get_group_size):
        self.client.cookies["user_id"] = self.user_id

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_user_id_cookie_is_missing(self, mock_is_member, mock_get_group_size):
        self.client.cookies["username"] = self.username

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_username_is_not_registered_in_redis(self, mock_is_member, mock_get_group_size):
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = self.user_id
        mock_is_member.return_value = False

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            self.username,
        )

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_renders_chat_when_cookies_are_valid_and_username_exists_in_redis(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = self.user_id

        mock_is_member.return_value = True
        mock_register_user_on_redis.return_value = self.user_id

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], self.username)
        self.assertEqual(response.context["user_id"], self.user_id)
        self.assertTrue(response.context["is_user_pro"])
        self.assertIsNone(response.context["groups"])
        self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow")

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            self.username,
        )
        mock_register_user_on_redis.assert_called_once_with(
            self.username,
            user_id=self.user_id,
        )

        self.assertNotIn("username", response.cookies)
        self.assertNotIn("user_id", response.cookies)

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_uses_registered_user_id_returned_by_service_for_guest_session(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        cookie_user_id = "old-cookie-user-id"
        registered_user_id = "fresh-redis-user-id"

        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = cookie_user_id

        mock_is_member.return_value = True
        mock_register_user_on_redis.return_value = registered_user_id

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["username"], self.username)
        self.assertEqual(response.context["user_id"], registered_user_id)

        mock_register_user_on_redis.assert_called_once_with(
            self.username,
            user_id=cookie_user_id,
        )

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_both_cookies_are_missing(self, mock_is_member, mock_get_group_size):
        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_username_cookie_is_empty(self, mock_is_member, mock_get_group_size):
        self.client.cookies["username"] = ""
        self.client.cookies["user_id"] = self.user_id

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_redirects_when_user_id_cookie_is_empty(self, mock_is_member, mock_get_group_size):
        self.client.cookies["username"] = self.username
        self.client.cookies["user_id"] = ""

        response = self.client.get(self.url)

        self.assertRedirects(response, self.home_url)

        mock_is_member.assert_not_called()

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_authenticated_user_without_guest_cookies_renders_chat(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        user = UserFactory(username="realuser")
        registered_user_id = str(user.id)

        self.client.force_login(user)
        mock_register_user_on_redis.return_value = registered_user_id

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["username"], user.username)
        self.assertEqual(response.context["user_id"], registered_user_id)

        self.assertEqual(response.cookies["username"].value, user.username)
        self.assertEqual(response.cookies["user_id"].value, registered_user_id)

        mock_is_member.assert_not_called()
        mock_register_user_on_redis.assert_called_once_with(
            user.username,
            user_id=user.id,
        )

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_is_empty(
            self,
            mock_is_member,
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

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_strips_username_before_validation(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

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
        mock_register_user_on_redis.assert_called_once_with(
            "testuser",
            user_id=None,
        )

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_post_redirects_when_username_is_too_short(self, mock_get_group_size):
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

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_post_redirects_when_username_has_invalid_characters(self, mock_get_group_size):
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

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_already_exists_in_redis(self, mock_is_member, mock_get_group_size):
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

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_redirects_when_username_already_exists_in_db_case_insensitive(self, mock_is_member,
                                                                                mock_get_group_size):
        UserFactory(username="testUser")
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

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_renders_chat_template(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")

        mock_register_user_on_redis.assert_called_once_with("testuser", user_id=None)

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_registers_submitted_username(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "TestUser"},
        )

        self.assertEqual(response.status_code, 200)

        mock_is_member.assert_called_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "TestUser",
        )
        mock_register_user_on_redis.assert_called_once_with(
            "TestUser",
            user_id=None,
        )

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_sets_username_and_user_id_cookies(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertEqual(response.cookies["username"].value, "testuser")
        self.assertEqual(response.cookies["user_id"].value, "user-uuid-123")

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_sets_cookies_as_httponly(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertTrue(response.cookies["username"]["httponly"])
        self.assertTrue(response.cookies["user_id"]["httponly"])

    @override_settings(COOKIES_SECURE=True)
    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_sets_secure_cookies_when_setting_is_enabled(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertTrue(response.cookies["username"]["secure"])
        self.assertTrue(response.cookies["user_id"]["secure"])

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_success_context_contains_username_and_user_id(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        mock_is_member.return_value = False
        mock_register_user_on_redis.return_value = "user-uuid-123"

        response = self.client.post(
            self.url,
            data={"username": "testuser"},
        )

        self.assertEqual(response.context["username"], "testuser")
        self.assertEqual(response.context["user_id"], "user-uuid-123")
        self.assertTrue(response.context["is_user_pro"])
        self.assertIsNone(response.context["groups"])

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_get_authenticated_user_uses_authenticated_user_data(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        user = UserFactory(username="realuser")
        registered_user_id = str(user.id)

        self.client.force_login(user)
        self.client.cookies["username"] = "guestuser"
        self.client.cookies["user_id"] = "guest-user-id"

        mock_register_user_on_redis.return_value = registered_user_id

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], user.username)
        self.assertEqual(response.context["user_id"], registered_user_id)

        self.assertEqual(response.cookies["username"].value, user.username)
        self.assertEqual(response.cookies["user_id"].value, registered_user_id)

        mock_is_member.assert_not_called()
        mock_register_user_on_redis.assert_called_once_with(
            user.username,
            user_id=user.id,
        )

    @patch("apps.chat.views.chat.register_user_on_redis")
    @patch("apps.chat.views.chat.RedisService.is_member")
    def test_post_authenticated_user_uses_authenticated_user_data_and_ignores_submitted_username(
            self,
            mock_is_member,
            mock_register_user_on_redis,
    ):
        user = UserFactory(username="realuser")
        registered_user_id = str(user.id)

        self.client.force_login(user)

        mock_register_user_on_redis.return_value = registered_user_id

        response = self.client.post(
            self.url,
            data={"username": "fakeguestuser"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chat/chat.html")
        self.assertEqual(response.context["username"], user.username)
        self.assertEqual(response.context["user_id"], registered_user_id)

        self.assertEqual(response.cookies["username"].value, user.username)
        self.assertEqual(response.cookies["user_id"].value, registered_user_id)

        mock_is_member.assert_not_called()
        mock_register_user_on_redis.assert_called_once_with(
            user.username,
            user_id=user.id,
        )
