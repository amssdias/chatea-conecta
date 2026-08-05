from django.contrib import admin

from apps.subscriptions.models import UserSubscription


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "stripe_customer_id", "stripe_subscription_id", "status")
