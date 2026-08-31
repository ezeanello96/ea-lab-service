"""Migración inicial de la app de equipos."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Device",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "device_type",
                    models.CharField(
                        choices=[
                            ("DESKTOP", "PC de escritorio"),
                            ("NOTEBOOK", "Notebook / Laptop"),
                            ("ALL_IN_ONE", "All-in-One"),
                            ("SERVER", "Servidor"),
                            ("PRINTER", "Impresora"),
                            ("MONITOR", "Monitor"),
                            ("CONSOLE", "Consola"),
                            ("OTHER", "Otro"),
                        ],
                        default="DESKTOP",
                        max_length=20,
                        verbose_name="Tipo de equipo",
                    ),
                ),
                ("brand", models.CharField(blank=True, max_length=100, verbose_name="Marca")),
                ("model", models.CharField(blank=True, max_length=100, verbose_name="Modelo")),
                ("serial_number", models.CharField(blank=True, max_length=100, verbose_name="Número de serie")),
                (
                    "alias",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        verbose_name="Alias",
                        help_text="Nombre corto para identificar el equipo rápidamente.",
                    ),
                ),
                ("operating_system", models.CharField(blank=True, max_length=100, verbose_name="Sistema operativo")),
                ("cpu", models.CharField(blank=True, max_length=150, verbose_name="Procesador")),
                ("ram_description", models.CharField(blank=True, max_length=100, verbose_name="Memoria RAM")),
                ("storage_description", models.CharField(blank=True, max_length=150, verbose_name="Almacenamiento")),
                ("gpu_description", models.CharField(blank=True, max_length=150, verbose_name="Tarjeta de video")),
                ("permanent_notes", models.TextField(blank=True, verbose_name="Observaciones permanentes")),
                (
                    "primary_photo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="devices/photos/",
                        verbose_name="Foto principal",
                    ),
                ),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Activo")),
                ("deactivated_at", models.DateTimeField(blank=True, null=True, verbose_name="Desactivado en")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Registrado en")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_devices",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creado por",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="devices",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Equipo",
                "verbose_name_plural": "Equipos",
                "ordering": ["customer__full_name", "brand", "model"],
            },
        ),
    ]
