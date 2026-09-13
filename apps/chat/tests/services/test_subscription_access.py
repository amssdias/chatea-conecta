from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from apps.chat.constants.private_chat import (
    PRIVATE_CHAT_ACCESS_FREE,
    PRIVATE_CHAT_ACCESS_PAYMENT_OVERDUE,
    PRIVATE_CHAT_ACCESS_UNLIMITED,
)
from apps.chat.services.subscription_access import resolve_private_chat_access
from apps.subscriptions.tests.factories import UserSubscriptionFactory
from apps.users.tests.factories import UserFactory


class ResolvePrivateChatAccessTests(TestCase):
    """
    This is the single switch behind the private-chat limit: everyone is capped
    at FREE_PRIVATE_CHAT_LIMIT unless this answers unlimited. Signing up is not
    what lifts the cap - paying is, and staying paid up is what keeps it lifted.
    """

    async def test_anonymous_user_is_held_at_the_free_ceiling(self):
        access = await resolve_private_chat_access(AnonymousUser())

        self.assertEqual(access, PRIVATE_CHAT_ACCESS_FREE)

    async def test_logged_in_user_without_a_subscription_is_held_at_the_free_ceiling(self):
        user = await database_sync_to_async(UserFactory)()

        access = await resolve_private_chat_access(user)

        self.assertEqual(access, PRIVATE_CHAT_ACCESS_FREE)

    async def test_active_subscription_lifts_the_ceiling(self):
        subscription = await database_sync_to_async(UserSubscriptionFactory)(active=True)

        access = await resolve_private_chat_access(subscription.user)

        self.assertEqual(access, PRIVATE_CHAT_ACCESS_UNLIMITED)

    async def test_canceled_subscription_is_held_at_the_free_ceiling(self):
        subscription = await database_sync_to_async(UserSubscriptionFactory)(canceled=True)

        access = await resolve_private_chat_access(subscription.user)

        self.assertEqual(access, PRIVATE_CHAT_ACCESS_FREE)

    async def test_past_due_subscription_is_capped_but_answered_as_a_billing_problem(self):
        """
        A past-due subscription still has a future period end, so it would read
        as Pro. The ceiling has to come back, and it must not fall through to
        the free answer: that would sell an upgrade the account already bought.
        """
        subscription = await database_sync_to_async(UserSubscriptionFactory)(past_due=True)

        access = await resolve_private_chat_access(subscription.user)

        self.assertEqual(access, PRIVATE_CHAT_ACCESS_PAYMENT_OVERDUE)
