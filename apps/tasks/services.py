"""Servicio de dominio para la gestión de tareas."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone


class TaskError(Exception):
    pass


class TaskService:

    @staticmethod
    @transaction.atomic
    def create_task(
        *,
        title: str,
        description: str = "",
        priority: str = "NORMAL",
        due_at=None,
        work_order=None,
        customer=None,
        device=None,
        assigned_to=None,
        created_by=None,
        recurrence_rule: str = "",
    ):
        from apps.tasks.models import Task

        task = Task.objects.create(
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
            work_order=work_order,
            customer=customer,
            device=device,
            assigned_to=assigned_to,
            created_by=created_by,
            recurrence_rule=recurrence_rule,
        )
        return task

    @staticmethod
    @transaction.atomic
    def complete(task, actor):
        from apps.tasks.models import Task

        if task.status not in Task.ACTIVE_STATUSES:
            raise TaskError("La tarea ya está finalizada o cancelada.")
        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "completed_at", "updated_at"])
        return task

    @staticmethod
    @transaction.atomic
    def cancel(task, actor):
        from apps.tasks.models import Task

        if task.status not in Task.ACTIVE_STATUSES:
            raise TaskError("La tarea ya está finalizada o cancelada.")
        task.status = Task.Status.CANCELLED
        task.save(update_fields=["status", "updated_at"])
        return task

    @staticmethod
    @transaction.atomic
    def snooze(task, actor, *, until):
        from apps.tasks.models import Task

        if task.status not in Task.ACTIVE_STATUSES:
            raise TaskError("No se puede posponer una tarea finalizada.")
        if until <= timezone.now():
            raise TaskError("La fecha de posposición debe ser en el futuro.")
        task.snoozed_until = until
        task.save(update_fields=["snoozed_until", "updated_at"])
        return task

    @staticmethod
    @transaction.atomic
    def reschedule(task, actor, *, due_at):
        task.due_at = due_at
        task.save(update_fields=["due_at", "updated_at"])
        return task

    @staticmethod
    def get_overdue_count() -> int:
        from apps.tasks.models import Task

        return Task.objects.filter(
            due_at__lt=timezone.now(),
            status__in=Task.ACTIVE_STATUSES,
        ).count()
