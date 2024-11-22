from django.contrib import admin

from apps.users.models import Profile, User


@admin.register(Profile)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gender")
    search_fields = ("user__username",)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("id", "username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
