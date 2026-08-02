from unittest.mock import AsyncMock, patch

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase

from apps.chat.consumers import ChatConsumer
from apps.chat.services.guest_session import GUEST_SESSION_COOKIE, issue_guest_token

USERNAME = "testuser"
USER_ID = "u_00001"


@patch("apps.chat.consumers.restore_user_private_chat_groups", new_callable=AsyncMock)
@patch("apps.chat.consumers.register_username_as_active", new_callable=AsyncMock)
@patch("apps.chat.consumers.mark_user_online", new_callable=AsyncMock)
class ChatConsumerGuestConnectTests(TransactionTestCase):
    """
    The websocket handshake used to trust the guest cookies as-is, which let
    anyone pick a nickname and, worse, join another guest's notification group
    by guessing their sequential id.
    """

    def build_communicator(self, cookies=None):
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
        communicator.scope["user"] = AnonymousUser()
        communicator.scope["cookies"] = cookies or {}
        return communicator

    async def assert_connection_refused(self, cookies):
        communicator = self.build_communicator(cookies)

        connected, _ = await communicator.connect()

        self.assertFalse(connected)

        await communicator.disconnect()

    @patch("apps.chat.services.guest_session.aclaim_guest_identity", new_callable=AsyncMock)
    async def test_refuses_forged_plaintext_identity_cookies(self, mock_claim, *mocks):
        """Regression: these two cookies alone used to be enough to connect."""
        mock_claim.return_value = True

        await self.assert_connection_refused(
            {"username": "victim", "user_id": USER_ID},
        )

        mock_claim.assert_not_awaited()

    async def test_refuses_a_connection_without_cookies(self, *mocks):
        await self.assert_connection_refused({})

    async def test_refuses_an_unsigned_guest_session_cookie(self, *mocks):
        await self.assert_connection_refused(
            {GUEST_SESSION_COOKIE: f"{USERNAME}:{USER_ID}"},
        )

    async def test_refuses_a_tampered_guest_session_cookie(self, *mocks):
        token = issue_guest_token(USERNAME, USER_ID)
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        await self.assert_connection_refused({GUEST_SESSION_COOKIE: tampered})

    @patch("apps.chat.services.guest_session.aclaim_guest_identity", new_callable=AsyncMock)
    async def test_refuses_a_nickname_owned_by_another_user_id(self, mock_claim, *mocks):
        mock_claim.return_value = False

        await self.assert_connection_refused(
            {GUEST_SESSION_COOKIE: issue_guest_token(USERNAME, USER_ID)},
        )

        mock_claim.assert_awaited_once_with(USERNAME, USER_ID)

    @patch("apps.chat.services.guest_session.aclaim_guest_identity", new_callable=AsyncMock)
    async def test_accepts_a_valid_signed_session(self, mock_claim, *mocks):
        mock_claim.return_value = True

        communicator = self.build_communicator(
            {GUEST_SESSION_COOKIE: issue_guest_token("TestUser", USER_ID)},
        )

        connected, _ = await communicator.connect()

        self.assertTrue(connected)

        await communicator.disconnect()

    @patch("apps.chat.services.guest_session.aclaim_guest_identity", new_callable=AsyncMock)
    async def test_identity_comes_from_the_token_not_from_other_cookies(self, mock_claim, *mocks):
        mock_claim.return_value = True

        communicator = self.build_communicator(
            {
                GUEST_SESSION_COOKIE: issue_guest_token(USERNAME, USER_ID),
                "username": "victim",
                "user_id": "u_00099",
            },
        )

        await communicator.connect()

        mock_claim.assert_awaited_once_with(USERNAME, USER_ID)

        await communicator.disconnect()
