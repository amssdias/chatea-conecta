from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.chat.services.bot_message_service import BotMessageService


class BotMessageServiceTestCase(SimpleTestCase):
    def setUp(self):
        self.redis_store = Mock()
        self.cache_loader = Mock()
        self.service = BotMessageService(
            redis_store=self.redis_store,
            cache_loader=self.cache_loader,
        )

    def test_ensure_cache_is_loaded_does_not_load_when_cache_exists(self):
        self.redis_store.is_cache_loaded.return_value = True

        self.service._ensure_cache_is_loaded()

        self.redis_store.is_cache_loaded.assert_called_once_with()
        self.cache_loader.load.assert_not_called()

    def test_ensure_cache_is_loaded_loads_cache_when_cache_does_not_exist(self):
        self.redis_store.is_cache_loaded.return_value = False

        self.service._ensure_cache_is_loaded()

        self.redis_store.is_cache_loaded.assert_called_once_with()
        self.cache_loader.load.assert_called_once_with()

    def test_get_message_to_send_returns_none_when_no_bot_user_exists(self):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = None

        result = self.service.get_message_to_send()

        self.assertIsNone(result)
        self.redis_store.get_random_bot_user_id.assert_called_once_with()
        self.redis_store.get_bot_username.assert_not_called()
        self.redis_store.mark_message_as_sent.assert_not_called()

    def test_get_message_to_send_returns_none_when_username_does_not_exist(self):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = 10
        self.redis_store.get_bot_username.return_value = None

        result = self.service.get_message_to_send()

        self.assertIsNone(result)
        self.redis_store.get_bot_username.assert_called_once_with(10)
        self.redis_store.mark_message_as_sent.assert_not_called()

    @patch.object(BotMessageService, "_select_message")
    def test_get_message_to_send_returns_none_when_no_message_is_available(
            self,
            mock_select_message,
    ):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = 10
        self.redis_store.get_bot_username.return_value = "john_bot"
        mock_select_message.return_value = None

        result = self.service.get_message_to_send()

        self.assertIsNone(result)
        mock_select_message.assert_called_once_with()
        self.redis_store.mark_message_as_sent.assert_not_called()

    @patch.object(BotMessageService, "_select_message")
    def test_get_message_to_send_returns_payload_and_marks_message_as_sent(
            self,
            mock_select_message,
    ):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = 10
        self.redis_store.get_bot_username.return_value = "john_bot"
        mock_select_message.return_value = (3, 501, "Hello everyone!")

        result = self.service.get_message_to_send()

        self.assertEqual(
            result,
            {
                "user_id": 10,
                "username": "john_bot",
                "topic_id": 3,
                "message_id": 501,
                "message": "Hello everyone!",
            },
        )
        self.redis_store.mark_message_as_sent.assert_called_once_with(501)

    def test_select_message_returns_none_when_no_topic_exists(self):
        self.redis_store.get_random_topic_id.return_value = None

        result = self.service._select_message()

        self.assertIsNone(result)
        self.redis_store.get_random_topic_id.assert_called_once_with()
        self.redis_store.get_topic_messages.assert_not_called()

    def test_select_message_skips_empty_topics_until_message_is_found(self):
        self.redis_store.get_random_topic_id.side_effect = [1, 2]
        self.redis_store.get_topic_messages.side_effect = [
            {},
            {
                501: "Hello from topic 2",
            },
        ]
        self.redis_store.message_was_sent.return_value = False

        result = self.service._select_message()

        self.assertEqual(result, (2, 501, "Hello from topic 2"))
        self.assertEqual(self.redis_store.get_random_topic_id.call_count, 2)
        self.assertEqual(self.redis_store.get_topic_messages.call_count, 2)

    def test_select_message_skips_topics_where_all_messages_were_sent(self):
        self.redis_store.get_random_topic_id.side_effect = [1, 2]
        self.redis_store.get_topic_messages.side_effect = [
            {
                501: "Already sent message",
            },
            {
                502: "Available message",
            },
        ]

        self.redis_store.message_was_sent.side_effect = [
            True,
            False,
        ]

        result = self.service._select_message()

        self.assertEqual(result, (2, 502, "Available message"))
        self.assertEqual(self.redis_store.get_random_topic_id.call_count, 2)

    def test_select_message_returns_none_after_max_topic_attempts(self):
        self.redis_store.get_random_topic_id.return_value = 1
        self.redis_store.get_topic_messages.return_value = {}

        result = self.service._select_message()

        self.assertIsNone(result)
        self.assertEqual(
            self.redis_store.get_random_topic_id.call_count,
            self.service.MAX_TOPIC_ATTEMPTS,
        )
        self.assertEqual(
            self.redis_store.get_topic_messages.call_count,
            self.service.MAX_TOPIC_ATTEMPTS,
        )

    @patch("apps.chat.services.bot_message_service.random.shuffle")
    def test_select_unsent_message_returns_first_unsent_message_after_shuffle(self, mock_shuffle):
        messages = {
            501: "First message",
            502: "Second message",
        }
        self.redis_store.message_was_sent.side_effect = [True, False]

        result = self.service._select_unsent_message(messages)

        self.assertEqual(result, (502, "Second message"))
        mock_shuffle.assert_called_once()
        self.redis_store.message_was_sent.assert_any_call(501)
        self.redis_store.message_was_sent.assert_any_call(502)

    def test_select_unsent_message_returns_none_when_all_messages_were_sent(self):
        messages = {
            501: "First message",
            502: "Second message",
        }
        self.redis_store.message_was_sent.return_value = True

        result = self.service._select_unsent_message(messages)

        self.assertIsNone(result)
        self.assertEqual(self.redis_store.message_was_sent.call_count, 2)

    def test_select_unsent_message_returns_none_when_messages_are_empty(self):
        result = self.service._select_unsent_message({})

        self.assertIsNone(result)
        self.redis_store.message_was_sent.assert_not_called()

    @patch("apps.chat.services.bot_message_service.random.shuffle")
    def test_select_unsent_message_does_not_check_remaining_messages_after_finding_one(
            self,
            mock_shuffle,
    ):
        messages = {
            501: "Available message",
            502: "Should not be checked",
        }
        self.redis_store.message_was_sent.return_value = False

        result = self.service._select_unsent_message(messages)

        self.assertEqual(result, (501, "Available message"))
        self.redis_store.message_was_sent.assert_called_once_with(501)

    @patch.object(BotMessageService, "_ensure_cache_is_loaded")
    @patch.object(BotMessageService, "_select_message")
    def test_get_message_to_send_ensures_cache_before_selecting_message(
            self,
            mock_select_message,
            mock_ensure_cache_is_loaded,
    ):
        self.redis_store.get_random_bot_user_id.return_value = 10
        self.redis_store.get_bot_username.return_value = "john_bot"
        mock_select_message.return_value = (3, 501, "Hello everyone!")

        self.service.get_message_to_send()

        mock_ensure_cache_is_loaded.assert_called_once_with()
        mock_select_message.assert_called_once_with()

    @patch.object(BotMessageService, "_select_message")
    def test_get_message_to_send_does_not_select_message_when_user_id_is_missing(
            self,
            mock_select_message,
    ):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = None

        result = self.service.get_message_to_send()

        self.assertIsNone(result)
        mock_select_message.assert_not_called()

    @patch.object(BotMessageService, "_select_message")
    def test_get_message_to_send_does_not_select_message_when_username_is_missing(
            self,
            mock_select_message,
    ):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = 10
        self.redis_store.get_bot_username.return_value = ""

        result = self.service.get_message_to_send()

        self.assertIsNone(result)
        mock_select_message.assert_not_called()

    def test_select_message_returns_first_available_message_from_selected_topic(self):
        self.redis_store.get_random_topic_id.return_value = 7
        self.redis_store.get_topic_messages.return_value = {
            701: "Available message",
        }
        self.redis_store.message_was_sent.return_value = False

        result = self.service._select_message()

        self.assertEqual(result, (7, 701, "Available message"))
        self.redis_store.get_random_topic_id.assert_called_once_with()
        self.redis_store.get_topic_messages.assert_called_once_with(7)
        self.redis_store.message_was_sent.assert_called_once_with(701)

    def test_select_message_returns_none_when_topic_exists_but_messages_are_empty_until_limit(
            self,
    ):
        self.redis_store.get_random_topic_id.return_value = 1
        self.redis_store.get_topic_messages.return_value = {}

        result = self.service._select_message()

        self.assertIsNone(result)
        self.assertEqual(
            self.redis_store.get_random_topic_id.call_count,
            self.service.MAX_TOPIC_ATTEMPTS,
        )

    def test_get_message_to_send_does_not_mark_message_as_sent_when_payload_cannot_be_built(
            self,
    ):
        self.redis_store.is_cache_loaded.return_value = True
        self.redis_store.get_random_bot_user_id.return_value = 10
        self.redis_store.get_bot_username.return_value = None

        result = self.service.get_message_to_send()

        self.assertIsNone(result)
        self.redis_store.mark_message_as_sent.assert_not_called()
