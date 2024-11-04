from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch
from django.core.cache import cache
from django.conf import settings
from faker import Faker

from apps.chat.constants.redis_keys import USER_IDS, TOPIC_IDS
from apps.chat.models import ConversationFlow
from apps.chat.services import DjangoCacheService
from apps.chat.tests.factories.conversation_flow_factory import ConversationFlowFactory
from apps.chat.tests.factories.topic_factory import TopicFactory
from apps.chat.tests.factories.user_factory import UserFactory

User = get_user_model()
fake = Faker()


class DjangoCacheServiceTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.cache_service = DjangoCacheService()
        cls.topic = TopicFactory()

    def setUp(self):
        cache.clear()

    def test_get_or_set_cache_with_cached_data(self):
        cache.set("test_key", {1, 2, 3})

        result = self.cache_service._get_or_set_cache(
            cache_key="test_key", fetch_function=lambda: {4, 5, 6}, timeout=300
        )

        self.assertEqual(result, {1, 2, 3})

    def test_get_or_set_cache_with_no_cached_data(self):
        self.assertIsNone(cache.get("test_key"))

        fetch_function = lambda: {4, 5, 6}

        result = self.cache_service._get_or_set_cache(
            cache_key="test_key", fetch_function=fetch_function, timeout=300
        )

        self.assertEqual(result, {4, 5, 6})
        self.assertEqual(cache.get("test_key"), {4, 5, 6})

    def test_get_or_set_cache_with_custom_timeout(self):
        self.assertIsNone(cache.get("custom_timeout_key"))

        fetch_function = lambda: {7, 8, 9}

        result = self.cache_service._get_or_set_cache(
            cache_key="custom_timeout_key", fetch_function=fetch_function, timeout=600
        )

        # Assert that the cache was updated with the fetched data
        self.assertEqual(result, {7, 8, 9})
        self.assertEqual(cache.get("custom_timeout_key"), {7, 8, 9})

    def test_get_cached_user_ids_cache_miss(self):
        """Test that users are fetched from DB when cache is empty."""

        mock_user_ids = {1, 2, 3}
        with patch(
            "apps.chat.services.django_cache_service.User.objects.all"
        ) as mock_all:
            mock_all.return_value.values_list.return_value = mock_user_ids

            result = self.cache_service.get_cached_user_ids()

            self.assertEqual(result, mock_user_ids)
            mock_all.assert_called_once()

            # Check if the result is now in the cache
            cached_result = cache.get(USER_IDS)
            self.assertEqual(cached_result, mock_user_ids)

    def test_get_cached_user_ids_cache_hit(self):
        """Test that users are fetched from cache when available."""
        mock_user_ids = {1, 2, 3}

        # Set cache manually
        cache.set(USER_IDS, mock_user_ids, timeout=300)

        # Call the method
        with patch(
            "apps.chat.services.django_cache_service.User.objects.all"
        ) as mock_all:
            result = self.cache_service.get_cached_user_ids()

            mock_all.assert_not_called()
            self.assertEqual(result, mock_user_ids)

    def test_get_cached_topic_ids_with_no_cached_data(self):
        self.assertIsNone(cache.get(TOPIC_IDS))

        # Mocking the Topic query to simulate fetching from the DB
        with patch(
            "apps.chat.services.django_cache_service.Topic.objects.all"
        ) as mock_all:
            mock_topic_ids = {1, 2, 3}
            mock_all.return_value.values_list.return_value = mock_topic_ids

            # Call the get_cached_topic_ids method
            result = self.cache_service.get_cached_topic_ids()

        # Assert that the result matches the mocked data
        self.assertEqual(result, mock_topic_ids)

        # Ensure the data was cached
        cached_data = cache.get(TOPIC_IDS)
        self.assertEqual(cached_data, mock_topic_ids)

    def test_get_cached_topic_ids_with_cached_data(self):
        # Prepopulate the cache with topic IDs
        cache.set(TOPIC_IDS, {4, 5, 6}, timeout=settings.CACHE_TIMEOUT_ONE_DAY)

        with patch(
            "apps.chat.services.django_cache_service.Topic.objects.all"
        ) as mock_all:
            # Call the get_cached_topic_ids method
            result = self.cache_service.get_cached_topic_ids()

        # Ensure the method returned the cached data
        self.assertEqual(result, {4, 5, 6})

        # Ensure that the DB fetch function was not called (because data is cached)
        mock_all.assert_not_called()

    def test_get_cached_topic_ids_with_custom_timeout(self):
        # Mocking the Topic query to simulate fetching from the DB
        with patch(
            "apps.chat.services.django_cache_service.Topic.objects.all"
        ) as mock_all:

            mock_topic_ids = {7, 8, 9}
            mock_all.return_value.values_list.return_value = mock_topic_ids

            # Call the get_cached_topic_ids method, which internally uses the _get_or_set_cache method
            result = self.cache_service.get_cached_topic_ids()

        # Ensure the result is the mocked data and was cached
        self.assertEqual(result, mock_topic_ids)

        # Ensure the data was cached with the custom timeout
        cached_data = cache.get(TOPIC_IDS)
        self.assertEqual(cached_data, mock_topic_ids)

        # You can also check the cache timeout here by adjusting cache.get() in Django"s low-level API

    def test_get_cached_conversation_flows_with_no_cached_data(self):
        [ConversationFlowFactory(topic=self.topic) for _ in range(5)]
        conversation_flows_list = list(
            ConversationFlow.objects.filter(topic=self.topic).values_list("id", "message")
        )

        # Call the get_cached_conversation_flows method
        result = self.cache_service.get_cached_conversation_flows(topic_id=1)

        # Assert that the result matches the mocked data
        self.assertEqual(result, conversation_flows_list)

        # Ensure the data was cached with the correct cache key
        cache_key = f"conversation_flows_topic_{self.topic.id}"
        cached_data = cache.get(cache_key)
        self.assertEqual(cached_data, conversation_flows_list)

    def test_get_cached_conversation_flows_with_cached_data(self):
        # Prepopulate the cache with conversation flows
        cache_key = "conversation_flows_topic_1"
        cached_conversation_flows = [
            ConversationFlowFactory(topic=self.topic) for _ in range(5)
        ]

        cache.set(
            cache_key, cached_conversation_flows, timeout=settings.CACHE_TIMEOUT_ONE_DAY
        )
        with patch(
            "apps.chat.services.django_cache_service.ConversationFlow.objects.filter"
        ) as mock_filter:

            # Call the get_cached_conversation_flows method
            result = self.cache_service.get_cached_conversation_flows(topic_id=1)

        # Ensure the method returned the cached data
        self.assertEqual(result, cached_conversation_flows)

        # Ensure that the DB fetch function was not called (because data is cached)
        mock_filter.assert_not_called()

    def test_get_cached_conversation_flows_with_custom_timeout(self):
        topic = TopicFactory()

        [ConversationFlowFactory(topic=topic) for _ in range(5)]
        conversation_flows_list = list(ConversationFlow.objects.filter(topic=topic).values_list("id", "message"))

        # Call the get_cached_conversation_flows method
        result = self.cache_service.get_cached_conversation_flows(topic_id=topic.id)

        # Assert that the result matches the mocked data
        self.assertEqual(result, conversation_flows_list)

        # Ensure the data was cached with the correct cache key
        cache_key = f"conversation_flows_topic_{topic.id}"
        cached_data = cache.get(cache_key)
        self.assertEqual(cached_data, conversation_flows_list)

        # Ensure that the cache was set with the custom timeout
        # If needed, you can validate cache timeout behavior (advanced setup-environment-test of cache expiration)

    def test_get_cached_conversation_flows_filter_with_no_cached_data(self):
        conversation_flows = [
            ConversationFlowFactory(topic=self.topic) for _ in range(5)
        ]
        # Call the get_cached_conversation_flows method
        result = self.cache_service.get_cached_conversation_flows(
            topic_id=self.topic.id
        )

        # Assert that the result matches the mocked data
        self.assertEqual(len(result), len(conversation_flows))

    def test_get_username_from_cache(self):
        """Test when username is already in the cache."""
        user = UserFactory()
        cache_key = f"username_{user.id}"
        cache.set(cache_key, user.username, timeout=settings.CACHE_TIMEOUT_ONE_MONTH)

        result = self.cache_service.get_username(user_id=user.id)

        self.assertEqual(result, user.username)
        # Ensure no DB query is made
        with patch(
            "apps.chat.services.django_cache_service.User.objects.get"
        ) as mock_get:
            self.cache_service.get_username(user_id=user.id)
            mock_get.assert_not_called()

    def test_get_username_from_db_and_cache_it(self):
        """Test when username is not in cache and fetched from the DB."""
        user = UserFactory()

        with patch(
            "apps.chat.services.django_cache_service.User.objects.get",
            return_value=user,
        ) as mock_get:
            result = self.cache_service.get_username(user_id=user.id)

            # Ensure the DB query was made
            mock_get.assert_called_once_with(id=user.id)

            # Check that the username is returned correctly
            self.assertEqual(result, user.username)

            # Ensure the username is cached after being fetched from the DB
            cached_username = cache.get(f"username_{user.id}")
            self.assertEqual(cached_username, user.username)

    @patch("apps.chat.services.django_cache_service.cache.get")
    @patch("apps.chat.services.django_cache_service.cache.set")
    def test_get_username_cached(self, mock_cache_set, mock_cache_get):
        user_id = 1
        username = fake.user_name()
        mock_cache_get.return_value = username  # Simulate cache returning a username

        result = self.cache_service.get_username(user_id)

        self.assertEqual(result, username)
        mock_cache_get.assert_called_once_with(f"username_{user_id}")
        mock_cache_set.assert_not_called()  # Cache set should not be called

    @patch("apps.chat.services.django_cache_service.cache.get")
    @patch("apps.chat.services.django_cache_service.cache.set")
    def test_get_username_existing_user(self, mock_cache_set, mock_cache_get):
        user = User.objects.create(username=fake.user_name())
        mock_cache_get.return_value = None  # Simulate cache miss
        mock_cache_set.return_value = None  # Simulate successful cache set

        result = self.cache_service.get_username(user.id)

        self.assertEqual(result, user.username)
        mock_cache_get.assert_called_once_with(f"username_{user.id}")
        mock_cache_set.assert_called_once_with(
            f"username_{user.id}",
            user.username,
            timeout=settings.CACHE_TIMEOUT_ONE_MONTH,
        )

    @patch("apps.chat.services.django_cache_service.cache.get")
    @patch("apps.chat.services.django_cache_service.cache.set")
    @patch("apps.chat.services.django_cache_service.User.objects.create")
    def test_get_username_nonexistent_user(
        self, mock_user_create, mock_cache_set, mock_cache_get
    ):
        # Arrange
        user_id = 3
        mock_cache_get.return_value = None  # Simulate cache miss
        mock_user_create.return_value.username = (
            fake.user_name()
        )  # Simulate created user's username

        result = self.cache_service.get_username(user_id)

        self.assertTrue(mock_user_create.called)  # Ensure a new user is created
        self.assertEqual(
            result, mock_user_create.return_value.username
        )  # Check if the returned username is the one generated
        mock_cache_get.assert_called_once_with(f"username_{user_id}")
        mock_cache_set.assert_called_once_with(
            f"username_{user_id}",
            mock_user_create.return_value.username,
            timeout=settings.CACHE_TIMEOUT_ONE_MONTH,
        )

    def test_has_user_sent_message(self):
        user_id = 1
        topic_id = 1
        message_id = 1
        cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        cache.set(cache_key, True, timeout=settings.CACHE_TIMEOUT_ONE_DAY)

        result = self.cache_service.has_user_sent_message(user_id, topic_id, message_id)

        self.assertTrue(result)

    def test_has_user_sent_message_false(self):
        result = self.cache_service.has_user_sent_message(1, 1, 1)
        self.assertFalse(result)

    @patch("apps.chat.services.django_cache_service.cache.get")
    def test_has_user_sent_message_cache_hit(self, mock_cache_get):
        user_id = 1
        topic_id = 1
        message_id = 1
        cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        mock_cache_get.return_value = True  # Simulate cache hit

        result = self.cache_service.has_user_sent_message(user_id, topic_id, message_id)

        self.assertTrue(result)
        mock_cache_get.assert_called_once_with(cache_key)

    @patch("apps.chat.services.django_cache_service.cache.get")
    def test_has_user_sent_message_cache_miss(self, mock_cache_get):
        user_id = 1
        topic_id = 1
        message_id = 1
        cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        mock_cache_get.return_value = None  # Simulate cache miss

        # Act
        result = self.cache_service.has_user_sent_message(user_id, topic_id, message_id)

        # Assert
        self.assertFalse(result)
        mock_cache_get.assert_called_once_with(cache_key)

    @patch("apps.chat.services.django_cache_service.cache.set")
    def test_mark_user_message_sent_in_redis(self, mock_cache_set):
        user_id = 1
        topic_id = 1
        message_id = 1
        expected_cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        expected_timeout = (
            settings.CACHE_TIMEOUT_ONE_DAY
        )

        message = "Hello"
        self.cache_service.mark_user_message_sent_in_redis(
            user_id, topic_id, message_id, message
        )

        mock_cache_set.assert_called_once_with(
            expected_cache_key, message, timeout=expected_timeout
        )
