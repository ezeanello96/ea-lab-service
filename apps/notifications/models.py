"""Modelos de notificaciones."""
import uuid

from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    """Notificación interna almacenada en BD (bandeja de entrada del usuario)."""

    class Channel(models.TextChoices):
        TELEGRAM = "TELEGRAM", "Telegram"
        INTERNAL = "INTERNAL", "Interno"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        SENT = "SENT", "Enviada"
        FAILED = "FAILED", "Fallida"
        SKIPPED = "SKIPPED", "Omitida"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="notifications", verbose_name="Destinatario",
    )
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.INTERNAL, verbose_name="Canal",
    )
    subject = models.CharField(max_length=200, blank=True, verbose_name="Asunto")
    body = models.TextField(verbose_name="Contenido")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        db_index=True, verbose_name="Estado",
    )
    error_message = models.TextField(blank=True, verbose_name="Error")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviada en")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada en")
    is_read = models.BooleanField(default=False, db_index=True, verbose_name="Leída")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Leída en")

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]

    def __str__(self):
        recipient = self.recipient.username if self.recipient else "—"
        return f"[{self.get_channel_display()}] {self.subject or self.body[:50]} → {recipient}"


class NotificationAttempt(models.Model):
    """
    Registro de despacho de notificaciones con clave de idempotencia.
    Formato de idempotency_key: {event}:{entity_pk}:{recipient_pk}:{date}:{channel}
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        PROCESSING = "PROCESSING", "Procesando"
        SENT = "SENT", "Enviado"
        FAILED = "FAILED", "Fallido"
        SKIPPED = "SKIPPED", "Omitido"

    class Channel(models.TextChoices):
        TELEGRAM = "TELEGRAM", "Telegram"
        INTERNAL = "INTERNAL", "Interno"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idempotency_key = models.CharField(
        max_length=255, unique=True, verbose_name="Clave de idempotencia",
        help_text="Formato: {evento}:{entidad}:{destinatario}:{fecha}:{canal}",
    )
    recipient = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="notification_attempts", verbose_name="Destinatario",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices, verbose_name="Canal")
    subject = models.CharField(max_length=200, blank=True, verbose_name="Asunto")
    body = models.TextField(verbose_name="Contenido")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
        db_index=True, verbose_name="Estado",
    )
    error_message = models.TextField(blank=True, verbose_name="Error")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado en")
    scheduled_for = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Programado para")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Intento de notificación"
        verbose_name_plural = "Intentos de notificación"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.channel}] {self.idempotency_key} → {self.status}"
