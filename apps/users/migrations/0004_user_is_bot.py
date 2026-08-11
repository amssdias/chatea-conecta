from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_alter_profile_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_bot",
            field=models.BooleanField(
                default=False,
                help_text="Designates whether this account is an automated chat bot.",
            ),
        ),
    ]
