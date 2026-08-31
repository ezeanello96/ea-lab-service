"""Modelos de órdenes de trabajo, historial de estados y secuencia."""
import uuid

from django.contrib.auth.models import User
from django.db import models

from apps.customers.models import Customer
from apps.devices.models import Device


class OrderSequence(models.Model):
    """Secuencia anual para generar números de orden sin duplicados.

    Debe actualizarse con SELECT FOR UPDATE dentro de una transacción.
    """

    year = models.PositiveIntegerField(primary_key=True, verbose_name="Año")
    last_value = models.PositiveIntegerField(default=0, verbose_name="Último valor")

    class Meta:
        verbose_name = "Secuencia de órdenes"
        verbose_name_plural = "Secuencias de órdenes"

    def __str__(self):
        return f"Secuencia {self.year}: {self.last_value}"


class WorkOrder(models.Model):
    """Orden de trabajo para el servicio técnico."""

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recibido"
        PENDING_DIAGNOSIS = "PENDING_DIAGNOSIS", "Pendiente de diagnóstico"
        IN_DIAGNOSIS = "IN_DIAGNOSIS", "En diagnóstico"
        AWAITING_APPROVAL = "AWAITING_APPROVAL", "Esperando aprobación"
        APPROVED_FOR_REPAIR = "APPROVED_FOR_REPAIR", "Aprobado para reparar"
        REJECTED = "REJECTED", "Presupuesto rechazado"
        WAITING_PART = "WAITING_PART", "Esperando repuesto"
        IN_REPAIR = "IN_REPAIR", "En reparación"
        IN_TESTING = "IN_TESTING", "En pruebas"
        READY_FOR_PICKUP = "READY_FOR_PICKUP", "Listo para retirar"
        DELIVERED = "DELIVERED", "Entregado"
        UNREPAIRABLE = "UNREPAIRABLE", "Sin reparación posible"
        CANCELLED = "CANCELLED", "Cancelado"

    # Transiciones permitidas por estado
    ALLOWED_TRANSITIONS: dict[str, list[str]] = {
        Status.RECEIVED: [Status.PENDING_DIAGNOSIS, Status.IN_DIAGNOSIS, Status.CANCELLED],
        Status.PENDING_DIAGNOSIS: [Status.IN_DIAGNOSIS, Status.CANCELLED],
        Status.IN_DIAGNOSIS: [Status.AWAITING_APPROVAL, Status.UNREPAIRABLE, Status.CANCELLED],
        Status.AWAITING_APPROVAL: [Status.APPROVED_FOR_REPAIR, Status.REJECTED, Status.CANCELLED],
        Status.APPROVED_FOR_REPAIR: [Status.WAITING_PART, Status.IN_REPAIR, Status.CANCELLED],
        Status.WAITING_PART: [Status.IN_REPAIR, Status.CANCELLED],
        Status.IN_REPAIR: [Status.WAITING_PART, Status.IN_TESTING, Status.CANCELLED],
        Status.IN_TESTING: [Status.IN_REPAIR, Status.READY_FOR_PICKUP],
        Status.READY_FOR_PICKUP: [Status.DELIVERED, Status.IN_REPAIR],
        Status.REJECTED: [Status.READY_FOR_PICKUP, Status.CANCELLED],
        Status.UNREPAIRABLE: [Status.READY_FOR_PICKUP, Status.DELIVERED],
        Status.DELIVERED: [],
        Status.CANCELLED: [],
    }

    ACTIVE_STATUSES = [
        Status.RECEIVED,
        Status.PENDING_DIAGNOSIS,
        Status.IN_DIAGNOSIS,
        Status.AWAITING_APPROVAL,
        Status.APPROVED_FOR_REPAIR,
        Status.WAITING_PART,
        Status.IN_REPAIR,
        Status.IN_TESTING,
        Status.READY_FOR_PICKUP,
    ]

    class Priority(models.TextChoices):
        LOW = "LOW", "Baja"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "Alta"
        URGENT = "URGENT", "Urgente"

    class Source(models.TextChoices):
        WALK_IN = "WALK_IN", "Presencial"
        PHONE = "PHONE", "Teléfono"
        TELEGRAM = "TELEGRAM", "Telegram"
        REFERRAL = "REFERRAL", "Referido"
        WEB = "WEB", "Web"
        OTHER = "OTHER", "Otro"

    class RelationType(models.TextChoices):
        WARRANTY = "WARRANTY", "Garantía"
        REPEAT_ISSUE = "REPEAT_ISSUE", "Reincidencia"
        FOLLOW_UP = "FOLLOW_UP", "Seguimiento"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="Número de orden",
        help_text="Formato OT-AAAA-NNNNN. Se genera automáticamente.",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="Cliente",
    )
    device = models.ForeignKey(
        Device,
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="Equipo",
    )
    related_order = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="related_orders",
        verbose_name="Orden relacionada",
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RelationType.choices,
        blank=True,
        verbose_name="Tipo de relación",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.RECEIVED,
        db_index=True,
        verbose_name="Estado",
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
        db_index=True,
        verbose_name="Prioridad",
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WALK_IN,
        verbose_name="Origen",
    )
    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
        verbose_name="Asignado a",
        db_index=True,
    )
    reported_issue = models.TextField(verbose_name="Problema informado")
    intake_condition = models.TextField(blank=True, verbose_name="Condición de ingreso")
    received_accessories = models.TextField(blank=True, verbose_name="Accesorios recibidos")
    internal_notes = models.TextField(blank=True, verbose_name="Notas internas")
    customer_visible_notes = models.TextField(
        blank=True, verbose_name="Notas visibles al cliente"
    )
    received_at = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name="Fecha de ingreso"
    )
    diagnosis_due_at = models.DateTimeField(
        null=True, blank=True, db_index=True, verbose_name="Límite de diagnóstico"
    )
    promised_delivery_at = models.DateTimeField(
        null=True, blank=True, db_index=True, verbose_name="Entrega prometida"
    )
    ready_at = models.DateTimeField(null=True, blank=True, verbose_name="Listo en")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Entregado en")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelado en")
    cancel_reason = models.TextField(blank=True, verbose_name="Motivo de cancelación")
    google_calendar_event_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID de evento en Google Calendar",
        help_text="Se rellena automáticamente al crear el evento desde el sistema.",
    )
    google_calendar_event_link = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="URL del evento en Google Calendar",
        help_text="Enlace directo al evento. Se rellena automáticamente.",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_orders",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de trabajo"
        verbose_name_plural = "Órdenes de trabajo"
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["status", "promised_delivery_at"]),
            models.Index(fields=["customer", "created_at"]),
        ]

    def __str__(self):
        return f"{self.number} — {self.customer}"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])


