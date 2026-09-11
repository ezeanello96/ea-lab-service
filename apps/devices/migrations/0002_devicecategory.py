"""Migración: crea DeviceCategory y agrega FK nullable device_category a Device."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DeviceCategory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="Nombre")),
                ("is_active", models.BooleanField(default=True, verbose_name="Activa")),
            ],
            options={
                "verbose_name": "Categoría de equipo",
                "verbose_name_plural": "Categorías de equipo",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="device",
            name="device_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="devices.devicecategory",
                verbose_name="Tipo de equipo",
            ),
        ),
    ]
