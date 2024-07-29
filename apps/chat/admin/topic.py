from django.contrib import admin

from apps.chat.models import Topic


@admin.register(Topic)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
