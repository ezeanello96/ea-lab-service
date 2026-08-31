"""Servicios síncronos del bot de Telegram — para uso desde Celery y vistas Django."""
import asyncio
import logging

logger = logging.getLogger(__name__)


def send_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """
    Envía un mensaje de Telegram desde un contexto síncrono (Celery worker).
    Retorna True si se envió correctamente, False si hubo error.
    """
    from django.conf import settings

    if not settings.TELEGRAM_ENABLED or not settings.TELEGRAM_BOT_TOKEN:
        logger.debug("Telegram deshabilitado o sin token, omitiendo envío a chat_id=%s", chat_id)
        return False

    try:
        from telegram import Bot

        async def _send():
            async with Bot(settings.TELEGRAM_BOT_TOKEN) as bot:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)

        asyncio.run(_send())
        return True
    except Exception as exc:
        logger.exception("Error enviando Telegram a chat_id=%s: %s", chat_id, exc)
        return False


def get_chat_id_for_user(user) -> int | None:
    """Retorna el chat_id de Telegram del usuario, o None si no está vinculado/activo."""
    try:
        account = user.telegram_account
        if account.is_active and account.notifications_enabled and not account.is_muted:
            return account.chat_id
    except Exception:
        pass
    return None
