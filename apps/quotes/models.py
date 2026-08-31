"""Modelos de presupuestos versionados."""
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from apps.workorders.models import WorkOrder


class Quote(models.Model):
    """Presupuesto versionado para una orden de trabajo.

    Solo el estado DRAFT permite editar ítems. Los estados finales
    (APPROVED, REJECTED, EXPIRED, REPLACED) son inmutables.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        SENT = "SENT", "Enviado"
        APPROVED = "APPROVED", "Aprobado"
        REJECTED = "REJECTED", "Rechazado"
        EXPIRED = "EXPIRED", "Vencido"
        REPLACED = "REPLACED", "Reemplazado"

    IMMUTABLE_STATUSES = {Status.APPROVED, Status.REJECTED, Status.EXPIRED, Status.REPLACED}

    class SentChannel(models.TextChoices):
        PHONE = "PHONE", "Teléfono"
        EMAIL = "EMAIL", "Email"
        TELEGRAM = "TELEGRAM", "Telegram"
        IN_PERSON = "IN_PERSON", "Presencial"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.PROTECT,
        related_name="quotes",
        verbose_name="Orden de trabajo",
    )
    version = models.PositiveIntegerField(verbose_name="Versión")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="Estado",
    )
    currency_code = models.CharField(max_length=3, default="ARS", verbose_name="Moneda")

    # Totales (calculados por QuoteService.recalculate)
    subtotal = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"), verbose_name="Subtotal"
    )
    discount_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"), verbose_name="Descuento"
    )
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), verbose_name="Tasa de IVA (%)"
    )
    tax_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"), verbose_name="IVA"
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"), verbose_name="Total"
    )

    valid_until = models.DateField(null=True, blank=True, verbose_name="Válido hasta")
    terms = models.TextField(blank=True, verbose_name="Condiciones")
    internal_notes = models.TextField(blank=True, verbose_name="Notas internas")

    # Envío
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado en")
    sent_channel = models.CharField(
        max_length=20, choices=SentChannel.choices, blank=True, verbose_name="Canal de envío"
    )
    sent_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_quotes",
        verbose_name="Enviado por",
    )

    # Respuesta del cliente
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name="Respondido en")
    answer_channel = models.CharField(
        max_length=20, choices=SentChannel.choices, blank=True, verbose_name="Canal de respuesta"
    )
    answered_by_name = models.CharField(
        max_length=160, blank=True, verbose_name="Respondido por (nombre)"
    )
    answer_comment = models.TextField(blank=True, verbose_name="Comentario de respuesta")

    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_quotes",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["work_order", "version"], name="unique_quote_version_per_order"
            )
        ]

    def __str__(self):
        return f"{self.work_order.number} v{self.version} — {self.get_status_display()}"

    @property
    def is_editable(self) -> bool:
        return self.status == self.Status.DRAFT

    @property
    def is_immutable(self) -> bool:
        return self.status in self.IMMUTABLE_STATUSES


class QuoteItem(models.Model):
    """Línea de ítem dentro de un presupuesto."""

    class ItemType(models.TextChoices):
        LABOR = "LABOR", "Mano de obra"
        PART = "PART", "Repuesto"
        SERVICE = "SERVICE", "Servicio"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Presupuesto",
    )
    position = models.PositiveIntegerField(verbose_name="Posición")
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.LABOR,
        verbose_name="Tipo",
    )
    description = models.CharField(max_length=500, verbose_name="Descripción")
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad",
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Precio unitario",
    )
    internal_unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Costo interno unitario",
    )
    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Total línea",
    )

    class Meta:
        verbose_name = "Ítem de presupuesto"
        verbose_name_plural = "Ítems de presupuesto"
        ordering = ["position"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0), name="quoteitem_quantity_positive"
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gte=0), name="quoteitem_price_non_negative"
            ),
        ]

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    def compute_line_total(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))
