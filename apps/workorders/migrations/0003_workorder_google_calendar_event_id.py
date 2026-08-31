"""Agrega campo google_calendar_event_id a WorkOrder."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workorders", "0002_diagnosis_worklog_finaltest"),
    ]

    operations = [
        migrations.AddField(
            model_name="workorder",
            name="google_calendar_event_id",
            field=models.CharField(
                blank=True,
                help_text="Se rellena automáticamente al crear el evento desde el sistema.",
                max_length=200,
                verbose_name="ID de evento en Google Calendar",
            ),
        ),
    ]
