# apps/telegram_bot/management/commands/runtelegrambot.py
"""
Comando de gestión para iniciar el bot de Telegram con long polling.

Uso:
    python manage.py runtelegrambot

El comando corre indefinidamente hasta recibir SIGTERM/SIGINT.
Requiere TELEGRAM_ENABLED=1 y TELEGRAM_BOT_TOKEN en las variables de entorno.
"""
import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Inicia el bot de Telegram con long polling"

    def handle(self, *args, **options):
        if not settings.TELEGRAM_ENABLED:
            self.stdout.write(
                self.style.WARNING(
                    "Bot de Telegram deshabilitado (TELEGRAM_ENABLED=0). "
                    "Para activarlo, configurá TELEGRAM_ENABLED=1 y TELEGRAM_BOT_TOKEN en .env"
                )
            )
            return

        if not settings.TELEGRAM_BOT_TOKEN:
            self.stderr.write(
                self.style.ERROR(
                    "TELEGRAM_BOT_TOKEN no configurado. "
                    "Copiá el token de @BotFather a tu archivo .env"
                )
            )
            return

        self.stdout.write(self.style.SUCCESS("Bot de Telegram iniciando con long polling..."))

        try:
            asyncio.run(self._run_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("Bot de Telegram detenido correctamente."))

    async def _run_bot(self):
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        from apps.telegram_bot.bot import (
            cmd_start, cmd_ayuda, cmd_vincular,
            cmd_hoy, cmd_manana, cmd_pendientes, cmd_listos,
            cmd_vencidos, cmd_orden, cmd_buscar,
            cmd_nota, cmd_completar, cmd_resumen,
            cmd_silenciar, cmd_desvincular,
            handle_unknown, handle_error,
        )

        app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Registrar handlers
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("ayuda", cmd_ayuda))
        app.add_handler(CommandHandler("help", cmd_ayuda))
        app.add_handler(CommandHandler("vincular", cmd_vincular))
        app.add_handler(CommandHandler("hoy", cmd_hoy))
        app.add_handler(CommandHandler("manana", cmd_manana))
        app.add_handler(CommandHandler("mañana", cmd_manana))
        app.add_handler(CommandHandler("pendientes", cmd_pendientes))
        app.add_handler(CommandHandler("listos", cmd_listos))
        app.add_handler(CommandHandler("vencidos", cmd_vencidos))
        app.add_handler(CommandHandler("orden", cmd_orden))
        app.add_handler(CommandHandler("buscar", cmd_buscar))
        app.add_handler(CommandHandler("nota", cmd_nota))
        app.add_handler(CommandHandler("completar", cmd_completar))
        app.add_handler(CommandHandler("resumen", cmd_resumen))
        app.add_handler(CommandHandler("silenciar", cmd_silenciar))
        app.add_handler(CommandHandler("desvincular", cmd_desvincular))
        app.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
        app.add_error_handler(handle_error)

        logger.info("Bot de Telegram iniciado con long polling.")
        self.stdout.write("Bot activo. Presiona Ctrl+C para detener.")

        await app.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
