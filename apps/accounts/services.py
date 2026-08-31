"""Servicios de la app de cuentas."""
import logging

from django.contrib.auth.models import User

from .models import TelegramPairingCode

logger = logging.getLogger(__name__)


def generate_telegram_pairing_code(user: User) -> TelegramPairingCode:
    """
    Genera un código de vinculación de Telegram para el usuario dado.
    Invalida cualquier código previo no utilizado.
    """
    code = TelegramPairingCode.generate_for_user(user)
    logger.info("Código de vinculación de Telegram generado para %s", user.username)
    return code


def link_telegram_account(user: User, telegram_id: int, username: str = "", first_name: str = ""):
    """
    Vincula una cuenta de Telegram al usuario dado.
    Retorna el TelegramAccount creado o actualizado.
    """
    from .models import TelegramAccount

    account, created = TelegramAccount.objects.update_or_create(
        user=user,
        defaults={
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "is_active": True,
        },
    )
    action = "Creada" if created else "Actualizada"
    logger.info("%s cuenta de Telegram para %s (ID: %d)", action, user.username, telegram_id)
    return account
