"""Configuración de la app de cuentas."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Cuentas de usuario"

    def ready(self):
        """Importar señales al inicializar la app."""
        import apps.accounts.signals  # noqa: F401
