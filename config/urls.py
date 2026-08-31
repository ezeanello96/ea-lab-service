"""URLs principales de PC Service Manager."""
from django.contrib import admin
from django.urls import include, path

from apps.core.views import DashboardView, HealthCheckView
from apps.workorders.views import GlobalSearchView

urlpatterns = [
    # Panel de administración
    path("admin/", admin.site.urls),
    # Inicio / Dashboard
    path("", DashboardView.as_view(), name="dashboard"),
    # Autenticación
    path("", include("apps.accounts.urls")),
    # Clientes
    path("", include("apps.customers.urls")),
    # Equipos
    path("", include("apps.devices.urls")),
    # Órdenes de trabajo
    path("", include("apps.workorders.urls")),
    # Presupuestos
    path("", include("apps.quotes.urls")),
    # Tareas
    path("", include("apps.tasks.urls")),
    # Reportes
    path("", include("apps.reports.urls")),
    # Búsqueda global
    path("buscar/", GlobalSearchView.as_view(), name="global-search"),
    # Endpoint de salud del sistema
    path("health/", HealthCheckView.as_view(), name="health"),
    # API REST v1
    path("api/v1/", include("apps.core.api_urls")),
]
