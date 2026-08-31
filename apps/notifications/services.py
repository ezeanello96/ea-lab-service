"""Servicio de notificaciones con despacho idempotente."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone


class NotificationService:

    @staticmethod
    def schedule(
        *,
        idempotency_key: str,
        recipient,
        channel: str,
        subject: str = "",
        body: str,
        scheduled_for=None,
    ):
        """
        Registra un intento de notificación. Idempotente por idempotency_key.
        Retorna (attempt, created).
        """
        from apps.notifications.models import NotificationAttempt

        attempt, created = NotificationAttempt.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "recipient": recipient,
                "channel": channel,
                "subject": subject,
                "body": body,
                "scheduled_for": scheduled_for or timezone.now(),
            },
        )
        return attempt, created

    @staticmethod
    def dispatch_due() -> int:
        """
        Despacha los intentos pendientes cuyo scheduled_for ya pasó.
        Llamado por Celery Beat cada minuto.
        Returns: cantidad de tareas despachadas.
        """
        from apps.notifications.models import NotificationAttempt
        from apps.notifications.celery_tasks import send_notification_attempt

        now = timezone.now()
        pending = (
            NotificationAttempt.objects.filter(
                status=NotificationAttempt.Status.PENDING,
                scheduled_for__lte=now,
            )
            .select_for_update(skip_locked=True)[:100]
        )
        count = 0
        for attempt in pending:
            send_notification_attempt.delay(str(attempt.pk))
            count += 1
        return count

    @staticmethod
    def send_digest() -> None:
        """Genera y programa el resumen diario interno para todos los usuarios activos."""
        from django.contrib.auth.models import User
        from apps.notifications.models import NotificationAttempt
        from apps.workorders.models import WorkOrder
        from apps.tasks.services import TaskService

        now = timezone.now()
        active_orders = WorkOrder.objects.filter(status__in=WorkOrder.ACTIVE_STATUSES).count()
        overdue_tasks = TaskService.get_overdue_count()
        ready_devices = WorkOrder.objects.filter(status=WorkOrder.Status.READY_FOR_PICKUP).count()

        date_label = now.strftime("%d/%m/%Y")
        lines = [
            f"Resumen del sistema — {date_label}",
            f"Órdenes activas: {active_orders}",
            f"Tareas vencidas: {overdue_tasks}",
            f"Equipos listos para retirar: {ready_devices}",
        ]
        body = "\n".join(lines)

        for user in User.objects.filter(is_active=True).iterator():
            key = f"digest:{now.strftime('%Y%m%d')}:{user.pk}:INTERNAL"
            NotificationService.schedule(
                idempotency_key=key,
                recipient=user,
                channel=NotificationAttempt.Channel.INTERNAL,
                subject=f"Resumen diario {date_label}",
                body=body,
                scheduled_for=now,
            )
