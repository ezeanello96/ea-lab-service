"""Migración inicial de la app core."""
import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BusinessSettings",
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
                    "business_name",
                    models.CharField(max_length=200, verbose_name="Nombre del negocio"),
                ),
                (
                    "legal_name",
                    models.CharField(blank=True, max_length=200, verbose_name="Razón social"),
                ),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="Teléfono")),
                ("email", models.EmailField(blank=True, verbose_name="Email")),
                ("address", models.TextField(blank=True, verbose_name="Dirección")),
                (
                    "currency_code",
                    models.CharField(
                        default="ARS", max_length=3, verbose_name="Código de moneda"
                    ),
                ),
                (
                    "timezone",
                    models.CharField(
                        default="America/Argentina/Cordoba",
                        max_length=50,
                        verbose_name="Zona horaria",
                    ),
                ),
                (
                    "order_prefix",
                    models.CharField(
                        default="OT",
                        help_text='Por ejemplo: "OT" generará OT-0001, OT-0002...',
                        max_length=10,
                        verbose_name="Prefijo de órdenes",
                    ),
                ),
                (
                    "default_warranty_days",
                    models.PositiveIntegerField(
                        default=30, verbose_name="Días de garantía por defecto"
                    ),
                ),
                (
                    "default_diagnosis_hours",
                    models.PositiveIntegerField(
                        default=48, verbose_name="Horas de diagnóstico por defecto"
                    ),
                ),
                (
                    "quiet_hours_start",
                    models.TimeField(
                        default="21:00", verbose_name="Inicio de horario de silencio"
                    ),
                ),
                (
                    "quiet_hours_end",
                    models.TimeField(
                        default="08:00", verbose_name="Fin de horario de silencio"
                    ),
                ),
                (
                    "morning_digest_time",
                    models.TimeField(
                        default="08:00", verbose_name="Hora del resumen matutino"
                    ),
                ),
                (
                    "evening_digest_time",
                    models.TimeField(
                        blank=True, null=True, verbose_name="Hora del resumen vespertino"
                    ),
                ),
                (
                    "warranty_terms",
                    models.TextField(blank=True, verbose_name="Términos de garantía"),
                ),
                (
                    "quote_terms",
                    models.TextField(blank=True, verbose_name="Términos de presupuesto"),
                ),
                (
                    "receipt_terms",
                    models.TextField(blank=True, verbose_name="Términos del recibo"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Creado en"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Actualizado en"),
                ),
            ],
            options={
                "verbose_name": "Configuración del negocio",
                "verbose_name_plural": "Configuración del negocio",
            },
        ),
    ]
