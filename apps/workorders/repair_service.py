"""Servicio de dominio para reparación, WorkLog y pruebas finales."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog

from .models import FinalTest, WorkLog, WorkOrder


class RepairError(Exception):
    pass


class RepairService:
    """Operaciones de reparación, logs de trabajo y pruebas finales."""

    @staticmethod
    @transaction.atomic
    def add_log(
        *,
        work_order: WorkOrder,
        actor: User,
        description: str,
        entry_type: str = WorkLog.EntryType.NOTE,
        minutes_spent: int | None = None,
        is_customer_visible: bool = False,
    ) -> WorkLog:
        log = WorkLog.objects.create(
            work_order=work_order,
            author=actor,
            entry_type=entry_type,
            description=description,
            minutes_spent=minutes_spent,
            is_customer_visible=is_customer_visible,
        )
        return log

    @staticmethod
    @transaction.atomic
    def add_final_test(
        *,
        work_order: WorkOrder,
        actor: User,
        name: str,
    ) -> FinalTest:
        test = FinalTest.objects.create(
            work_order=work_order,
            name=name,
            status=FinalTest.TestStatus.PENDING,
        )
        return test

    @staticmethod
    @transaction.atomic
    def set_test_result(
        *,
        test: FinalTest,
        actor: User,
        status: str,
        notes: str = "",
    ) -> FinalTest:
        if status not in FinalTest.TestStatus.values:
            raise RepairError(f"Estado de prueba inválido: {status}")
        test.status = status
        test.notes = notes
        test.tested_by = actor
        test.tested_at = timezone.now()
        test.save()
        return test

    @staticmethod
    def validate_ready_for_pickup(work_order: WorkOrder) -> list[str]:
        """Retorna lista de errores que impiden marcar la orden como lista para retirar.

        Si la lista está vacía, la orden puede avanzar a READY_FOR_PICKUP.
        """
        errors: list[str] = []
        tests = list(work_order.final_tests.all())
        if not tests:
            errors.append(
                "La orden no tiene pruebas finales registradas. "
                "Debe agregar y completar al menos una prueba antes de marcar como lista."
            )
            return errors

        pending = [t for t in tests if t.status == FinalTest.TestStatus.PENDING]
        failed = [t for t in tests if t.status == FinalTest.TestStatus.FAILED]

        if pending:
            names = ", ".join(t.name for t in pending)
            errors.append(f"Pruebas pendientes: {names}.")
        if failed:
            names = ", ".join(t.name for t in failed)
            errors.append(
                f"Pruebas con fallo: {names}. "
                "Debe marcarlas como No aplica o resolverlas antes de continuar."
            )
        return errors

    @staticmethod
    def get_total_minutes(work_order: WorkOrder) -> int:
        """Suma de minutos invertidos en todos los WorkLog de la orden."""
        result = work_order.work_logs.filter(
            minutes_spent__isnull=False
        ).aggregate(total=__import__("django.db.models", fromlist=["Sum"]).Sum("minutes_spent"))
        return result["total"] or 0
