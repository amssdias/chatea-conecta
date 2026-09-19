from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from django.conf import settings
from django.core import signing
from django.test import SimpleTestCase, override_settings

from apps.chat.constants.redis_keys import ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.services.guest_session import (
    GUEST_SESSION_SALT,
    aclaim_guest_identity,
    aresolve_guest_identity,
    claim_guest_identity,
    issue_guest_token,
    read_guest_token,
    revoke_guest_identity,
)

USERNAME = "testuser"
USER_ID = "u_00001"
USERNAME_KEY = USERNAME_TO_UUID_KEY.format(username=USERNAME)
ID_KEY = ID_TO_USERNAME_KEY.format(user_id=USER_ID)


class ReadGuestTokenTests(SimpleTestCase):
    def test_round_trip_returns_the_issued_identity(self):
        token = issue_guest_token(USERNAME, USER_ID)

        self.assertEqual(read_guest_token(token), (USERNAME, USER_ID))

    def test_user_id_is_serialized_as_a_string(self):
        token = issue_guest_token(USERNAME, 42)

        self.assertEqual(read_guest_token(token), (USERNAME, "42"))

    def test_returns_none_for_an_empty_token(self):
        self.assertIsNone(read_guest_token(""))

    def test_returns_none_for_a_tampered_token(self):
        token = issue_guest_token(USERNAME, USER_ID)
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        self.assertIsNone(read_guest_token(tampered))

    def test_returns_none_for_a_token_signed_with_another_salt(self):
        token = signing.dumps({"u": USERNAME, "i": USER_ID}, salt="somewhere.else")

        self.assertIsNone(read_guest_token(token))

    def test_returns_none_for_an_unsigned_value(self):
        self.assertIsNone(read_guest_token(f"{USERNAME}:{USER_ID}"))

    @patch("apps.chat.services.guest_session.signing.loads")
    def test_returns_none_for_an_expired_token(self, mock_loads):
        mock_loads.side_effect = signing.SignatureExpired("too old")

        self.assertIsNone(read_guest_token(issue_guest_token(USERNAME, USER_ID)))

    @override_settings(GUEST_SESSION_MAX_AGE=600)
    @patch("apps.chat.services.guest_session.signing.loads")
    def test_checks_the_token_age_against_the_configured_lifetime(self, mock_loads):
        mock_loads.return_value = {"u": USERNAME, "i": USER_ID}
        token = issue_guest_token(USERNAME, USER_ID)

        read_guest_token(token)

        mock_loads.assert_called_once_with(
            token,
            salt=GUEST_SESSION_SALT,
            max_age=600,
        )

    def test_returns_none_when_the_payload_is_not_a_mapping(self):
        token = signing.dumps([USERNAME, USER_ID], salt=GUEST_SESSION_SALT)

        self.assertIsNone(read_guest_token(token))

    def test_returns_none_when_a_claim_is_missing(self):
        token = signing.dumps({"u": USERNAME}, salt=GUEST_SESSION_SALT)

        self.assertIsNone(read_guest_token(token))

    def test_returns_none_when_the_user_id_is_empty(self):
        token = signing.dumps({"u": USERNAME, "i": ""}, salt=GUEST_SESSION_SALT)

        self.assertIsNone(read_guest_token(token))

    def test_returns_none_when_the_username_breaks_the_nickname_rules(self):
        token = signing.dumps({"u": "no spaces!", "i": USER_ID}, salt=GUEST_SESSION_SALT)

        self.assertIsNone(read_guest_token(token))


@override_settings(GUEST_SESSION_MAX_AGE=600)
@patch("apps.chat.services.guest_session.RedisService.set_expiration")
@patch("apps.chat.services.guest_session.RedisService.set_value")
@patch("apps.chat.services.guest_session.RedisService.get_key")
@patch("apps.chat.services.guest_session.RedisService.set_unique")
class ClaimGuestIdentityTests(SimpleTestCase):
    def test_accepts_the_owner_of_the_nickname(
        self,
        mock_set_unique,
        mock_get_key,
        mock_set_value,
        mock_set_expiration,
    ):
        mock_set_unique.return_value = None
        mock_get_key.return_value = USER_ID

        self.assertTrue(claim_guest_identity(USERNAME, USER_ID))

        mock_get_key.assert_called_once_with(USERNAME_KEY)

    def test_rejects_a_nickname_owned_by_another_user_id(
        self,
        mock_set_unique,
        mock_get_key,
        mock_set_value,
        mock_set_expiration,
    ):
        mock_set_unique.return_value = None
        mock_get_key.return_value = "u_00099"

        self.assertFalse(claim_guest_identity(USERNAME, USER_ID))

        mock_set_value.assert_not_called()

    def test_readopts_the_identity_when_the_mapping_expired(
        self,
        mock_set_unique,
        mock_get_key,
        mock_set_value,
        mock_set_expiration,
    ):
        mock_set_unique.return_value = True

        self.assertTrue(claim_guest_identity(USERNAME, USER_ID))

        mock_set_unique.assert_called_once_with(USERNAME_KEY, USER_ID, ttl=600)
        mock_get_key.assert_not_called()
        mock_set_value.assert_called_once_with(ID_KEY, USERNAME, timeout=600)

    def test_refreshes_both_mapping_keys_for_an_existing_owner(
        self,
        mock_set_unique,
        mock_get_key,
        mock_set_value,
        mock_set_expiration,
    ):
        mock_set_unique.return_value = None
        mock_get_key.return_value = USER_ID

        claim_guest_identity(USERNAME, USER_ID)

        mock_set_value.assert_called_once_with(ID_KEY, USERNAME, timeout=600)
        mock_set_expiration.assert_called_once_with(USERNAME_KEY, 600)

    def test_looks_the_nickname_up_in_lowercase(
        self,
        mock_set_unique,
        mock_get_key,
        mock_set_value,
        mock_set_expiration,
    ):
        mock_set_unique.return_value = None
        mock_get_key.return_value = USER_ID

        self.assertTrue(claim_guest_identity("TestUser", USER_ID))

        mock_set_unique.assert_called_once_with(USERNAME_KEY, USER_ID, ttl=600)


