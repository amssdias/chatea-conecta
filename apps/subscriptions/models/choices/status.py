from django.db import models


class Status(models.TextChoices):
    INACTIVE = "inactive", "Inactive"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELED = "canceled", "Canceled"
    EXPIRED = "expired", "Expired"
