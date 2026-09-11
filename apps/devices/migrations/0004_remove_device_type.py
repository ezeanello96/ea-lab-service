"""Migración: elimina el campo device_type de Device."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0003_populate_device_categories"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="device",
            name="device_type",
        ),
    ]
