"""Servicios de dominio para presupuestos."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.workorders.models import WorkOrder

from .models import Quote, QuoteItem


class QuoteError(Exception):
    pass


class QuoteService:
    """Operaciones sobre presupuestos versionados."""

    @staticmethod
    @transaction.atomic
    def create_version(*, work_order: WorkOrder, actor: User) -> Quote:
        """Crea una nueva versión de presupuesto para la orden.

        Si existe una versión DRAFT o SENT activa, la marca como REPLACED.
        """
        existing = work_order.quotes.filter(
            status__in=[Quote.Status.DRAFT, Quote.Status.SENT]
        ).first()
        if existing:
            old_status = existing.status
            existing.status = Quote.Status.REPLACED
            existing.save(update_fields=["status", "updated_at"])
            AuditLog.log(
                "update",
                user=actor,
                obj=existing,
                changes={"status": {"from": old_status, "to": Quote.Status.REPLACED}},
            )

        last_version = work_order.quotes.aggregate(
            max_v=__import__("django.db.models", fromlist=["Max"]).Max("version")
        )["max_v"] or 0

        from django.conf import settings
        business = None
        try:
            from apps.core.models import BusinessSettings
            business = BusinessSettings.objects.filter().first()
        except Exception:
            pass

        quote = Quote.objects.create(
            work_order=work_order,
            version=last_version + 1,
            status=Quote.Status.DRAFT,
            currency_code=getattr(settings, "CURRENCY_CODE", "ARS"),
            terms=getattr(business, "quote_terms", "") if business else "",
            created_by=actor,
        )
        AuditLog.log("create", user=actor, obj=quote)
        return quote

    @staticmethod
    @transaction.atomic
    def add_or_update_item(
        *,
        quote: Quote,
        actor: User,
        position: int,
        item_type: str,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        internal_unit_cost: Decimal | None = None,
        item_id: str | None = None,
    ) -> QuoteItem:
        if not quote.is_editable:
            raise QuoteError("Solo se pueden editar ítems en presupuestos en borrador.")

        if item_id:
            item = QuoteItem.objects.get(pk=item_id, quote=quote)
        else:
            item = QuoteItem(quote=quote)

        item.position = position
        item.item_type = item_type
        item.description = description
        item.quantity = quantity
        item.unit_price = unit_price
        item.internal_unit_cost = internal_unit_cost
        item.line_total = item.compute_line_total()
        item.save()
        QuoteService.recalculate(quote=quote)
        return item

    @staticmethod
    @transaction.atomic
    def delete_item(*, quote: Quote, item: QuoteItem, actor: User) -> None:
        if not quote.is_editable:
            raise QuoteError("No se pueden eliminar ítems de un presupuesto no editable.")
        item.delete()
        QuoteService.recalculate(quote=quote)

    @staticmethod
    def recalculate(*, quote: Quote) -> Quote:
        """Recalcula subtotal, impuesto y total usando Decimal."""
        items = list(quote.items.all())
        subtotal = sum((i.quantity * i.unit_price for i in items), Decimal("0.00"))
        tax_amount = (subtotal * quote.tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = (subtotal - quote.discount_amount + tax_amount).quantize(Decimal("0.01"))

        Quote.objects.filter(pk=quote.pk).update(
            subtotal=subtotal.quantize(Decimal("0.01")),
            tax_amount=tax_amount,
            total=max(Decimal("0.00"), total),
        )
        quote.refresh_from_db()
        return quote

    @staticmethod
    @transaction.atomic
    def send(
        *,
        quote: Quote,
        actor: User,
        channel: str,
    ) -> Quote:
        if quote.status != Quote.Status.DRAFT:
            raise QuoteError("Solo se puede enviar un presupuesto en borrador.")
        quote.status = Quote.Status.SENT
        quote.sent_at = timezone.now()
        quote.sent_channel = channel
        quote.sent_by = actor
        quote.save()
        AuditLog.log(
            "update", user=actor, obj=quote,
            changes={"status": {"from": Quote.Status.DRAFT, "to": Quote.Status.SENT}},
        )
        return quote

    @staticmethod
    @transaction.atomic
    def approve(
        *,
        quote: Quote,
        actor: User,
        answered_by_name: str,
        answer_channel: str,
        answer_comment: str = "",
    ) -> Quote:
        if quote.status not in (Quote.Status.DRAFT, Quote.Status.SENT):
            raise QuoteError("Solo se puede aprobar un presupuesto en borrador o enviado.")

        # Solo puede haber una versión aprobada por orden
        other_approved = quote.work_order.quotes.filter(
            status=Quote.Status.APPROVED
        ).exclude(pk=quote.pk)
        if other_approved.exists():
            raise QuoteError("Ya existe una versión aprobada para esta orden.")

        quote.status = Quote.Status.APPROVED
        quote.answered_at = timezone.now()
        quote.answer_channel = answer_channel
        quote.answered_by_name = answered_by_name
        quote.answer_comment = answer_comment
        quote.save()

        # Avanzar la orden si corresponde
        order = quote.work_order
        if order.status == WorkOrder.Status.AWAITING_APPROVAL:
            from apps.workorders.services import WorkOrderService, WorkOrderStatusHistory
            WorkOrderService.transition(
                order=order,
                actor=actor,
                to_status=WorkOrder.Status.APPROVED_FOR_REPAIR,
                comment=f"Presupuesto v{quote.version} aprobado por {answered_by_name}.",
                source=WorkOrderStatusHistory.Source.WEB,
            )

        AuditLog.log(
            "update", user=actor, obj=quote,
            changes={"status": {"from": "SENT", "to": Quote.Status.APPROVED}},
        )
        return quote

    @staticmethod
    @transaction.atomic
    def reject(
        *,
        quote: Quote,
        actor: User,
        answered_by_name: str,
        answer_channel: str,
        answer_comment: str = "",
    ) -> Quote:
        if quote.status not in (Quote.Status.DRAFT, Quote.Status.SENT):
            raise QuoteError("Solo se puede rechazar un presupuesto en borrador o enviado.")

        quote.status = Quote.Status.REJECTED
        quote.answered_at = timezone.now()
        quote.answer_channel = answer_channel
        quote.answered_by_name = answered_by_name
        quote.answer_comment = answer_comment
        quote.save()

        order = quote.work_order
        if order.status == WorkOrder.Status.AWAITING_APPROVAL:
            from apps.workorders.services import WorkOrderService, WorkOrderStatusHistory
            WorkOrderService.transition(
                order=order,
                actor=actor,
                to_status=WorkOrder.Status.REJECTED,
                comment=f"Presupuesto v{quote.version} rechazado.",
                source=WorkOrderStatusHistory.Source.WEB,
            )

        AuditLog.log(
            "update", user=actor, obj=quote,
            changes={"status": {"from": "SENT", "to": Quote.Status.REJECTED}},
        )
        return quote
