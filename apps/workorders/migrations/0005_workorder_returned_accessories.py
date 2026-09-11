"""Migración: agrega campo returned_accessories a WorkOrder."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workorders", "0004_workorder_google_calendar_event_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="workorder",
            name="returned_accessories",
            field=models.TextField(
                blank=True,
                verbose_name="Accesorios devueltos",
                help_text="Accesorios entregados al cliente al momento de la devolución del equipo.",
            ),
        ),
    ]
