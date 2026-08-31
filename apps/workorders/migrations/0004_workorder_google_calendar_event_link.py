"""Agrega campo google_calendar_event_link a WorkOrder."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workorders", "0003_workorder_google_calendar_event_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="workorder",
            name="google_calendar_event_link",
            field=models.URLField(
                blank=True,
                help_text="Enlace directo al evento. Se rellena automáticamente.",
                max_length=500,
                verbose_name="URL del evento en Google Calendar",
            ),
        ),
    ]
