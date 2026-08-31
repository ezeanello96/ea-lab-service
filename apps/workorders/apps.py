"""Configuración de la app de órdenes de trabajo."""
from django.apps import AppConfig


class WorkordersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workorders"
    verbose_name = "Órdenes de trabajo"
