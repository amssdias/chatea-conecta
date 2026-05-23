from django.contrib import admin

from apps.subscriptions.models import UserSubscription


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("stripe_customer_id",)
    # search_fields = ("topic", "message")
