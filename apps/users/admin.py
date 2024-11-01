from django.contrib import admin

from apps.users.models import Profile


@admin.register(Profile)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("user", "gender")
    search_fields = ("user__username",)
