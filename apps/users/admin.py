from django.contrib import admin

from apps.users.models import Profile, User


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gender", "link")
    search_fields = ("user__username",)
    list_filter = ("gender",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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
        self.message_user(request, f"{updated} user(s) marked as bots.")

    @admin.action(description="Unmark selected users as bots")
    def unmark_as_bot(self, request, queryset):
        updated = queryset.update(is_bot=False)
        self.message_user(request, f"{updated} user(s) unmarked as bots.")
