# Generated by Django 4.2.15 on 2024-11-06 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="is_promotional",
            field=models.BooleanField(default=False),
        ),
    ]