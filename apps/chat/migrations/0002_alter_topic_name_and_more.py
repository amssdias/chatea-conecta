# Generated by Django 4.2.11 on 2024-07-29 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="topic",
            name="name",
            field=models.CharField(max_length=22, unique=True),
        ),
        migrations.AddConstraint(
            model_name="conversationflow",
            constraint=models.UniqueConstraint(
                fields=("topic", "message"), name="unique_topic_message"
            ),
        ),
    ]
