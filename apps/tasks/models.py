"""Modelos de tareas internas del taller."""
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En progreso"
        COMPLETED = "COMPLETED", "Completada"
        CANCELLED = "CANCELLED", "Cancelada"

    class Priority(models.TextChoices):
        LOW = "LOW", "Baja"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "Alta"
        URGENT = "URGENT", "Urgente"

    ACTIVE_STATUSES = {Status.PENDING, Status.IN_PROGRESS}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(blank=True, verbose_name="Descripción")
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.NORMAL,
        db_index=True, verbose_name="Prioridad",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        db_index=True, verbose_name="Estado",
    )
    due_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha límite", db_index=True)
    snoozed_until = models.DateTimeField(null=True, blank=True, verbose_name="Pospuesta hasta")
    recurrence_rule = models.CharField(
        max_length=100, blank=True, verbose_name="Regla de recurrencia",
        help_text="Por ejemplo: daily, weekly. Vacío = sin recurrencia.",
    )
    # Optional relations
    work_order = models.ForeignKey(
        "workorders.WorkOrder", null=True, blank=True, on_delete=models.CASCADE,
        related_name="tasks", verbose_name="Orden de trabajo",
    )
    customer = models.ForeignKey(
        "customers.Customer", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tasks", verbose_name="Cliente",
    )
    device = models.ForeignKey(
        "devices.Device", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tasks", verbose_name="Equipo",
    )
    assigned_to = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_tasks", verbose_name="Asignado a",
    )
    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL,
        related_name="created_tasks", verbose_name="Creado por",
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completada en")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ["-priority", "due_at"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return (
            self.due_at is not None
            and timezone.now() > self.due_at
            and self.status in self.ACTIVE_STATUSES
        )

    @property
    def is_snoozed(self):
        return self.snoozed_until is not None and timezone.now() < self.snoozed_until


class Reminder(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        PROCESSING = "PROCESSING", "Procesando"
        SENT = "SENT", "Enviado"
        FAILED = "FAILED", "Fallido"
        CANCELLED = "CANCELLED", "Cancelado"

    class Channel(models.TextChoices):
        TELEGRAM = "TELEGRAM", "Telegram"
        INTERNAL = "INTERNAL", "Interno"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="reminders", verbose_name="Tarea")
    scheduled_at = models.DateTimeField(verbose_name="Programado para", db_index=True)
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.INTERNAL, verbose_name="Canal",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        db_index=True, verbose_name="Estado",
    )
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado en")
    error_message = models.TextField(blank=True, verbose_name="Error")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recordatorio"
        verbose_name_plural = "Recordatorios"
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"Recordatorio para «{self.task.title}» el {self.scheduled_at:%d/%m/%Y %H:%M}"
