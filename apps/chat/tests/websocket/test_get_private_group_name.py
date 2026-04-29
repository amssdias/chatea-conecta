from django.test import SimpleTestCase

from apps.chat.constants.consumer import USER_PRIVATE_GROUP
from apps.chat.websocket.group_names import get_private_group_name


class GetPrivateGroupNameTests(SimpleTestCase):
    def test_returns_private_group_name(self):
        result = get_private_group_name(
            user1_id="10",
            user2_id="20",
        )

        self.assertEqual(
            result,
            USER_PRIVATE_GROUP.format("10", "20").lower(),
        )

    def test_replaces_spaces_with_hyphens(self):
        result = get_private_group_name(
            user1_id="user 10",
            user2_id="user 20",
        )

        self.assertEqual(
            result,
            USER_PRIVATE_GROUP.format("user-10", "user-20").lower(),
        )

    def test_returns_group_name_in_lowercase(self):
        result = get_private_group_name(
            user1_id="USER 10",
            user2_id="USER 20",
        )

        self.assertEqual(
            result,
            USER_PRIVATE_GROUP.format("user-10", "user-20").lower(),
        )

    def test_accepts_integer_user_ids(self):
        result = get_private_group_name(
            user1_id=10,
            user2_id=20,
        )

        self.assertEqual(
            result,
            USER_PRIVATE_GROUP.format("10", "20").lower(),
        )
