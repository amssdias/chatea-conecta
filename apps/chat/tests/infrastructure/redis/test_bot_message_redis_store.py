from unittest.mock import patch

from django.test import SimpleTestCase

from apps.chat.constants.bot_message_redis_keys import (
    BOT_MESSAGE_CACHE_LOADED,
    BOT_TOPIC_IDS,
    BOT_TOPIC_MESSAGES,
    BOT_USER_IDS,
    BOT_USERNAMES, BOT_MESSAGE_SENT,
)
from apps.chat.constants.cache_expiration import BOT_MESSAGE_CACHE_TTL, BOT_MESSAGE_SENT_TTL
from apps.chat.infrastructure.redis.bot_message_redis_store import (
    BotMessageRedisStore,
)


class BotMessageRedisStoreTestCase(SimpleTestCase):
    def setUp(self):
        self.store = BotMessageRedisStore()

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.key_exists")
    def test_is_cache_loaded_returns_true_when_cache_key_exists(self, mock_key_exists):
        mock_key_exists.return_value = True

        result = self.store.is_cache_loaded()

        self.assertTrue(result)
        mock_key_exists.assert_called_once_with(BOT_MESSAGE_CACHE_LOADED)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.key_exists")
    def test_is_cache_loaded_returns_false_when_cache_key_does_not_exist(self, mock_key_exists):
        mock_key_exists.return_value = False

        result = self.store.is_cache_loaded()

        self.assertFalse(result)
        mock_key_exists.assert_called_once_with(BOT_MESSAGE_CACHE_LOADED)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_value")
    def test_mark_cache_as_loaded_stores_cache_flag_with_expected_ttl(self, mock_set_value):
        self.store.mark_cache_as_loaded()

        mock_set_value.assert_called_once_with(
            redis_key=BOT_MESSAGE_CACHE_LOADED,
            value="1",
            timeout=BOT_MESSAGE_CACHE_TTL,
        )

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.delete_key")
    def test_clear_cache_loaded_flag_deletes_cache_flag(self, mock_delete_key):
        self.store.clear_cache_loaded_flag()

        mock_delete_key.assert_called_once_with(BOT_MESSAGE_CACHE_LOADED)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.store_hash")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.add_to_set")
    def test_store_bot_users_stores_user_ids_and_usernames(
            self,
            mock_add_to_set,
            mock_store_hash,
            mock_set_expiration,
    ):
        self.store.store_bot_users(
            {
                1: "john_bot",
                2: "maria_bot",
            }
        )

        mock_add_to_set.assert_called_once_with(BOT_USER_IDS, "1", "2")
        mock_store_hash.assert_called_once_with(
            BOT_USERNAMES,
            {
                "1": "john_bot",
                "2": "maria_bot",
            },
        )

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.store_hash")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.add_to_set")
    def test_store_bot_users_sets_expiration_for_user_ids_and_usernames(
            self,
            mock_add_to_set,
            mock_store_hash,
            mock_set_expiration,
    ):
        self.store.store_bot_users(
            {
                1: "john_bot",
                2: "maria_bot",
            }
        )

        self.assertEqual(mock_set_expiration.call_count, 2)
        mock_set_expiration.assert_any_call(BOT_USER_IDS, BOT_MESSAGE_CACHE_TTL)
        mock_set_expiration.assert_any_call(BOT_USERNAMES, BOT_MESSAGE_CACHE_TTL)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.store_hash")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.add_to_set")
    def test_store_bot_users_does_nothing_when_users_are_empty(
            self,
            mock_add_to_set,
            mock_store_hash,
            mock_set_expiration,
    ):
        self.store.store_bot_users({})

        mock_add_to_set.assert_not_called()
        mock_store_hash.assert_not_called()
        mock_set_expiration.assert_not_called()

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_random_set_member")
    def test_get_random_bot_user_id_returns_integer_user_id(self, mock_get_random_set_member):
        mock_get_random_set_member.return_value = "15"

        result = self.store.get_random_bot_user_id()

        self.assertEqual(result, 15)
        mock_get_random_set_member.assert_called_once_with(BOT_USER_IDS)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_random_set_member")
    def test_get_random_bot_user_id_returns_none_when_no_user_exists(self, mock_get_random_set_member):
        mock_get_random_set_member.return_value = None

        result = self.store.get_random_bot_user_id()

        self.assertIsNone(result)
        mock_get_random_set_member.assert_called_once_with(BOT_USER_IDS)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_from_hash")
    def test_get_bot_username_returns_username_from_hash(self, mock_get_from_hash):
        mock_get_from_hash.return_value = "alex_bot"

        result = self.store.get_bot_username(10)

        self.assertEqual(result, "alex_bot")
        mock_get_from_hash.assert_called_once_with(BOT_USERNAMES, 10)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.add_to_set")
    def test_store_topic_ids_stores_topic_ids(self, mock_add_to_set):
        self.store.store_topic_ids({1, 2, 3})

        mock_add_to_set.assert_called_once_with(BOT_TOPIC_IDS, 1, 2, 3)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.add_to_set")
    def test_store_topic_ids_sets_expiration(self, mock_add_to_set, mock_set_expiration):
        self.store.store_topic_ids({1, 2, 3})

        mock_set_expiration.assert_called_once_with(
            BOT_TOPIC_IDS,
            BOT_MESSAGE_CACHE_TTL,
        )

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.add_to_set")
    def test_store_topic_ids_does_nothing_when_topic_ids_are_empty(self, mock_add_to_set, mock_set_expiration):
        self.store.store_topic_ids(set())

        mock_add_to_set.assert_not_called()
        mock_set_expiration.assert_not_called()

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_random_set_member")
    def test_get_random_topic_id_returns_integer_topic_id(self, mock_get_random_set_member):
        mock_get_random_set_member.return_value = "25"

        result = self.store.get_random_topic_id()

        self.assertEqual(result, 25)
        mock_get_random_set_member.assert_called_once_with(BOT_TOPIC_IDS)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_random_set_member")
    def test_get_random_topic_id_returns_none_when_no_topic_exists(self, mock_get_random_set_member):
        mock_get_random_set_member.return_value = None

        result = self.store.get_random_topic_id()

        self.assertIsNone(result)
        mock_get_random_set_member.assert_called_once_with(BOT_TOPIC_IDS)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.store_hash")
    def test_store_topic_messages_stores_messages_for_topic(self, mock_store_hash, mock_set_expiration):
        self.store.store_topic_messages(
            topic_id=10,
            messages={
                501: "Hello everyone!",
                502: "Anyone from Madrid?",
            },
        )

        redis_key = BOT_TOPIC_MESSAGES.format(topic_id=10)

        mock_store_hash.assert_called_once_with(
            redis_key,
            {
                "501": "Hello everyone!",
                "502": "Anyone from Madrid?",
            },
        )

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.store_hash")
    def test_store_topic_messages_sets_expiration(self, mock_store_hash, mock_set_expiration):
        self.store.store_topic_messages(
            topic_id=10,
            messages={
                501: "Hello everyone!",
            },
        )

        redis_key = BOT_TOPIC_MESSAGES.format(topic_id=10)

        mock_set_expiration.assert_called_once_with(
            redis_key,
            BOT_MESSAGE_CACHE_TTL,
        )

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_expiration")
    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.store_hash")
    def test_store_topic_messages_does_nothing_when_messages_are_empty(self, mock_store_hash, mock_set_expiration):
        self.store.store_topic_messages(
            topic_id=10,
            messages={},
        )

        mock_store_hash.assert_not_called()
        mock_set_expiration.assert_not_called()

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_hash")
    def test_get_topic_messages_returns_messages_with_integer_ids(self, mock_get_hash):
        redis_key = BOT_TOPIC_MESSAGES.format(topic_id=10)

        mock_get_hash.return_value = {
            "501": "Hello everyone!",
            "502": "Anyone from Madrid?",
        }

        result = self.store.get_topic_messages(topic_id=10)

        self.assertEqual(
            result,
            {
                501: "Hello everyone!",
                502: "Anyone from Madrid?",
            },
        )
        mock_get_hash.assert_called_once_with(redis_key)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_hash")
    def test_get_topic_messages_returns_empty_dict_when_no_messages_exist(self, mock_get_hash):
        redis_key = BOT_TOPIC_MESSAGES.format(topic_id=10)
        mock_get_hash.return_value = {}

        result = self.store.get_topic_messages(topic_id=10)

        self.assertEqual(result, {})
        mock_get_hash.assert_called_once_with(redis_key)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.key_exists")
    def test_message_was_sent_returns_true_when_sent_key_exists(self, mock_key_exists):
        message_id = 501
        redis_key = BOT_MESSAGE_SENT.format(message_id=message_id)
        mock_key_exists.return_value = True

        result = self.store.message_was_sent(message_id)

        self.assertTrue(result)
        mock_key_exists.assert_called_once_with(redis_key)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.key_exists")
    def test_message_was_sent_returns_false_when_sent_key_does_not_exist(self, mock_key_exists):
        message_id = 501
        redis_key = BOT_MESSAGE_SENT.format(message_id=message_id)
        mock_key_exists.return_value = False

        result = self.store.message_was_sent(message_id)

        self.assertFalse(result)
        mock_key_exists.assert_called_once_with(redis_key)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.set_value")
    def test_mark_message_as_sent_stores_sent_key_with_expected_ttl(self, mock_set_value):
        message_id = 501
        redis_key = BOT_MESSAGE_SENT.format(message_id=message_id)

        self.store.mark_message_as_sent(message_id)

        mock_set_value.assert_called_once_with(
            redis_key=redis_key,
            value="1",
            timeout=BOT_MESSAGE_SENT_TTL,
        )

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_from_hash")
    def test_get_bot_username_returns_none_when_username_does_not_exist(self, mock_get_from_hash):
        mock_get_from_hash.return_value = None

        result = self.store.get_bot_username(999)

        self.assertIsNone(result)
        mock_get_from_hash.assert_called_once_with(BOT_USERNAMES, 999)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_random_set_member")
    def test_get_random_bot_user_id_raises_value_error_for_invalid_redis_value(self, mock_get_random_set_member):
        mock_get_random_set_member.return_value = "invalid-user-id"

        with self.assertRaises(ValueError):
            self.store.get_random_bot_user_id()

        mock_get_random_set_member.assert_called_once_with(BOT_USER_IDS)

    @patch("apps.chat.infrastructure.redis.bot_message_redis_store.RedisService.get_random_set_member")
    def test_get_random_topic_id_raises_value_error_for_invalid_redis_value(self, mock_get_random_set_member):
        mock_get_random_set_member.return_value = "invalid-topic-id"

        with self.assertRaises(ValueError):
            self.store.get_random_topic_id()

        mock_get_random_set_member.assert_called_once_with(BOT_TOPIC_IDS)
