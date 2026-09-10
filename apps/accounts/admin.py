"""Configuración del admin para la app de cuentas."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import TelegramAccount, TelegramPairingCode, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Perfil"
    fields = (
        "display_name",
        "phone",
        "can_view_costs",
        "can_deliver_with_balance",
        "telegram_notifications_enabled",
    )


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_user_id", "username", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "username", "telegram_user_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TelegramPairingCode)
class TelegramPairingCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code_hash", "expires_at", "used_at", "created_at")
    list_filter = ("expires_at",)
    search_fields = ("user__username", "code_hash")
    readonly_fields = ("created_at",)
