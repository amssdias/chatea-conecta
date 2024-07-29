from django.contrib import admin

from apps.chat.models import ConversationFlow


@admin.register(ConversationFlow)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("topic", "message")
    search_fields = ("topic", "message")
