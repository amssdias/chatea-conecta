from django.contrib import admin

from apps.subscriptions.models import StripeWebhookEvent, StripeInvoiceNotification


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("id", "stripe_event_id", "status")


@admin.register(StripeInvoiceNotification)
class StripeInvoiceNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "stripe_invoice_id")
