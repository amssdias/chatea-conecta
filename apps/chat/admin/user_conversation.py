from django.contrib import admin

from apps.chat.models import UserConversation


@admin.register(UserConversation)
class UserConversationAdmin(admin.ModelAdmin):
    list_display = ("user", "conversation_flow", "created_at")
