# Generated by Django 4.2.16 on 2024-11-25 22:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_remove_topic_is_promotional_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserConversation",
        ),
    ]
