"""Admin de auditoría."""
from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor", "action", "object_repr", "ip_address")
    list_filter = ("action",)
    search_fields = ("actor__username", "object_repr", "ip_address")
    readonly_fields = (
        "actor",
        "action",
        "content_type",
        "object_id",
        "object_repr",
        "changes",
        "ip_address",
        "user_agent",
        "timestamp",
    )
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
