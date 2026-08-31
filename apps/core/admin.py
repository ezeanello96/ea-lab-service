"""Configuración del admin para la app core."""
from django.contrib import admin

from .models import BusinessSettings


@admin.register(BusinessSettings)
class BusinessSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Identificación",
            {
                "fields": (
                    "business_name",
                    "legal_name",
                    "phone",
                    "email",
                    "address",
                )
            },
        ),
        (
            "Configuración general",
            {
                "fields": (
                    "currency_code",
                    "timezone",
                    "order_prefix",
                    "default_warranty_days",
                    "default_diagnosis_hours",
                )
            },
        ),
        (
            "Notificaciones",
            {
                "fields": (
                    "quiet_hours_start",
                    "quiet_hours_end",
                    "morning_digest_time",
                    "evening_digest_time",
                )
            },
        ),
        (
            "Textos legales",
            {
                "fields": (
                    "warranty_terms",
                    "quote_terms",
                    "receipt_terms",
                )
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        """Solo permitir un registro."""
        return not BusinessSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar la configuración."""
        return False
