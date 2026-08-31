"""Tareas Celery de la app de notificaciones."""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


class _NotificationSkipped(Exception):
    """Señaliza que el intento fue omitido intencionalmente (no es un error retriable)."""


@shared_task(
    name="notifications.send_attempt",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def send_notification_attempt(self, attempt_pk: str):
    """Envía un intento de notificación. Idempotente."""
    from apps.notifications.models import NotificationAttempt

    try:
        attempt = NotificationAttempt.objects.get(pk=attempt_pk)
    except NotificationAttempt.DoesNotExist:
        logger.warning("NotificationAttempt %s no existe", attempt_pk)
        return

    if attempt.status == NotificationAttempt.Status.SENT:
        return  # Idempotent: already sent

    attempt.status = NotificationAttempt.Status.PROCESSING
    attempt.save(update_fields=["status"])

    try:
        if attempt.channel == NotificationAttempt.Channel.INTERNAL:
            _deliver_internal(attempt)
        elif attempt.channel == NotificationAttempt.Channel.TELEGRAM:
            _deliver_telegram(attempt)

        attempt.status = NotificationAttempt.Status.SENT
        attempt.sent_at = timezone.now()
        attempt.save(update_fields=["status", "sent_at"])
        logger.info("Notification attempt %s sent", attempt_pk)

    except _NotificationSkipped as skip_reason:
        attempt.status = NotificationAttempt.Status.SKIPPED
        attempt.error_message = str(skip_reason)
        attempt.save(update_fields=["status", "error_message"])
        logger.info("Notification attempt %s skipped: %s", attempt_pk, skip_reason)

    except Exception as exc:
        logger.exception("Error sending notification attempt %s", attempt_pk)
        attempt.status = NotificationAttempt.Status.FAILED
        attempt.error_message = str(exc)
        attempt.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc)


def _deliver_internal(attempt):
    """Crea una Notification interna para el destinatario."""
    from apps.notifications.models import Notification

    Notification.objects.create(
        recipient=attempt.recipient,
        channel=Notification.Channel.INTERNAL,
        subject=attempt.subject,
        body=attempt.body,
        status=Notification.Status.SENT,
        sent_at=timezone.now(),
    )


def _deliver_telegram(attempt):
    """Envía mensaje de Telegram al destinatario del intento."""
    from apps.telegram_bot.services import send_message, get_chat_id_for_user

    if not attempt.recipient:
        raise ValueError("El intento de notificación Telegram no tiene destinatario.")

    chat_id = get_chat_id_for_user(attempt.recipient)
    if chat_id is None:
        raise _NotificationSkipped("Usuario sin cuenta Telegram activa o silenciada.")

    text = attempt.body
    if attempt.subject:
        text = f"*{attempt.subject}*\n\n{attempt.body}"

    ok = send_message(chat_id=chat_id, text=text)
    if not ok:
        raise RuntimeError(f"Fallo al enviar Telegram a chat_id={chat_id}")
