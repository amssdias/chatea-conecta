from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

from apps.chat.constants.redis_keys import (
    ID_TO_USERNAME_KEY,
    REDIS_ALL_USERNAMES_KEY,
    USERNAME_TO_UUID_KEY,
)
from apps.chat.services.register_user import register_user_on_redis

USER_ID = "u_00001"


@patch("apps.chat.services.register_user.RedisService.create_user_id")
@patch("apps.chat.services.register_user.RedisService.set_value")
@patch("apps.chat.services.register_user.RedisService.add_to_set")
class RegisterUserOnRedisTests(SimpleTestCase):
    def test_adds_the_lowercased_username_to_the_active_set(
        self,
        mock_add_to_set,
        mock_set_value,
        mock_create_user_id,
    ):
        register_user_on_redis("TestUser", user_id=USER_ID)

        mock_add_to_set.assert_called_once_with(REDIS_ALL_USERNAMES_KEY, "testuser")

    def test_writes_both_mapping_keys_with_the_token_lifetime(
        self,
        mock_add_to_set,
        mock_set_value,
        mock_create_user_id,
    ):
        register_user_on_redis("TestUser", user_id=USER_ID)

        mock_set_value.assert_any_call(
            ID_TO_USERNAME_KEY.format(user_id=USER_ID),
            "TestUser",
            timeout=settings.GUEST_SESSION_MAX_AGE,
        )
        mock_set_value.assert_any_call(
            USERNAME_TO_UUID_KEY.format(username="testuser"),
            USER_ID,
            timeout=settings.GUEST_SESSION_MAX_AGE,
        )

    def test_takes_over_a_nickname_released_by_a_previous_guest(
        self,
        mock_add_to_set,
        mock_set_value,
        mock_create_user_id,
    ):
        """
        The write must not be conditional: a guest who leaves frees the nickname,
        and the next guest to claim it has to become its owner, or the ownership
        check would lock them out of their own session.
        """
        register_user_on_redis("testuser", user_id="u_00099")

        mock_set_value.assert_any_call(
            USERNAME_TO_UUID_KEY.format(username="testuser"),
            "u_00099",
            timeout=settings.GUEST_SESSION_MAX_AGE,
        )

    def test_generates_a_user_id_when_none_is_given(
        self,
        mock_add_to_set,
        mock_set_value,
        mock_create_user_id,
    ):
        mock_create_user_id.return_value = USER_ID

        self.assertEqual(register_user_on_redis("testuser"), USER_ID)

        mock_create_user_id.assert_called_once_with()

    def test_keeps_the_given_user_id(
        self,
        mock_add_to_set,
        mock_set_value,
        mock_create_user_id,
    ):
        self.assertEqual(register_user_on_redis("testuser", user_id=USER_ID), USER_ID)

        mock_create_user_id.assert_not_called()