@override_settings(GUEST_SESSION_MAX_AGE=600)
class RevokeGuestIdentityTests(SimpleTestCase):
    @patch("apps.chat.services.guest_session.RedisService.delete_key")
    def test_deletes_both_mapping_keys(self, mock_delete_key):
        revoke_guest_identity("TestUser", USER_ID)

        mock_delete_key.assert_any_call(USERNAME_KEY)
        mock_delete_key.assert_any_call(ID_KEY)
        self.assertEqual(mock_delete_key.call_count, 2)

    @patch("apps.chat.services.guest_session.RedisService.delete_key")
    def test_skips_the_id_key_when_there_is_no_user_id(self, mock_delete_key):
        revoke_guest_identity(USERNAME, "")

        mock_delete_key.assert_called_once_with(USERNAME_KEY)


@patch(
    "apps.chat.services.guest_session.AsyncRedisService.set_expiration",
    new_callable=AsyncMock,
)
@patch(
    "apps.chat.services.guest_session.AsyncRedisService.get_value",
    new_callable=AsyncMock,
)
@patch(
    "apps.chat.services.guest_session.AsyncRedisService.set_value",
    new_callable=AsyncMock,
)
class AsyncGuestIdentityTests(IsolatedAsyncioTestCase):
    async def test_accepts_the_owner_of_the_nickname(
        self,
        mock_set_value,
        mock_get_value,
        mock_set_expiration,
    ):
        mock_set_value.return_value = False
        mock_get_value.return_value = USER_ID

        self.assertTrue(await aclaim_guest_identity(USERNAME, USER_ID))

    async def test_rejects_a_nickname_owned_by_another_user_id(
        self,
        mock_set_value,
        mock_get_value,
        mock_set_expiration,
    ):
        mock_set_value.return_value = False
        mock_get_value.return_value = "u_00099"

        self.assertFalse(await aclaim_guest_identity(USERNAME, USER_ID))

        mock_set_value.assert_awaited_once_with(
            USERNAME_KEY,
            USER_ID,
            ex=settings.GUEST_SESSION_MAX_AGE,
            nx=True,
        )

    async def test_readopts_the_identity_when_the_mapping_expired(
        self,
        mock_set_value,
        mock_get_value,
        mock_set_expiration,
    ):
        mock_set_value.return_value = True

        self.assertTrue(await aclaim_guest_identity(USERNAME, USER_ID))

        mock_get_value.assert_not_awaited()
        mock_set_value.assert_awaited_with(
            ID_KEY,
            USERNAME,
            ex=settings.GUEST_SESSION_MAX_AGE,
        )

    async def test_resolve_returns_the_identity_for_a_valid_token(
        self,
        mock_set_value,
        mock_get_value,
        mock_set_expiration,
    ):
        mock_set_value.return_value = False
        mock_get_value.return_value = USER_ID

        identity = await aresolve_guest_identity(issue_guest_token(USERNAME, USER_ID))

        self.assertEqual(identity, (USERNAME, USER_ID))

    async def test_resolve_returns_none_for_a_forged_token(
        self,
        mock_set_value,
        mock_get_value,
        mock_set_expiration,
    ):
        identity = await aresolve_guest_identity("not-a-signed-token")

        self.assertIsNone(identity)
        mock_set_value.assert_not_awaited()

    async def test_resolve_returns_none_when_the_nickname_belongs_to_someone_else(
        self,
        mock_set_value,
        mock_get_value,
        mock_set_expiration,
    ):
        mock_set_value.return_value = False
        mock_get_value.return_value = "u_00099"

        identity = await aresolve_guest_identity(issue_guest_token(USERNAME, USER_ID))

        self.assertIsNone(identity)
