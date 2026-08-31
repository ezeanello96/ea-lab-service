"""Migración: actualiza Task con TextChoices y nuevos campos, crea Reminder."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0001_initial"),
        ("devices", "0001_initial"),
        ("tasks", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Rename due_date → due_at
        migrations.RenameField(
            model_name="task",
            old_name="due_date",
            new_name="due_at",
        ),
        # Update priority choices to uppercase TextChoices
        migrations.AlterField(
            model_name="task",
            name="priority",
            field=models.CharField(
                choices=[
                    ("LOW", "Baja"),
                    ("NORMAL", "Normal"),
                    ("HIGH", "Alta"),
                    ("URGENT", "Urgente"),
                ],
                db_index=True,
                default="NORMAL",
                max_length=10,
                verbose_name="Prioridad",
            ),
        ),
        # Update status choices to uppercase TextChoices
        migrations.AlterField(
            model_name="task",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pendiente"),
                    ("IN_PROGRESS", "En progreso"),
                    ("COMPLETED", "Completada"),
                    ("CANCELLED", "Cancelada"),
                ],
                db_index=True,
                default="PENDING",
                max_length=20,
                verbose_name="Estado",
            ),
        ),
        # Add db_index to due_at
        migrations.AlterField(
            model_name="task",
            name="due_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Fecha límite"),
        ),
        # Add snoozed_until
        migrations.AddField(
            model_name="task",
            name="snoozed_until",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Pospuesta hasta"),
        ),
        # Add recurrence_rule
        migrations.AddField(
            model_name="task",
            name="recurrence_rule",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="Regla de recurrencia",
                help_text="Por ejemplo: daily, weekly. Vacío = sin recurrencia.",
            ),
        ),
        # Add customer FK
        migrations.AddField(
            model_name="task",
            name="customer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to="customers.customer",
                verbose_name="Cliente",
            ),
        ),
        # Add device FK
        migrations.AddField(
            model_name="task",
            name="device",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tasks",
                to="devices.device",
                verbose_name="Equipo",
            ),
        ),
        # Add created_by FK
        migrations.AddField(
            model_name="task",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_tasks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Creado por",
            ),
        ),
        # Rename related_name for assigned_to
        migrations.AlterField(
            model_name="task",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_tasks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Asignado a",
            ),
        ),
        # Update ordering in Meta
        migrations.AlterModelOptions(
            name="task",
            options={
                "ordering": ["-priority", "due_at"],
                "verbose_name": "Tarea",
                "verbose_name_plural": "Tareas",
            },
        ),
        # Create Reminder model
        migrations.CreateModel(
            name="Reminder",
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
                    "scheduled_at",
                    models.DateTimeField(db_index=True, verbose_name="Programado para"),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("TELEGRAM", "Telegram"), ("INTERNAL", "Interno")],
                        default="INTERNAL",
                        max_length=20,
                        verbose_name="Canal",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("PROCESSING", "Procesando"),
                            ("SENT", "Enviado"),
                            ("FAILED", "Fallido"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="Enviado en")),
                ("error_message", models.TextField(blank=True, verbose_name="Error")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reminders",
                        to="tasks.task",
                        verbose_name="Tarea",
                    ),
                ),
            ],
            options={
                "verbose_name": "Recordatorio",
                "verbose_name_plural": "Recordatorios",
                "ordering": ["scheduled_at"],
            },
        ),
    ]
