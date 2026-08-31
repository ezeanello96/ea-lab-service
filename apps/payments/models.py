"""Modelos de pagos y cobros."""
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.workorders.models import WorkOrder


class Payment(models.Model):
    """Registro de un cobro asociado a una orden de trabajo."""

    METHOD_CASH = "cash"
    METHOD_TRANSFER = "transfer"
    METHOD_CARD_DEBIT = "card_debit"
    METHOD_CARD_CREDIT = "card_credit"
    METHOD_MERCADO_PAGO = "mercado_pago"
    METHOD_OTHER = "other"

    METHOD_CHOICES = [
        (METHOD_CASH, "Efectivo"),
        (METHOD_TRANSFER, "Transferencia bancaria"),
        (METHOD_CARD_DEBIT, "Tarjeta de débito"),
        (METHOD_CARD_CREDIT, "Tarjeta de crédito"),
        (METHOD_MERCADO_PAGO, "Mercado Pago"),
        (METHOD_OTHER, "Otro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Orden de trabajo",
    )
    registered_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="registered_payments",
        verbose_name="Registrado por",
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name="Monto (ARS)"
    )
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default=METHOD_CASH,
        verbose_name="Método de pago",
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Referencia",
        help_text="Número de transferencia, comprobante, etc.",
    )
    notes = models.TextField(blank=True, verbose_name="Notas")
    paid_at = models.DateTimeField(
        default=timezone.now, verbose_name="Fecha de pago"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registrado en")

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"${self.amount:,.2f} ({self.get_method_display()}) — {self.work_order.number}"
