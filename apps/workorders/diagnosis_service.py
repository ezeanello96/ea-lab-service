"""Servicio de dominio para diagnósticos."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog

from .models import Diagnosis, WorkOrder, WorkOrderStatusHistory


class DiagnosisError(Exception):
    pass


class DiagnosisService:
    """Operaciones sobre diagnósticos técnicos."""

    @staticmethod
    @transaction.atomic
    def get_or_create_draft(*, work_order: WorkOrder, technician: User) -> Diagnosis:
        """Obtiene el diagnóstico existente o crea uno en borrador."""
        diagnosis, created = Diagnosis.objects.get_or_create(
            work_order=work_order,
            defaults={
                "technician": technician,
                "status": Diagnosis.Status.DRAFT,
                "started_at": timezone.now(),
            },
        )
        if created:
            AuditLog.log("create", user=technician, obj=diagnosis)
            # Avanzar la orden a IN_DIAGNOSIS si está en estado anterior
            if work_order.status in (
                WorkOrder.Status.RECEIVED,
                WorkOrder.Status.PENDING_DIAGNOSIS,
            ):
                from .services import WorkOrderService
                WorkOrderService.transition(
                    order=work_order,
                    actor=technician,
                    to_status=WorkOrder.Status.IN_DIAGNOSIS,
                    comment="Diagnóstico iniciado.",
                    source=WorkOrderStatusHistory.Source.WEB,
                )
        return diagnosis

    @staticmethod
    @transaction.atomic
    def save_draft(
        *,
        diagnosis: Diagnosis,
        actor: User,
        reported_problem_summary: str = "",
        findings: str = "",
        tests_performed: str = "",
        recommended_solution: str = "",
        risk_notes: str = "",
        repairable: bool | None = None,
        estimated_hours=None,
    ) -> Diagnosis:
        if diagnosis.is_final:
            raise DiagnosisError("No se puede editar un diagnóstico finalizado.")

        old_repr = str(diagnosis)
        diagnosis.reported_problem_summary = reported_problem_summary
        diagnosis.findings = findings
        diagnosis.tests_performed = tests_performed
        diagnosis.recommended_solution = recommended_solution
        diagnosis.risk_notes = risk_notes
        diagnosis.repairable = repairable
        diagnosis.estimated_hours = estimated_hours
        diagnosis.save()
        AuditLog.log("update", user=actor, obj=diagnosis, object_repr=old_repr)
        return diagnosis

    @staticmethod
    @transaction.atomic
    def finalize(*, diagnosis: Diagnosis, actor: User) -> Diagnosis:
        """Finaliza el diagnóstico. Requiere findings y repairable definido."""
        if diagnosis.is_final:
            raise DiagnosisError("El diagnóstico ya está finalizado.")
        if not diagnosis.findings.strip():
            raise DiagnosisError("Debe registrar los hallazgos antes de finalizar.")
        if diagnosis.repairable is None:
            raise DiagnosisError(
                "Debe indicar si el equipo tiene reparación antes de finalizar."
            )

        diagnosis.status = Diagnosis.Status.FINAL
        diagnosis.completed_at = timezone.now()
        diagnosis.save()

        order = diagnosis.work_order
        if diagnosis.repairable:
            # Pasar a esperando aprobación si el estado lo permite
            if order.status == WorkOrder.Status.IN_DIAGNOSIS:
                from .services import WorkOrderService
                WorkOrderService.transition(
                    order=order,
                    actor=actor,
                    to_status=WorkOrder.Status.AWAITING_APPROVAL,
                    comment="Diagnóstico finalizado.",
                    source=WorkOrderStatusHistory.Source.WEB,
                )
        else:
            if order.status == WorkOrder.Status.IN_DIAGNOSIS:
                from .services import WorkOrderService
                WorkOrderService.transition(
                    order=order,
                    actor=actor,
                    to_status=WorkOrder.Status.UNREPAIRABLE,
                    comment="Diagnóstico: sin reparación posible.",
                    source=WorkOrderStatusHistory.Source.WEB,
                )

        AuditLog.log("update", user=actor, obj=diagnosis, changes={"status": {"from": "DRAFT", "to": "FINAL"}})
        return diagnosis
