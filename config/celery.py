"""Configuración de Celery para PC Service Manager."""
import os

from celery import Celery

# Módulo de settings por defecto para el programa celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("pcservice")

# Leer configuración desde el objeto settings de Django.
# El namespace 'CELERY' significa que todas las claves de configuración de Celery
# deben tener el prefijo `CELERY_`.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Descubrir automáticamente tareas en todos los módulos tasks.py de las apps instaladas
app.autodiscover_tasks(
    [
        "apps.accounts",
        "apps.core",
        "apps.customers",
        "apps.devices",
        "apps.workorders",
        "apps.quotes",
        "apps.tasks",
        "apps.payments",
        "apps.notifications",
        "apps.telegram_bot",
        "apps.audit",
        "apps.reports",
    ]
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de depuración para verificar que Celery funciona."""
    print(f"Solicitud: {self.request!r}")
