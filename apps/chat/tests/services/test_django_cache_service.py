import time
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from faker import Faker

from apps.chat.constants.redis_keys import (
    USER_IDS,
    TOPIC_IDS,
    USER_PROMOTIONAL_IDS,
)
from apps.chat.models import ConversationFlow
from apps.chat.services import DjangoCacheService
from apps.chat.tests.factories.conversation_flow_factory import ConversationFlowFactory
from apps.chat.tests.factories.topic_factory import TopicFactory
from apps.users.tests.factories.profile import ProfileFactory
from apps.users.tests.factories.user_factory import UserFactory

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
            "apps.chat.services.django_cache_service.User.objects.filter"
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

    def test_get_cached_promotional_user_ids_cache_miss(self):
        """Test that promotional user IDs are fetched from DB when cache is empty."""

        profile1 = ProfileFactory(with_link=True)
        profile2 = ProfileFactory(with_link=True)
        profile3 = ProfileFactory(with_link=True)

        promotional_user_ids = {profile1.user.id, profile2.user.id, profile3.user.id}

        result = self.cache_service.get_cached_user_ids(promotional=True)

        self.assertEqual(result, promotional_user_ids)

        # Check if the result is now in the cache for promotional IDs
        cached_result = cache.get(USER_PROMOTIONAL_IDS)
        self.assertEqual(cached_result, promotional_user_ids)

    def test_get_cached_promotional_user_ids_cache_hit(self):
        """Test that promotional user IDs are fetched from cache when available."""

        profile = ProfileFactory(with_link=True)
        promotional_user_ids = {profile.user.id}

        # Manually set cache for promotional user IDs
        cache.set(USER_PROMOTIONAL_IDS, promotional_user_ids, timeout=300)

        with patch(
            "apps.chat.services.django_cache_service.User.objects.filter"
        ) as mock_filter:
            result = self.cache_service.get_cached_user_ids(promotional=True)

            mock_filter.assert_not_called()
            self.assertEqual(result, promotional_user_ids)

    def test_get_cached_user_ids_mixed_cache(self):
        """Test both promotional and regular user IDs when one is cached and the other is not."""

        user1 = UserFactory(username="username-1")
        user2 = UserFactory(username="username-2")
        regular_user_ids = {user1.id, user2.id}

        profile1 = ProfileFactory(with_link=True)
        profile2 = ProfileFactory(with_link=True)
        promotional_user_ids = {profile1.user.id, profile2.user.id}

        # Cache only regular user IDs
        cache.set(USER_IDS, regular_user_ids, timeout=300)

        with patch(
            "apps.chat.services.django_cache_service.User.objects.filter"
        ) as mock_filter:
            mock_filter.return_value.values_list.return_value = promotional_user_ids

            # Test promotional user IDs (cache miss)
            result_promotional = self.cache_service.get_cached_user_ids(
                promotional=True
            )
            self.assertEqual(result_promotional, promotional_user_ids)
            mock_filter.assert_called_once_with(profile__link__isnull=False)

            # Test regular user IDs (cache hit)
            result_regular = self.cache_service.get_cached_user_ids(promotional=False)
            self.assertEqual(result_regular, regular_user_ids)

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

            result = self.cache_service.get_cached_topic_ids()

        # Ensure the result is the mocked data and was cached
        self.assertEqual(result, mock_topic_ids)

        cached_data = cache.get(TOPIC_IDS)
        self.assertEqual(cached_data, mock_topic_ids)

    def test_get_cached_conversation_flows_with_no_cached_data(self):
        [ConversationFlowFactory(topic=self.topic, is_promotional=False) for _ in range(5)]
        conversation_flows_list = list(
            ConversationFlow.objects.filter(topic=self.topic, is_promotional=False).values_list(
                "id", "message"
            )
        )

        # Call the get_cached_conversation_flows method
        result = self.cache_service.get_cached_conversation_flows(topic_id=1, promotional=False)

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
            result = self.cache_service.get_cached_conversation_flows(topic_id=1, promotional=False)

        # Ensure the method returned the cached data
        self.assertEqual(result, cached_conversation_flows)

        # Ensure that the DB fetch function was not called (because data is cached)
        mock_filter.assert_not_called()

    def test_get_cached_conversation_flows_with_custom_timeout(self):
        topic = TopicFactory()

        [ConversationFlowFactory(topic=topic, is_promotional=False) for _ in range(5)]
        conversation_flows_list = list(
            ConversationFlow.objects.filter(topic=topic, is_promotional=False).values_list("id", "message")
        )

        # Call the get_cached_conversation_flows method
        result = self.cache_service.get_cached_conversation_flows(topic_id=topic.id, promotional=False)

        # Assert that the result matches the mocked data
        self.assertEqual(result, conversation_flows_list)

        # Ensure the data was cached with the correct cache key
        cache_key = f"conversation_flows_topic_{topic.id}"
        cached_data = cache.get(cache_key)
        self.assertEqual(cached_data, conversation_flows_list)

        # Ensure that the cache was set with the custom timeout
        # If needed, you can validate cache timeout behavior (advanced setup-environment-test of cache expiration)

    def test_get_cached_conversation_flows_promotional_with_no_cached_data(self):
        # Create promotional conversation flows
        [ConversationFlowFactory(topic=self.topic, is_promotional=True) for _ in range(5)]
        conversation_flows_list = list(
            ConversationFlow.objects.filter(topic=self.topic, is_promotional=True).values_list("id", "message")
        )

        # Call the get_cached_conversation_flows method
        result = self.cache_service.get_cached_conversation_flows(topic_id=self.topic.id, promotional=True)

        # Assert that the result matches the mocked data
        self.assertEqual(result, conversation_flows_list)

        # Ensure the data was cached with the correct cache key
        cache_key = f"conversation_flows_promotional_topic_{self.topic.id}"
        cached_data = cache.get(cache_key)
        self.assertEqual(cached_data, conversation_flows_list)

    def test_get_cached_conversation_flows_promotional_with_cached_data(self):
        # Prepopulate the cache with promotional conversation flows
        cache_key = f"conversation_flows_promotional_topic_{self.topic.id}"
        cached_conversation_flows = [
            (cf.id, cf.message) for cf in [ConversationFlowFactory(topic=self.topic, is_promotional=True) for _ in range(5)]
        ]

        cache.set(
            cache_key, cached_conversation_flows, timeout=settings.CACHE_TIMEOUT_ONE_DAY
        )

        with patch(
            "apps.chat.services.django_cache_service.ConversationFlow.objects.filter"
        ) as mock_filter:

            # Call the get_cached_conversation_flows method
            result = self.cache_service.get_cached_conversation_flows(topic_id=self.topic.id, promotional=True)

        # Ensure the method returned the cached data
        self.assertEqual(result, cached_conversation_flows)

        # Ensure that the DB fetch function was not called
        mock_filter.assert_not_called()

    def test_get_cached_conversation_flows_with_empty_dataset(self):
        result = self.cache_service.get_cached_conversation_flows(topic_id=self.topic.id, promotional=False)

        # Assert the result is empty
        self.assertEqual(result, [])

        # Check cache to ensure an empty list was stored
        cache_key = f"conversation_flows_topic_{self.topic.id}"
        cached_data = cache.get(cache_key)
        self.assertEqual(cached_data, [])

    def test_get_cached_conversation_flows_invalid_topic_id(self):
        # Call the method with a non-existent topic_id
        result = self.cache_service.get_cached_conversation_flows(topic_id=99999, promotional=False)

        # Assert the result is empty
        self.assertEqual(result, [])

    def test_get_cached_conversation_flows_cache_expiration(self):
        # Create conversation flows and cache them
        cache_key = f"conversation_flows_topic_{self.topic.id}"
        conversation_flows = [
            (cf.id, cf.message) for cf in [ConversationFlowFactory(topic=self.topic, is_promotional=False) for _ in range(5)]
        ]

        cache.set(
            cache_key, conversation_flows, timeout=1  # Cache expiration in 1 second
        )

        # Wait for cache to expire
        import time
        time.sleep(2)

        # Call the method and ensure the cache is repopulated
        result = self.cache_service.get_cached_conversation_flows(topic_id=self.topic.id, promotional=False)

        # Assert that the result matches the database contents
        self.assertEqual(len(result), len(conversation_flows))

        # Check the cache was refreshed
        cached_data = cache.get(cache_key)
        self.assertEqual(cached_data, result)

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
    def test_mark_user_message_sent_in_redis_with_default_timeout(self, mock_cache_set):
        user_id = 1
        topic_id = 1
        message_id = 1
        message = "Hello"
        expected_cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )

        self.cache_service.mark_user_message_sent_in_redis(
            user_id, topic_id, message_id, message
        )

        mock_cache_set.assert_called_once_with(
            expected_cache_key, message, timeout=86400 # One day
        )

    @patch("apps.chat.services.django_cache_service.cache.set")
    def test_mark_user_message_sent_in_redis_with_custom_timeout(self, mock_cache_set):
        user_id = 1
        topic_id = 1
        message_id = 1
        message = "Hello"
        expected_cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        custom_timeout = settings.CACHE_TIMEOUT_FIVE_MIN
        self.cache_service.mark_user_message_sent_in_redis(
            user_id, topic_id, message_id, message, timeout=custom_timeout
        )

        mock_cache_set.assert_called_once_with(
            expected_cache_key, message, timeout=custom_timeout
        )

    def test_mark_user_message_sent_in_redis_integration_with_cache_default_timeout(self):
        user_id = 1
        topic_id = 1
        message_id = 1
        message = "Hello"
        expected_cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )

        self.cache_service.mark_user_message_sent_in_redis(
            user_id, topic_id, message_id, message
        )

        cached_value = cache.get(expected_cache_key)
        self.assertEqual(cached_value, message)

    def test_mark_user_message_sent_in_redis_integration_with_cache_custom_timeout(self):
        user_id = 1
        topic_id = 1
        message_id = 1
        message = "Hello"
        expected_cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )
        custom_timeout = settings.CACHE_TIMEOUT_FIVE_MIN
        self.cache_service.mark_user_message_sent_in_redis(
            user_id, topic_id, message_id, message, timeout=custom_timeout
        )

        cached_value = cache.get(expected_cache_key)
        self.assertEqual(cached_value, message)

    def test_message_not_in_cache_after_timeout_integration(self):
        user_id = 1
        topic_id = 1
        message_id = 1
        message = "Hello"
        expected_cache_key = self.cache_service.USER_MESSAGE_SENT.format(
            user_id=user_id, topic_id=topic_id, message_id=message_id
        )

        self.cache_service.mark_user_message_sent_in_redis(
            user_id, topic_id, message_id, message, timeout=2
        )

        # Wait for cache to expire
        time.sleep(2)

        # Ensure the cache is empty after timeout
        cached_value = cache.get(expected_cache_key)
        self.assertIsNone(cached_value)
