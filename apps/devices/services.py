"""Servicios de dominio para equipos."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.customers.models import Customer

from .models import Device


class DeviceService:
    """Operaciones de negocio sobre equipos."""

    @staticmethod
    @transaction.atomic
    def create_device(
        *,
        actor: User,
        customer: Customer,
        device_category=None,
        brand: str = "",
        model: str = "",
        serial_number: str = "",
        alias: str = "",
        operating_system: str = "",
        cpu: str = "",
        ram_description: str = "",
        storage_description: str = "",
        gpu_description: str = "",
        permanent_notes: str = "",
    ) -> Device:
        device = Device(
            customer=customer,
            device_category=device_category,
            brand=brand,
            model=model,
            serial_number=serial_number,
            alias=alias,
            operating_system=operating_system,
            cpu=cpu,
            ram_description=ram_description,
            storage_description=storage_description,
            gpu_description=gpu_description,
            permanent_notes=permanent_notes,
            created_by=actor,
        )
        device.save()
        AuditLog.log("create", user=actor, obj=device)
        return device

    @staticmethod
    @transaction.atomic
    def update_device(*, device: Device, actor: User, **fields) -> Device:
        old_repr = str(device)
        changed: dict = {}
        for field, value in fields.items():
            if hasattr(device, field) and getattr(device, field) != value:
                changed[field] = {"from": getattr(device, field), "to": value}
                setattr(device, field, value)
        device.save()
        if changed:
            AuditLog.log("update", user=actor, obj=device, object_repr=old_repr, changes=changed)
        return device

    @staticmethod
    @transaction.atomic
    def deactivate_device(*, device: Device, actor: User) -> Device:
        device.is_active = False
        device.deactivated_at = timezone.now()
        device.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        AuditLog.log("update", user=actor, obj=device, changes={"is_active": {"from": True, "to": False}})
        return device
