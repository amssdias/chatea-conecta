from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from apps.chat.services.subscription_access import user_has_pro_access


class UserHasProAccessTests(TestCase):
    async def test_anonymous_user_never_has_pro_access(self):
        has_access = await user_has_pro_access(AnonymousUser())

        self.assertFalse(has_access)
