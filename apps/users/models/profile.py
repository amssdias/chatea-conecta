from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.constants import MALE, FEMALE


class Profile(models.Model):
    GENDERS = (
        (MALE, _("Male")),
        (FEMALE, _("Female")),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user"
    )
    gender = models.CharField(max_length=1, choices=GENDERS, null=True, blank=True)
    link = models.URLField(max_length=200, null=True, blank=True)
