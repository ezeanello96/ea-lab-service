"""Servicios de dominio para clientes."""
from __future__ import annotations

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AuditLog

from .models import Customer, CustomerTag


class CustomerService:
    """Operaciones de negocio sobre clientes."""

    @staticmethod
    @transaction.atomic
    def create_customer(
        *,
        actor: User,
        full_name: str,
        phone: str,
        email: str = "",
        business_name: str = "",
        document_type: str = "",
        document_number: str = "",
        address: str = "",
        preferred_channel: str = Customer.PreferredChannel.PHONE,
        notes: str = "",
        marketing_consent: bool = False,
        marketing_consent_source: str = "",
        tag_ids: list[str] | None = None,
    ) -> Customer:
        customer = Customer(
            full_name=full_name,
            phone=phone,
            email=email,
            business_name=business_name,
            document_type=document_type,
            document_number=document_number,
            address=address,
            preferred_channel=preferred_channel,
            notes=notes,
            marketing_consent=marketing_consent,
            marketing_consent_source=marketing_consent_source,
            created_by=actor,
        )
        if marketing_consent:
            customer.marketing_consent_at = timezone.now()
        customer.save()

        if tag_ids:
            tags = CustomerTag.objects.filter(id__in=tag_ids, is_active=True)
            customer.tags.set(tags)

        AuditLog.log("create", user=actor, obj=customer)
        return customer

    @staticmethod
    @transaction.atomic
    def update_customer(
        *,
        customer: Customer,
        actor: User,
        **fields,
    ) -> Customer:
        old_repr = str(customer)
        changed: dict = {}

        marketing_consent_was = customer.marketing_consent
        for field, value in fields.items():
            if hasattr(customer, field) and getattr(customer, field) != value:
                changed[field] = {"from": getattr(customer, field), "to": value}
                setattr(customer, field, value)

        if "marketing_consent" in fields:
            if fields["marketing_consent"] and not marketing_consent_was:
                customer.marketing_consent_at = timezone.now()
            elif not fields["marketing_consent"] and marketing_consent_was:
                customer.marketing_opt_out_at = timezone.now()

        customer.save()

        if changed:
            AuditLog.log("update", user=actor, obj=customer, object_repr=old_repr, changes=changed)
        return customer

    @staticmethod
    @transaction.atomic
    def deactivate_customer(*, customer: Customer, actor: User) -> Customer:
        if not customer.is_active:
            return customer
        customer.is_active = False
        customer.deactivated_at = timezone.now()
        customer.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        AuditLog.log(
            "update",
            user=actor,
            obj=customer,
            object_repr=str(customer),
            changes={"is_active": {"from": True, "to": False}},
        )
        return customer

    @staticmethod
    @transaction.atomic
    def reactivate_customer(*, customer: Customer, actor: User) -> Customer:
        customer.is_active = True
        customer.deactivated_at = None
        customer.save(update_fields=["is_active", "deactivated_at", "updated_at"])
        AuditLog.log(
            "update",
            user=actor,
            obj=customer,
            changes={"is_active": {"from": False, "to": True}},
        )
        return customer
