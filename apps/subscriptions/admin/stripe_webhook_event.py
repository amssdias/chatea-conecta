from django.contrib import admin

from apps.subscriptions.models import StripeWebhookEvent, StripeInvoiceNotification


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("id", "stripe_event_id", "event_type", "status")
    readonly_fields = ("stripe_event_id", "event_type")


@admin.register(StripeInvoiceNotification)
class StripeInvoiceNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "stripe_invoice_id", "email_type", "status")
    readonly_fields = ("stripe_invoice_id", "email_type")
