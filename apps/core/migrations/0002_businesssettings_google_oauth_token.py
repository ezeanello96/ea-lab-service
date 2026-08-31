"""Agrega campo google_oauth_token a BusinessSettings."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="businesssettings",
            name="google_oauth_token",
            field=models.TextField(
                blank=True,
                help_text="JSON con access_token y refresh_token. Se gestiona automáticamente.",
                verbose_name="Token OAuth de Google Calendar",
            ),
        ),
    ]
