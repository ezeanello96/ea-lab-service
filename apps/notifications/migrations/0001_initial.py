"""Migración inicial de la app de notificaciones."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
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
                    "channel",
                    models.CharField(
                        choices=[
                            ("telegram", "Telegram"),
                            ("internal", "Interna (sistema)"),
                        ],
                        default="internal",
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                (
                    "subject",
                    models.CharField(blank=True, max_length=200, verbose_name="Asunto"),
                ),
                ("body", models.TextField(verbose_name="Contenido")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("sent", "Enviada"),
                            ("failed", "Fallida"),
                            ("skipped", "Omitida (horario de silencio)"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="Mensaje de error"),
                ),
                (
                    "sent_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Enviada en"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Creada en"),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Destinatario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notificación",
                "verbose_name_plural": "Notificaciones",
                "ordering": ["-created_at"],
            },
        ),
    ]
