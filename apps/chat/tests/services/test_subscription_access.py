from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from apps.chat.services.subscription_access import user_has_pro_access
from apps.subscriptions.tests.factories import UserSubscriptionFactory
from apps.users.tests.factories import UserFactory


class UserHasProAccessTests(TestCase):
    """
    This is the single switch behind the private-chat limit: everyone is capped
    at FREE_PRIVATE_CHAT_LIMIT unless this returns True. Signing up is not what
    lifts the cap - paying is.
    """

    async def test_anonymous_user_never_has_pro_access(self):
        has_access = await user_has_pro_access(AnonymousUser())

        self.assertFalse(has_access)

    async def test_logged_in_user_without_a_subscription_has_no_pro_access(self):
        user = await database_sync_to_async(UserFactory)()

        has_access = await user_has_pro_access(user)

        self.assertFalse(has_access)

    async def test_logged_in_user_with_an_active_subscription_has_pro_access(self):
        subscription = await database_sync_to_async(UserSubscriptionFactory)(active=True)

        has_access = await user_has_pro_access(subscription.user)

        self.assertTrue(has_access)

    async def test_logged_in_user_with_a_canceled_subscription_has_no_pro_access(self):
        subscription = await database_sync_to_async(UserSubscriptionFactory)(canceled=True)

        has_access = await user_has_pro_access(subscription.user)

        self.assertFalse(has_access)
