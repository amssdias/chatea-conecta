from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.services.guest_session import GUEST_SESSION_COOKIE, issue_guest_token
from apps.users.tests.factories import UserFactory

USER_ID = "u_00001"


@patch("apps.users.views.close_chat_session.revoke_guest_identity")
@patch("apps.chat.views.home_chat.RedisService.is_member", autospec=True)
@patch("apps.chat.views.home_chat.RedisService.remove_from_set", autospec=True)
class TestCloseChatSessionView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users:logout")

    def setUp(self):
        self.client = Client()

    def given_guest_session(self, username="testuser", user_id=USER_ID):
        self.client.cookies[GUEST_SESSION_COOKIE] = issue_guest_token(username, user_id)

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_redirect_when_no_guest_session_cookie(
        self,
        mock_get_group_size,
        mock_remove_from_set,
        mock_is_member,
        mock_revoke,
    ):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("chat:home"))
        mock_is_member.assert_not_called()
        mock_remove_from_set.assert_not_called()
        mock_revoke.assert_not_called()

    def test_remove_username_from_redis_called(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = True
        self.given_guest_session()
        self.client.post(self.url)
        mock_remove_from_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "testuser")

    def test_guest_identity_is_revoked(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = True
        self.given_guest_session()
        self.client.post(self.url)
        mock_revoke.assert_called_once_with("testuser", USER_ID)

    def test_guest_session_cookie_deleted(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = False
        self.given_guest_session()
        response = self.client.post(self.url)

        self.assertEqual(response.cookies[GUEST_SESSION_COOKIE].value, "")

    def test_legacy_identity_cookies_deleted(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = False
        self.given_guest_session()
        response = self.client.post(self.url)

        self.assertEqual(response.cookies["username"].value, "")
        self.assertEqual(response.cookies["user_id"].value, "")

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_forged_plaintext_username_cookie_is_ignored(
        self,
        mock_get_group_size,
        mock_remove_from_set,
        mock_is_member,
        mock_revoke,
    ):
        """A guest must not be able to free somebody else's nickname."""
        mock_is_member.return_value = True
        self.client.cookies["username"] = "victim"

        self.client.post(self.url)

        mock_is_member.assert_not_called()
        mock_remove_from_set.assert_not_called()
        mock_revoke.assert_not_called()

    def test_no_remove_when_username_not_in_redis(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = False
        self.given_guest_session()
        self.client.post(self.url)
        mock_remove_from_set.assert_not_called()

    @patch("apps.chat.views.home_chat.RedisService.get_group_size", return_value=5)
    def test_redirect_when_guest_session_cookie_present(
        self,
        mock_get_group_size,
        mock_remove_from_set,
        mock_is_member,
        mock_revoke,
    ):
        mock_is_member.return_value = False
        self.given_guest_session()
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("chat:home"))

    def test_username_casing_is_preserved(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = True
        self.given_guest_session(username="TestUser")
        self.client.post(self.url)
        mock_remove_from_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "TestUser")

    def test_redirect_status_code(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = False
        self.given_guest_session()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_without_guest_token(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = True
        user = UserFactory(username="realuser")
        self.client.force_login(user)

        response = self.client.post(self.url)

        mock_remove_from_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "realuser")
        mock_revoke.assert_called_once_with("realuser", str(user.pk))
        self.assertEqual(response.status_code, 302)

    def test_multiple_users(self, mock_remove_from_set, mock_is_member, mock_revoke):
        mock_is_member.return_value = True
        self.given_guest_session(username="user1")
        self.client.post(self.url)
        mock_remove_from_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "user1")

        self.given_guest_session(username="user2")
        self.client.post(self.url)
        self.assertEqual(mock_remove_from_set.call_count, 2)
