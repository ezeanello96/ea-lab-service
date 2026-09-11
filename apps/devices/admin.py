from django.contrib import admin
from .models import Device, DeviceCategory


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_editable = ("is_active",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "device_category", "customer", "created_at")
    list_filter = ("device_category", "is_active")
    search_fields = ("brand", "model", "serial_number", "alias", "customer__full_name")