class WorkOrderStatusHistory(models.Model):
    """Registro inmutable de cada cambio de estado de una orden."""

    class Source(models.TextChoices):
        WEB = "WEB", "Web"
        API = "API", "API"
        TELEGRAM = "TELEGRAM", "Telegram"
        SYSTEM = "SYSTEM", "Sistema"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Orden de trabajo",
    )
    from_status = models.CharField(
        max_length=30,
        blank=True,
        choices=WorkOrder.Status.choices,
        verbose_name="Estado anterior",
    )
    to_status = models.CharField(
        max_length=30,
        choices=WorkOrder.Status.choices,
        verbose_name="Estado nuevo",
    )
    comment = models.TextField(blank=True, verbose_name="Comentario")
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Actor",
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.WEB,
        verbose_name="Origen",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historial de estados"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.work_order.number}: {self.from_status} → {self.to_status}"


class Diagnosis(models.Model):
    """Diagnóstico técnico de una orden. Relación uno a uno con la orden."""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        FINAL = "FINAL", "Finalizado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.OneToOneField(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="diagnosis",
        verbose_name="Orden de trabajo",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Estado",
    )
    reported_problem_summary = models.TextField(
        blank=True, verbose_name="Resumen del problema reportado"
    )
    findings = models.TextField(blank=True, verbose_name="Hallazgos")
    tests_performed = models.TextField(blank=True, verbose_name="Pruebas realizadas")
    recommended_solution = models.TextField(blank=True, verbose_name="Solución recomendada")
    risk_notes = models.TextField(blank=True, verbose_name="Notas de riesgo")
    repairable = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="¿Tiene reparación?",
        help_text="Nulo mientras es borrador.",
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Horas estimadas",
    )
    technician = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="diagnoses",
        verbose_name="Técnico",
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Inicio")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Finalizado en")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Diagnóstico"
        verbose_name_plural = "Diagnósticos"

    def __str__(self):
        return f"Diagnóstico {self.work_order.number} ({self.get_status_display()})"

    @property
    def is_final(self) -> bool:
        return self.status == self.Status.FINAL


class WorkLog(models.Model):
    """Entrada cronológica de trabajo técnico sobre una orden.

    Las entradas no se eliminan. Una corrección se documenta con otra entrada.
    """

    class EntryType(models.TextChoices):
        NOTE = "NOTE", "Nota"
        REPAIR = "REPAIR", "Reparación"
        TEST = "TEST", "Prueba"
        PART = "PART", "Repuesto"
        CUSTOMER_CONTACT = "CUSTOMER_CONTACT", "Contacto con cliente"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="work_logs",
        verbose_name="Orden de trabajo",
    )
    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="work_logs",
        verbose_name="Autor",
    )
    entry_type = models.CharField(
        max_length=20,
        choices=EntryType.choices,
        default=EntryType.NOTE,
        verbose_name="Tipo de entrada",
    )
    description = models.TextField(verbose_name="Descripción")
    minutes_spent = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Minutos invertidos",
    )
    is_customer_visible = models.BooleanField(
        default=False,
        verbose_name="Visible al cliente",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entrada de trabajo"
        verbose_name_plural = "Entradas de trabajo"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.work_order.number} — {self.get_entry_type_display()} ({self.created_at:%d/%m/%Y})"


class FinalTest(models.Model):
    """Prueba final antes de marcar una orden como lista para retirar."""

    class TestStatus(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        PASSED = "PASSED", "Aprobado"
        FAILED = "FAILED", "Fallido"
        NOT_APPLICABLE = "NOT_APPLICABLE", "No aplica"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="final_tests",
        verbose_name="Orden de trabajo",
    )
    name = models.CharField(max_length=200, verbose_name="Prueba")
    status = models.CharField(
        max_length=20,
        choices=TestStatus.choices,
        default=TestStatus.PENDING,
        verbose_name="Resultado",
    )
    notes = models.TextField(blank=True, verbose_name="Notas")
    tested_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="final_tests",
        verbose_name="Probado por",
    )
    tested_at = models.DateTimeField(null=True, blank=True, verbose_name="Probado en")

    class Meta:
        verbose_name = "Prueba final"
        verbose_name_plural = "Pruebas finales"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} — {self.get_status_display()}"
