"""Modelos de clientes y etiquetas."""
import uuid

from django.contrib.auth.models import User
from django.db import models


class CustomerTag(models.Model):
    """Etiqueta reutilizable para clasificar clientes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Etiqueta de cliente"
        verbose_name_plural = "Etiquetas de clientes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Cliente del servicio técnico."""

    class DocumentType(models.TextChoices):
        DNI = "DNI", "DNI"
        CUIT = "CUIT", "CUIT"
        OTHER = "OTHER", "Otro"
        NONE = "", "Sin documento"

    class PreferredChannel(models.TextChoices):
        PHONE = "PHONE", "Teléfono"
        EMAIL = "EMAIL", "Email"
        TELEGRAM = "TELEGRAM", "Telegram"
        IN_PERSON = "IN_PERSON", "Presencial"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=160, verbose_name="Nombre completo")
    business_name = models.CharField(max_length=200, blank=True, verbose_name="Razón social")
    document_type = models.CharField(
        max_length=10,
        choices=DocumentType.choices,
        blank=True,
        default="",
        verbose_name="Tipo de documento",
    )
    document_number = models.CharField(
        max_length=30, blank=True, verbose_name="Número de documento"
    )
    phone = models.CharField(max_length=30, verbose_name="Teléfono")
    phone_normalized = models.CharField(
        max_length=30,
        blank=True,
        db_index=True,
        verbose_name="Teléfono normalizado",
        help_text="Solo dígitos, para búsqueda rápida.",
    )
    email = models.EmailField(blank=True, db_index=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Dirección")
    preferred_channel = models.CharField(
        max_length=20,
        choices=PreferredChannel.choices,
        default=PreferredChannel.PHONE,
        verbose_name="Canal preferido",
    )
    notes = models.TextField(blank=True, verbose_name="Notas internas")
    marketing_consent = models.BooleanField(
        default=False, verbose_name="Consentimiento comercial"
    )
    marketing_consent_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de consentimiento"
    )
    marketing_consent_source = models.CharField(
        max_length=100, blank=True, verbose_name="Origen del consentimiento"
    )
    marketing_opt_out_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de baja comercial"
    )
    tags = models.ManyToManyField(
        CustomerTag, blank=True, related_name="customers", verbose_name="Etiquetas"
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activo")
    deactivated_at = models.DateTimeField(null=True, blank=True, verbose_name="Desactivado en")
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_customers",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["full_name"], name="customer_name_idx"),
            models.Index(fields=["document_type", "document_number"], name="customer_doc_idx"),
        ]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        self.phone_normalized = "".join(c for c in self.phone if c.isdigit())
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.business_name or self.full_name

    def possible_duplicates(self):
        """Retorna queryset de posibles duplicados por teléfono, email o documento."""
        from django.db.models import Q
        q = Q()
        if self.phone_normalized:
            q |= Q(phone_normalized=self.phone_normalized)
        if self.email:
            q |= Q(email__iexact=self.email)
        if self.document_number:
            q |= Q(document_number=self.document_number, document_type=self.document_type)
        if not q:
            return Customer.objects.none()
        return Customer.objects.filter(q).exclude(pk=self.pk)
