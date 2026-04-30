from unittest.mock import Mock, call, patch

from django.test import TestCase

from apps.chat.services.bot_cache_loader import BotCacheLoader
from apps.chat.tests.factories import (
    ConversationFlowFactory,
    TopicFactory,
)
from apps.users.tests.factories import UserFactory


class BotCacheLoaderTestCase(TestCase):
    def setUp(self):
        self.redis_store = Mock()
        self.loader = BotCacheLoader(redis_store=self.redis_store)

    def test_load_loads_users_topics_messages_and_marks_cache_as_loaded(self):
        user = UserFactory(username="john_bot")
        topic = TopicFactory()
        message = ConversationFlowFactory(
            topic=topic,
            message="Hello from topic!",
            is_promotional=False,
        )

        self.loader.load()

        self.redis_store.store_bot_users.assert_called_once_with(
            {
                user.id: "john_bot",
            }
        )
        self.redis_store.store_topic_ids.assert_called_once_with({topic.id})
        self.redis_store.store_topic_messages.assert_called_once_with(
            topic_id=topic.id,
            messages={
                message.id: "Hello from topic!",
            },
        )
        self.redis_store.mark_cache_as_loaded.assert_called_once_with()

    def test_load_marks_cache_as_loaded_even_when_there_is_no_data(self):
        self.loader.load()

        self.redis_store.store_bot_users.assert_called_once_with({})
        self.redis_store.store_topic_ids.assert_called_once_with(set())
        self.redis_store.store_topic_messages.assert_not_called()
        self.redis_store.mark_cache_as_loaded.assert_called_once_with()

    def test_load_bot_users_stores_non_staff_non_superuser_users(self):
        user_1 = UserFactory(username="john_bot")
        user_2 = UserFactory(username="maria_bot")

        self.loader._load_bot_users()

        self.redis_store.store_bot_users.assert_called_once_with(
            {
                user_1.id: "john_bot",
                user_2.id: "maria_bot",
            }
        )

    def test_load_bot_users_excludes_staff_users(self):
        normal_user = UserFactory(
            username="normal_bot",
            is_staff=False,
            is_superuser=False,
        )
        UserFactory(
            username="staff_user",
            is_staff=True,
            is_superuser=False,
        )

        self.loader._load_bot_users()

        self.redis_store.store_bot_users.assert_called_once_with(
            {
                normal_user.id: "normal_bot",
            }
        )

    def test_load_bot_users_excludes_superusers(self):
        normal_user = UserFactory(
            username="normal_bot",
            is_staff=False,
            is_superuser=False,
        )
        UserFactory(
            username="admin_user",
            is_staff=False,
            is_superuser=True,
        )

        self.loader._load_bot_users()

        self.redis_store.store_bot_users.assert_called_once_with(
            {
                normal_user.id: "normal_bot",
            }
        )

    def test_load_bot_users_includes_inactive_users_because_no_is_active_filter_exists(self):
        active_user = UserFactory(
            username="active_bot",
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        inactive_user = UserFactory(
            username="inactive_bot",
            is_active=False,
            is_staff=False,
            is_superuser=False,
        )

        self.loader._load_bot_users()

        self.redis_store.store_bot_users.assert_called_once_with(
            {
                active_user.id: "active_bot",
                inactive_user.id: "inactive_bot",
            }
        )

    def test_load_topics_and_messages_stores_all_topic_ids(self):
        topic_1 = TopicFactory()
        topic_2 = TopicFactory()

        self.loader._load_topics_and_messages()

        self.redis_store.store_topic_ids.assert_called_once_with(
            {
                topic_1.id,
                topic_2.id,
            }
        )

    def test_load_topics_and_messages_stores_messages_grouped_by_topic(self):
        topic_1 = TopicFactory()
        topic_2 = TopicFactory()

        message_1 = ConversationFlowFactory(
            topic=topic_1,
            message="Message from topic 1",
            is_promotional=False,
        )
        message_2 = ConversationFlowFactory(
            topic=topic_2,
            message="Message from topic 2",
            is_promotional=False,
        )

        self.loader._load_topics_and_messages()

        self.redis_store.store_topic_ids.assert_called_once_with(
            {
                topic_1.id,
                topic_2.id,
            }
        )
        self.redis_store.store_topic_messages.assert_has_calls(
            [
                call(
                    topic_id=topic_1.id,
                    messages={
                        message_1.id: "Message from topic 1",
                    },
                ),
                call(
                    topic_id=topic_2.id,
                    messages={
                        message_2.id: "Message from topic 2",
                    },
                ),
            ],
            any_order=True,
        )

    def test_load_topics_and_messages_does_not_store_topic_messages_when_topic_has_no_messages(self):
        topic = TopicFactory()

        self.loader._load_topics_and_messages()

        self.redis_store.store_topic_ids.assert_called_once_with({topic.id})
        self.redis_store.store_topic_messages.assert_not_called()

    def test_get_messages_for_topic_returns_only_non_promotional_messages(self):
        topic = TopicFactory()

        normal_message = ConversationFlowFactory(
            topic=topic,
            message="Normal message",
            is_promotional=False,
        )
        ConversationFlowFactory(
            topic=topic,
            message="Promotional message",
            is_promotional=True,
        )

        result = self.loader._get_messages_for_topic(topic.id)

        self.assertEqual(
            result,
            {
                normal_message.id: "Normal message",
            },
        )

    def test_get_messages_for_topic_does_not_include_messages_from_other_topics(self):
        topic = TopicFactory()
        other_topic = TopicFactory()

        message = ConversationFlowFactory(
            topic=topic,
            message="Correct topic message",
            is_promotional=False,
        )
        ConversationFlowFactory(
            topic=other_topic,
            message="Other topic message",
            is_promotional=False,
        )

        result = self.loader._get_messages_for_topic(topic.id)

        self.assertEqual(
            result,
            {
                message.id: "Correct topic message",
            },
        )

    def test_get_messages_for_topic_returns_empty_dict_when_topic_has_no_messages(self):
        topic = TopicFactory()

        result = self.loader._get_messages_for_topic(topic.id)

        self.assertEqual(result, {})

    def test_load_topics_and_messages_does_not_store_messages_when_topic_has_only_promotional_messages(self):
        topic = TopicFactory()

        ConversationFlowFactory(
            topic=topic,
            message="Promotional message",
            is_promotional=True,
        )

        self.loader._load_topics_and_messages()

        self.redis_store.store_topic_ids.assert_called_once_with({topic.id})
        self.redis_store.store_topic_messages.assert_not_called()

    def test_load_topics_and_messages_stores_only_topics_with_normal_messages(self):
        topic_with_normal_message = TopicFactory()
        topic_with_only_promotional_message = TopicFactory()
        topic_without_messages = TopicFactory()

        normal_message = ConversationFlowFactory(
            topic=topic_with_normal_message,
            message="Normal message",
            is_promotional=False,
        )
        ConversationFlowFactory(
            topic=topic_with_only_promotional_message,
            message="Promotional message",
            is_promotional=True,
        )

        self.loader._load_topics_and_messages()

        self.redis_store.store_topic_ids.assert_called_once_with(
            {
                topic_with_normal_message.id,
                topic_with_only_promotional_message.id,
                topic_without_messages.id,
            }
        )
        self.redis_store.store_topic_messages.assert_called_once_with(
            topic_id=topic_with_normal_message.id,
            messages={
                normal_message.id: "Normal message",
            },
        )

    def test_load_calls_loader_steps_and_marks_cache_as_loaded(self):
        with (
            patch.object(self.loader, "_load_bot_users") as mock_load_bot_users,
            patch.object(self.loader, "_load_topics_and_messages") as mock_load_topics_and_messages,
        ):
            self.loader.load()

        mock_load_bot_users.assert_called_once_with()
        mock_load_topics_and_messages.assert_called_once_with()
        self.redis_store.mark_cache_as_loaded.assert_called_once_with()
