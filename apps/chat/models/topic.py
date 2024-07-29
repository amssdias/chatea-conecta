from django.db import models


class Topic(models.Model):
    name = models.CharField(max_length=22, unique=True)

    def __str__(self):
        return self.name
