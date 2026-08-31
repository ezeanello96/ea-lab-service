"""Servicios de dominio para órdenes de trabajo."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.customers.models import Customer
from apps.devices.models import Device

from .models import OrderSequence, WorkOrder, WorkOrderStatusHistory


class WorkOrderNumberError(Exception):
    pass


class InvalidStatusTransition(Exception):
    pass


def _generate_order_number(prefix: str = "OT") -> str:
    """Genera un número único OT-AAAA-NNNNN con bloqueo de fila transaccional."""
    year = timezone.now().year
    seq, _ = OrderSequence.objects.select_for_update().get_or_create(year=year)
    seq.last_value += 1
    seq.save(update_fields=["last_value"])
    return f"{prefix}-{year}-{seq.last_value:05d}"


class WorkOrderService:
    """Operaciones de negocio sobre órdenes de trabajo."""

    @staticmethod
    @transaction.atomic
    def create_order(
        *,
        actor: User,
        customer: Customer,
        device: Device,
        reported_issue: str,
        priority: str = WorkOrder.Priority.NORMAL,
        source: str = WorkOrder.Source.WALK_IN,
        assigned_to: User | None = None,
        intake_condition: str = "",
        received_accessories: str = "",
        internal_notes: str = "",
        diagnosis_due_at=None,
        promised_delivery_at=None,
        related_order: WorkOrder | None = None,
        relation_type: str = "",
    ) -> WorkOrder:
        from django.conf import settings

        prefix = getattr(settings, "ORDER_PREFIX", "OT")
        number = _generate_order_number(prefix)

        order = WorkOrder(
            number=number,
            customer=customer,
            device=device,
            reported_issue=reported_issue,
            priority=priority,
            source=source,
            assigned_to=assigned_to,
            intake_condition=intake_condition,
            received_accessories=received_accessories,
            internal_notes=internal_notes,
            diagnosis_due_at=diagnosis_due_at,
            promised_delivery_at=promised_delivery_at,
            related_order=related_order,
            relation_type=relation_type,
            status=WorkOrder.Status.RECEIVED,
            created_by=actor,
        )
        order.save()

        WorkOrderStatusHistory.objects.create(
            work_order=order,
            from_status="",
            to_status=WorkOrder.Status.RECEIVED,
            comment="Orden creada.",
            actor=actor,
            source=WorkOrderStatusHistory.Source.WEB,
        )

        AuditLog.log("create", user=actor, obj=order)
        return order

    @staticmethod
    @transaction.atomic
    def transition(
        *,
        order: WorkOrder,
        actor: User,
        to_status: str,
        comment: str = "",
        source: str = WorkOrderStatusHistory.Source.WEB,
    ) -> WorkOrder:
        if not order.can_transition_to(to_status):
            raise InvalidStatusTransition(
                f"No se puede pasar de '{order.get_status_display()}' "
                f"a '{WorkOrder.Status(to_status).label}'."
            )

        from_status = order.status
        order.status = to_status

        if to_status == WorkOrder.Status.READY_FOR_PICKUP:
            order.ready_at = timezone.now()
        elif to_status == WorkOrder.Status.DELIVERED:
            order.delivered_at = timezone.now()
        elif to_status == WorkOrder.Status.CANCELLED:
            order.cancelled_at = timezone.now()
            if comment:
                order.cancel_reason = comment

        order.save()

        WorkOrderStatusHistory.objects.create(
            work_order=order,
            from_status=from_status,
            to_status=to_status,
            comment=comment,
            actor=actor,
            source=source,
        )

        AuditLog.log(
            "status_change",
            user=actor,
            obj=order,
            changes={"status": {"from": from_status, "to": to_status}},
        )
        return order

    @staticmethod
    @transaction.atomic
    def force_transition(
        *,
        order: WorkOrder,
        actor: User,
        to_status: str,
        reason: str,
        source: str = WorkOrderStatusHistory.Source.WEB,
    ) -> WorkOrder:
        """Transición administrativa que omite las reglas normales. Requiere motivo."""
        if not reason.strip():
            raise ValueError("Se requiere un motivo para forzar una transición.")
        if not actor.is_staff:
            raise PermissionError("Solo administradores pueden forzar transiciones.")

        from_status = order.status
        order.status = to_status
        order.save(update_fields=["status", "updated_at"])

        WorkOrderStatusHistory.objects.create(
            work_order=order,
            from_status=from_status,
            to_status=to_status,
            comment=f"[FORZADO] {reason}",
            actor=actor,
            source=source,
        )
        AuditLog.log(
            "status_change",
            user=actor,
            obj=order,
            changes={"status": {"from": from_status, "to": to_status}, "forced": True},
        )
        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(
        *,
        order: WorkOrder,
        actor: User,
        reason: str,
        source: str = WorkOrderStatusHistory.Source.WEB,
    ) -> WorkOrder:
        if order.status == WorkOrder.Status.CANCELLED:
            return order
        return WorkOrderService.transition(
            order=order,
            actor=actor,
            to_status=WorkOrder.Status.CANCELLED,
            comment=reason,
            source=source,
        )
