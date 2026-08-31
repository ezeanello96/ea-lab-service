"""Migración inicial de la app de tareas."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("workorders", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Task",
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
                ("title", models.CharField(max_length=200, verbose_name="Título")),
                ("description", models.TextField(blank=True, verbose_name="Descripción")),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Baja"),
                            ("medium", "Media"),
                            ("high", "Alta"),
                            ("urgent", "Urgente"),
                        ],
                        db_index=True,
                        default="medium",
                        max_length=10,
                        verbose_name="Prioridad",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendiente"),
                            ("in_progress", "En progreso"),
                            ("done", "Completada"),
                            ("cancelled", "Cancelada"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "due_date",
                    models.DateTimeField(blank=True, null=True, verbose_name="Fecha límite"),
                ),
                (
                    "completed_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Completada en"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Creada en"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Actualizada en"),
                ),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Asignado a",
                    ),
                ),
                (
                    "work_order",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tasks",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tarea",
                "verbose_name_plural": "Tareas",
                "ordering": ["-priority", "due_date"],
            },
        ),
    ]
