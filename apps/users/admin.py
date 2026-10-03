from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction

from apps.chat.infrastructure.redis.bot_message_redis_store import (
    BotMessageRedisStore,
)
from apps.users.models import Profile, User


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gender", "link")
    search_fields = ("user__username",)
    list_filter = ("gender",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_bot", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("id", "username", "email", "first_name", "last_name", "is_staff", "is_bot")
    list_editable = ("is_bot",)
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("is_active", "is_bot", "is_staff", "is_superuser")
    actions = ("mark_as_bot", "unmark_as_bot")

    @admin.action(description="Mark selected users as bots")
    def mark_as_bot(self, request, queryset):
        updated = queryset.update(is_bot=True)
        self._reload_bot_cache_on_commit()
        self.message_user(request, f"{updated} user(s) marked as bots.")

    @admin.action(description="Unmark selected users as bots")
    def unmark_as_bot(self, request, queryset):
        updated = queryset.update(is_bot=False)
        self._reload_bot_cache_on_commit()
        self.message_user(request, f"{updated} user(s) unmarked as bots.")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if "is_bot" in form.changed_data:
            self._reload_bot_cache_on_commit()

    @staticmethod
    def _reload_bot_cache_on_commit():
        # Cleared after the commit: a bot tick that reloads the cache before the
        # new is_bot value is visible would cache the old bot list for a week.
        transaction.on_commit(BotMessageRedisStore().clear_cache_loaded_flag)
