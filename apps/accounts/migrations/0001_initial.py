"""Migración inicial de la app de cuentas."""
import uuid

import apps.accounts.models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("display_name", models.CharField(blank=True, max_length=100, verbose_name="Nombre para mostrar")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="Teléfono")),
                ("can_view_costs", models.BooleanField(default=False, verbose_name="Puede ver costos")),
                ("can_deliver_with_balance", models.BooleanField(default=False, verbose_name="Puede entregar con saldo pendiente")),
                ("telegram_notifications_enabled", models.BooleanField(default=True, verbose_name="Notificaciones por Telegram habilitadas")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "Perfil de usuario", "verbose_name_plural": "Perfiles de usuario"},
        ),
        migrations.CreateModel(
            name="TelegramAccount",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("telegram_user_id", models.BigIntegerField(unique=True, verbose_name="ID de usuario de Telegram")),
                ("chat_id", models.BigIntegerField(unique=True, verbose_name="ID de chat de Telegram")),
                ("username", models.CharField(blank=True, max_length=100, verbose_name="Usuario de Telegram")),
                ("first_name", models.CharField(blank=True, max_length=100, verbose_name="Nombre en Telegram")),
                ("last_name", models.CharField(blank=True, max_length=100, verbose_name="Apellido en Telegram")),
                ("verified_at", models.DateTimeField(verbose_name="Verificado en")),
                ("is_active", models.BooleanField(default=True, verbose_name="Activa")),
                ("notifications_enabled", models.BooleanField(default=True, verbose_name="Notificaciones habilitadas")),
                ("muted_until", models.DateTimeField(blank=True, null=True, verbose_name="Silenciado hasta")),
                ("last_interaction_at", models.DateTimeField(blank=True, null=True, verbose_name="Última interacción")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Vinculada en")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Actualizada en")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telegram_account",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuario",
                    ),
                ),
            ],
            options={"verbose_name": "Cuenta de Telegram", "verbose_name_plural": "Cuentas de Telegram"},
        ),
        migrations.CreateModel(
            name="TelegramPairingCode",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code_hash", models.CharField(max_length=64, verbose_name="Hash del código")),
                ("expires_at", models.DateTimeField(default=apps.accounts.models._default_expiry, verbose_name="Expira en")),
                ("used_at", models.DateTimeField(blank=True, null=True, verbose_name="Usado en")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="issued_pairing_codes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Generado por",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telegram_pairing_codes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuario a vincular",
                    ),
                ),
            ],
            options={
                "verbose_name": "Código de vinculación de Telegram",
                "verbose_name_plural": "Códigos de vinculación de Telegram",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="telegrampairingcode",
            constraint=models.UniqueConstraint(
                condition=models.Q(used_at__isnull=True),
                fields=["user"],
                name="unique_active_pairing_code_per_user",
            ),
        ),
    ]
