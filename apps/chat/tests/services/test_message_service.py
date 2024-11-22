from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.chat.constants.redis_keys import USER_PROMOTIONAL_LINKS
from apps.chat.services.message_service import MessageService
from apps.users.tests.factories.profile import ProfileFactory

User = get_user_model()


class MessageServiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = MessageService()

        # Mock django_cache and redis_connection attributes
        cls.service.django_cache = MagicMock()
        cls.service.redis_connection = MagicMock()

    def test_should_select_promotional_user(self):
        results = [self.service._should_select_promotional_user() for _ in range(1000)]
        self.assertIn(True, results, "True was not returned in any of the runs")
        self.assertIn(False, results, "False was not returned in any of the runs")

    def test_get_random_user_id(self):
        user_ids = {1, 2, 3, 4}
        result = self.service._get_random_user_id(user_ids)
        self.assertIn(result, user_ids, "Returned user_id is not in the input set")

    def test_get_random_user_id_empty_set(self):
        user_ids = set()
        result = self.service._get_random_user_id(user_ids)
        self.assertIsNone(result, "Expected None for empty user_ids set")

    def test_get_random_topic_id(self):
        topic_ids = {101, 102, 103}
        result = self.service._get_random_topic_id(topic_ids)
        self.assertIn(result, topic_ids, "Returned topic_id is not in the input set")

    def test_get_random_topic_id_empty_set(self):
        topic_ids = set()
        result = self.service._get_random_topic_id(topic_ids)
        self.assertIsNone(result, "Expected None for empty topic_ids set")

    def test_store_user_promotional_links(self):
        link1 = "http://link1.com"
        link2 = "http://link2.com"
        profile1 = ProfileFactory(link=link1)
        profile2 = ProfileFactory(link=link2)

        # Set up mocked Redis behaviors
        self.service.redis_connection.key_exists.return_value = False
        self.service.redis_connection.store_in_hash = MagicMock()

        self.service.store_user_promotional_links(is_promotional=True)

        expected_data = {
            str(profile1.user.id): link1,
            str(profile2.user.id): link2,
        }
        self.service.redis_connection.store_in_hash.assert_called_once_with(
            hash_key=USER_PROMOTIONAL_LINKS,
            data=expected_data,
        )
        self.service.redis_connection.key_exists.assert_called_once_with(USER_PROMOTIONAL_LINKS)

    def test_store_no_users_promotional_links(self):
        # Set up mocked Redis behaviors
        self.service.redis_connection.key_exists.return_value = False
        self.service.redis_connection.store_in_hash = MagicMock()

        self.service.store_user_promotional_links(is_promotional=True)

        self.service.redis_connection.store_in_hash.assert_called_once_with(
            hash_key=USER_PROMOTIONAL_LINKS,
            data={},
        )
        self.service.redis_connection.key_exists.assert_called_once_with(USER_PROMOTIONAL_LINKS)

    def test_already_stored_users_promotional_links(self):
        # Set up mocked Redis behaviors
        self.service.redis_connection.key_exists.return_value = True
        self.service.redis_connection.store_in_hash = MagicMock()

        self.service.store_user_promotional_links(is_promotional=True)

        self.service.redis_connection.store_in_hash.assert_not_called()
        self.service.redis_connection.key_exists.assert_called_once_with(USER_PROMOTIONAL_LINKS)

    def test_build_message_no_placeholder(self):
        result = self.service.build_message(user_id=1, message="Hello, World!")
        self.assertEqual(result, "Hello, World!", "Expected message to remain unchanged")

    def test_build_message_with_placeholder(self):
        self.service.redis_connection.get_from_hash.return_value = "http://promo-link.com"

        result = self.service.build_message(user_id="1", message="Visit this link: {}")
        self.assertEqual(
            result,
            "Visit this link: http://promo-link.com",
            "Message was not formatted with the user link",
        )

    def test_get_message_to_send_no_users(self):
        self.service.django_cache.get_cached_user_ids.return_value = set()
        self.service.django_cache.get_cached_topic_ids.return_value = set()

        result = self.service.get_message_to_send()
        self.assertIsNone(result)

    def test_get_message_to_send_no_topics(self):
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = set()

        result = self.service.get_message_to_send()
        self.assertIsNone(result)

    def test_get_message_to_send_user_has_sent_all_messages(self):
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = [(1, "Message 1")]
        self.service.django_cache.has_user_sent_message.return_value = True

        result = self.service.get_message_to_send()
        self.assertIsNone(result)

    def test_get_message_to_send_valid_message(self):
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = [(1, "Message 1")]
        self.service.django_cache.has_user_sent_message.return_value = False
        self.service.django_cache.get_username.return_value = "test_user"

        result = self.service.get_message_to_send()
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["message"], "Message 1")

    def test_get_message_to_send_promotional_user(self):
        self.service.redis_connection.key_exists.return_value = False
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = [(1, "Message {}")]
        self.service.django_cache.has_user_sent_message.return_value = False
        self.service.django_cache.get_username.return_value = "test_user"
        self.service.redis_connection.get_from_hash.return_value = "http://example.com/promo"

        with patch.object(self.service, '_should_select_promotional_user', return_value=True):
            result = self.service.get_message_to_send()

        self.assertEqual(result["message"], "Message http://example.com/promo")

    def test_get_message_to_send_no_promotional_links(self):
        self.service.redis_connection.key_exists.return_value = False
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = [(1, "Message {}")]
        self.service.django_cache.has_user_sent_message.return_value = False
        self.service.django_cache.get_username.return_value = "test_user"
        self.service.redis_connection.get_from_hash.return_value = None

        with patch.object(self.service, '_should_select_promotional_user', return_value=False):
            result = self.service.get_message_to_send()

        self.assertEqual(result["message"], "Message {}")

    def test_get_message_to_send_no_user_for_topic(self):
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = []

        result = self.service.get_message_to_send()
        self.assertIsNone(result)

    def test_get_message_to_send_switch_promotional_users(self):
        self.service.django_cache.get_cached_user_ids.side_effect = [set(), {2}]
        self.service.django_cache.get_cached_topic_ids.side_effect = [set(), {201}]
        self.service.django_cache.get_cached_conversation_flows.return_value = [(1, "Message")]
        self.service.django_cache.has_user_sent_message.return_value = False
        self.service.django_cache.get_username.return_value = "test_user"

        result = self.service.get_message_to_send()
        self.assertIsNotNone(result)
        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["message"], "Message")

    def test_get_message_to_send_no_conversation_flows(self):
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = []

        result = self.service.get_message_to_send()
        self.assertIsNone(result)

    def test_get_message_to_send_message_formatting(self):
        self.service.django_cache.get_cached_user_ids.return_value = {1}
        self.service.django_cache.get_cached_topic_ids.return_value = {101}
        self.service.django_cache.get_cached_conversation_flows.return_value = [(1, "Message {}")]
        self.service.django_cache.has_user_sent_message.return_value = False
        self.service.django_cache.get_username.return_value = "test_user"
        self.service.redis_connection.get_from_hash.return_value = "http://example.com"

        with patch.object(self.service, '_should_select_promotional_user', return_value=True):
            result = self.service.get_message_to_send()

        self.assertEqual(result["message"], "Message http://example.com")
