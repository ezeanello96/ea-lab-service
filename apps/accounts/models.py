"""Modelos de cuentas de usuario, perfiles y vinculación con Telegram."""
import hashlib
import secrets
import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """Perfil extendido del usuario del sistema."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=100, blank=True, verbose_name="Nombre para mostrar")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    can_view_costs = models.BooleanField(
        default=False,
        verbose_name="Puede ver costos",
        help_text="Permite ver los costos internos de las órdenes de trabajo.",
    )
    can_deliver_with_balance = models.BooleanField(
        default=False,
        verbose_name="Puede entregar con saldo pendiente",
        help_text="Permite entregar equipos aunque el cliente tenga saldo pendiente.",
    )
    telegram_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="Notificaciones por Telegram habilitadas",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return self.display_name or self.user.get_full_name() or self.user.username

    def get_display_name(self):
        return self.display_name or self.user.get_full_name() or self.user.username


class TelegramAccount(models.Model):
    """Cuenta de Telegram vinculada a un usuario interno del sistema."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="telegram_account",
        verbose_name="Usuario",
    )
    telegram_user_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID de usuario de Telegram",
    )
    chat_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID de chat de Telegram",
        help_text="Para el MVP el chat_id coincide con telegram_user_id en chats privados.",
    )
    username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Usuario de Telegram",
        help_text="Sin el símbolo @",
    )
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Nombre en Telegram")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Apellido en Telegram")
    verified_at = models.DateTimeField(verbose_name="Verificado en")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    notifications_enabled = models.BooleanField(
        default=True, verbose_name="Notificaciones habilitadas"
    )
    muted_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Silenciado hasta",
        help_text="Si está definido y es futuro, no se envían notificaciones no urgentes.",
    )
    last_interaction_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Última interacción"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vinculada en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizada en")

    class Meta:
        verbose_name = "Cuenta de Telegram"
        verbose_name_plural = "Cuentas de Telegram"

    def __str__(self):
        return f"@{self.username}" if self.username else str(self.telegram_user_id)

    @property
    def is_muted(self) -> bool:
        if self.muted_until is None:
            return False
        return timezone.now() < self.muted_until


def _default_expiry():
    return timezone.now() + timedelta(minutes=10)


class TelegramPairingCode(models.Model):
    """Código temporal para vincular una cuenta de Telegram con un usuario interno.

    El código en texto plano nunca se persiste: solo se guarda su hash SHA-256.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="telegram_pairing_codes",
        verbose_name="Usuario a vincular",
    )
    code_hash = models.CharField(
        max_length=64,
        verbose_name="Hash del código",
        help_text="SHA-256 del código en texto plano. El código plano no se guarda.",
    )
    expires_at = models.DateTimeField(default=_default_expiry, verbose_name="Expira en")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Usado en")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="issued_pairing_codes",
        verbose_name="Generado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Código de vinculación de Telegram"
        verbose_name_plural = "Códigos de vinculación de Telegram"
        ordering = ["-created_at"]
        # Solo un código activo por usuario
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(used_at__isnull=True),
                name="unique_active_pairing_code_per_user",
            )
        ]

    def __str__(self):
        return f"Código para {self.user.username} (expira {self.expires_at})"

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and timezone.now() < self.expires_at

    @classmethod
    def generate_for_user(cls, user: User, created_by: User) -> tuple["TelegramPairingCode", str]:
        """Genera un nuevo código de vinculación.

        Invalida códigos anteriores no usados del mismo usuario.
        Retorna (instancia, código_en_texto_plano).
        El texto plano debe mostrarse una sola vez y nunca guardarse.
        """
        cls.objects.filter(user=user, used_at__isnull=True).update(used_at=timezone.now())
        plain_code = secrets.token_urlsafe(6).upper()[:8]
        code_hash = hashlib.sha256(plain_code.encode()).hexdigest()
        instance = cls.objects.create(user=user, code_hash=code_hash, created_by=created_by)
        return instance, plain_code

    @classmethod
    def verify(cls, plain_code: str) -> "TelegramPairingCode | None":
        """Verifica un código en texto plano y retorna la instancia si es válida."""
        code_hash = hashlib.sha256(plain_code.encode()).hexdigest()
        try:
            instance = cls.objects.select_related("user").get(code_hash=code_hash)
        except cls.DoesNotExist:
            return None
        return instance if instance.is_valid else None
