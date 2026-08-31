"""Tareas Celery periódicas de la app de tareas."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="tasks.check_due_reminders", bind=True, max_retries=3, acks_late=True)
def check_due_reminders(self):
    """Periodic: despacha notificaciones pendientes."""
    from apps.notifications.services import NotificationService

    try:
        count = NotificationService.dispatch_due()
        logger.info("check_due_reminders: despachados %d intentos", count)
        return count
    except Exception as exc:
        logger.exception("Error en check_due_reminders")
        raise self.retry(exc=exc)


@shared_task(name="tasks.send_morning_digest", acks_late=True)
def send_morning_digest():
    """Envía el resumen matutino a todos los usuarios activos."""
    from apps.notifications.services import NotificationService

    NotificationService.send_digest()
    logger.info("Resumen matutino enviado")
