# Generated by Django 4.2.15 on 2024-11-06 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="link",
            field=models.URLField(blank=True, null=True),
        ),
    ]
