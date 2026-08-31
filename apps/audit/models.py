"""Modelos de auditoría del sistema."""
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    """
    Registro de auditoría de acciones relevantes del sistema.
    Almacena quién hizo qué, cuándo y desde dónde.
    """

    # Acciones predefinidas
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_LOGIN_FAILED = "login_failed"
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_VIEW = "view"
    ACTION_EXPORT = "export"
    ACTION_PAYMENT = "payment"
    ACTION_STATUS_CHANGE = "status_change"
    ACTION_DELIVER = "deliver"
    ACTION_OTHER = "other"

    ACTION_CHOICES = [
        (ACTION_LOGIN, "Inicio de sesión"),
        (ACTION_LOGOUT, "Cierre de sesión"),
        (ACTION_LOGIN_FAILED, "Intento de inicio de sesión fallido"),
        (ACTION_CREATE, "Creación"),
        (ACTION_UPDATE, "Modificación"),
        (ACTION_DELETE, "Eliminación"),
        (ACTION_VIEW, "Visualización"),
        (ACTION_EXPORT, "Exportación"),
        (ACTION_PAYMENT, "Pago"),
        (ACTION_STATUS_CHANGE, "Cambio de estado"),
        (ACTION_DELIVER, "Entrega"),
        (ACTION_OTHER, "Otro"),
    ]

    class Source(models.TextChoices):
        WEB = "WEB", "Web"
        API = "API", "API"
        TELEGRAM = "TELEGRAM", "Telegram"
        SYSTEM = "SYSTEM", "Sistema"

    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="Actor",
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEB,
        db_index=True,
        verbose_name="Origen",
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        verbose_name="Acción",
    )
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Tipo de contenido",
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="ID del objeto",
    )
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Representación del objeto",
    )
    changes = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Cambios realizados",
        help_text="Diccionario con los valores antes y después del cambio.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP",
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha y hora",
    )

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["actor", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]

    def __str__(self):
        username = self.actor.username if self.actor else "Anónimo"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {username} → {self.get_action_display()}"

    @classmethod
    def log(
        cls,
        action,
        user=None,
        request=None,
        obj=None,
        object_repr="",
        changes=None,
    ):
        """
        Método conveniente para registrar un evento de auditoría.

        Uso:
            AuditLog.log("create", user=request.user, obj=work_order, request=request)
        """
        ip_address = None
        user_agent = ""

        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

        content_type = None
        object_id = ""

        if obj is not None:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = str(obj.pk)
            if not object_repr:
                object_repr = str(obj)[:500]

        source = cls.Source.WEB
        if request is not None and getattr(request, "is_telegram", False):
            source = cls.Source.TELEGRAM

        return cls.objects.create(
            actor=user,
            source=source,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            ip_address=ip_address or None,
            user_agent=user_agent,
        )
