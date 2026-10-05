from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import site
from django.test import TestCase
from django.urls import reverse

from apps.users.admin import UserAdmin
from apps.users.models import User
from apps.users.tests.factories import UserFactory


@patch("apps.users.admin.BotMessageRedisStore")
class TestUserAdminBotCache(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("admin:users_user_changelist")
        cls.staff = UserFactory(is_staff=True, is_superuser=True)

    def setUp(self):
        self.client.force_login(self.staff)

    def run_action(self, action, user):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                self.url,
                {"action": action, "_selected_action": [user.pk]},
            )

    def test_mark_as_bot_clears_cache_loaded_flag(self, mock_store):
        user = UserFactory(is_bot=False)

        self.run_action("mark_as_bot", user)

        user.refresh_from_db()
        self.assertTrue(user.is_bot)
        mock_store.return_value.clear_cache_loaded_flag.assert_called_once_with()

    def test_unmark_as_bot_clears_cache_loaded_flag(self, mock_store):
        user = UserFactory(is_bot=True)

        self.run_action("unmark_as_bot", user)

        user.refresh_from_db()
        self.assertFalse(user.is_bot)
        mock_store.return_value.clear_cache_loaded_flag.assert_called_once_with()

    def test_list_edit_of_is_bot_clears_cache_loaded_flag(self, mock_store):
        user = UserFactory(is_bot=False)

        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                self.url,
                {
                    "form-TOTAL_FORMS": "1",
                    "form-INITIAL_FORMS": "1",
                    "form-0-id": str(user.pk),
                    "form-0-is_bot": "on",
                    "_save": "Save",
                },
            )

        user.refresh_from_db()
        self.assertTrue(user.is_bot)
        mock_store.return_value.clear_cache_loaded_flag.assert_called_once_with()

    def test_flag_is_not_cleared_before_the_commit(self, mock_store):
        user = UserFactory(is_bot=False)

        with self.captureOnCommitCallbacks(execute=False):
            self.client.post(
                self.url,
                {"action": "mark_as_bot", "_selected_action": [user.pk]},
            )

        mock_store.return_value.clear_cache_loaded_flag.assert_not_called()

    def test_saving_other_fields_keeps_cache_loaded_flag(self, mock_store):
        user = UserFactory(is_bot=True)
        form = SimpleNamespace(changed_data=["email"])

        with self.captureOnCommitCallbacks(execute=True):
            UserAdmin(User, site).save_model(
                request=None, obj=user, form=form, change=True
            )

        mock_store.return_value.clear_cache_loaded_flag.assert_not_called()
