"""Modelos de equipos de clientes."""
import uuid

from django.contrib.auth.models import User
from django.db import models

from apps.customers.models import Customer


class Device(models.Model):
    """Equipo o dispositivo de un cliente."""

    class DeviceType(models.TextChoices):
        DESKTOP = "DESKTOP", "PC de escritorio"
        NOTEBOOK = "NOTEBOOK", "Notebook / Laptop"
        ALL_IN_ONE = "ALL_IN_ONE", "All-in-One"
        SERVER = "SERVER", "Servidor"
        PRINTER = "PRINTER", "Impresora"
        MONITOR = "MONITOR", "Monitor"
        CONSOLE = "CONSOLE", "Consola"
        OTHER = "OTHER", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="devices",
        verbose_name="Cliente",
    )
    device_type = models.CharField(
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.DESKTOP,
        verbose_name="Tipo de equipo",
    )
    brand = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    model = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Número de serie")
    alias = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Alias",
        help_text="Nombre corto para identificar el equipo rápidamente.",
    )
    operating_system = models.CharField(
        max_length=100, blank=True, verbose_name="Sistema operativo"
    )
    cpu = models.CharField(max_length=150, blank=True, verbose_name="Procesador")
    ram_description = models.CharField(max_length=100, blank=True, verbose_name="Memoria RAM")
    storage_description = models.CharField(
        max_length=150, blank=True, verbose_name="Almacenamiento"
    )
    gpu_description = models.CharField(
        max_length=150, blank=True, verbose_name="Tarjeta de video"
    )
    permanent_notes = models.TextField(blank=True, verbose_name="Observaciones permanentes")
    primary_photo = models.ImageField(
        upload_to="devices/photos/",
        null=True,
        blank=True,
        verbose_name="Foto principal",
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activo")
    deactivated_at = models.DateTimeField(null=True, blank=True, verbose_name="Desactivado en")
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_devices",
        verbose_name="Creado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Registrado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["customer__full_name", "brand", "model"]

    def __str__(self):
        parts = [p for p in [self.brand, self.model] if p]
        label = " ".join(parts) if parts else self.get_device_type_display()
        if self.alias:
            label = f"{label} ({self.alias})"
        return label

    def possible_duplicates(self):
        """Duplicados del mismo cliente con el mismo número de serie."""
        if not self.serial_number:
            return Device.objects.none()
        return Device.objects.filter(
            customer=self.customer,
            serial_number=self.serial_number,
        ).exclude(pk=self.pk)
