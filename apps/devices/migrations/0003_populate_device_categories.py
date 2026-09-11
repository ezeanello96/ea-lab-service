"""Migración de datos: crea categorías por defecto y asigna device_category a devices existentes."""
from django.db import migrations

CATEGORIES = [
    "All-in-One",
    "Consola",
    "Impresora",
    "Monitor",
    "Notebook / Laptop",
    "Otro",
    "PC de escritorio",
    "Servidor",
]

DEVICE_TYPE_TO_CATEGORY = {
    "DESKTOP": "PC de escritorio",
    "NOTEBOOK": "Notebook / Laptop",
    "ALL_IN_ONE": "All-in-One",
    "SERVER": "Servidor",
    "PRINTER": "Impresora",
    "MONITOR": "Monitor",
    "CONSOLE": "Consola",
    "OTHER": "Otro",
}


def populate_categories(apps, schema_editor):
    DeviceCategory = apps.get_model("devices", "DeviceCategory")
    Device = apps.get_model("devices", "Device")

    # Crear categorías
    for name in CATEGORIES:
        DeviceCategory.objects.get_or_create(name=name)

    # Asignar categorías a devices existentes
    for device_type_value, category_name in DEVICE_TYPE_TO_CATEGORY.items():
        category = DeviceCategory.objects.get(name=category_name)
        Device.objects.filter(device_type=device_type_value).update(device_category=category)


def reverse_populate(apps, schema_editor):
    DeviceCategory = apps.get_model("devices", "DeviceCategory")
    DeviceCategory.objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0002_devicecategory"),
    ]

    operations = [
        migrations.RunPython(populate_categories, reverse_populate),
    ]
