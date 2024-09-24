from django.contrib import admin

from apps.chat.models import ConversationFlow


@admin.register(ConversationFlow)
class ConversationFlowAdmin(admin.ModelAdmin):
    list_display = ("topic", "message")
    search_fields = ("topic", "message")
