"""Migración: actualiza Notification con TextChoices, agrega is_read/read_at, crea NotificationAttempt."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Update Notification channel choices to uppercase
        migrations.AlterField(
            model_name="notification",
            name="channel",
            field=models.CharField(
                choices=[("TELEGRAM", "Telegram"), ("INTERNAL", "Interno")],
                default="INTERNAL",
                max_length=20,
                verbose_name="Canal",
            ),
        ),
        # Update Notification status choices to uppercase
        migrations.AlterField(
            model_name="notification",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pendiente"),
                    ("SENT", "Enviada"),
                    ("FAILED", "Fallida"),
                    ("SKIPPED", "Omitida"),
                ],
                db_index=True,
                default="PENDING",
                max_length=20,
                verbose_name="Estado",
            ),
        ),
        # Add is_read to Notification
        migrations.AddField(
            model_name="notification",
            name="is_read",
            field=models.BooleanField(db_index=True, default=False, verbose_name="Leída"),
        ),
        # Add read_at to Notification
        migrations.AddField(
            model_name="notification",
            name="read_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Leída en"),
        ),
        # Create NotificationAttempt model
        migrations.CreateModel(
            name="NotificationAttempt",
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
                    "idempotency_key",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        verbose_name="Clave de idempotencia",
                        help_text="Formato: {evento}:{entidad}:{destinatario}:{fecha}:{canal}",
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("TELEGRAM", "Telegram"), ("INTERNAL", "Interno")],
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                ("subject", models.CharField(blank=True, max_length=200, verbose_name="Asunto")),
                ("body", models.TextField(verbose_name="Contenido")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("PROCESSING", "Procesando"),
                            ("SENT", "Enviado"),
                            ("FAILED", "Fallido"),
                            ("SKIPPED", "Omitido"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                ("error_message", models.TextField(blank=True, verbose_name="Error")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="Enviado en")),
                (
                    "scheduled_for",
                    models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Programado para"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                (
                    "recipient",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notification_attempts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Destinatario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Intento de notificación",
                "verbose_name_plural": "Intentos de notificación",
                "ordering": ["-created_at"],
            },
        ),
    ]
