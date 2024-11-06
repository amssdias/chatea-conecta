from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=22, unique=True)
    is_promotional = models.BooleanField(default=False)

    def __str__(self):
        return self.name
