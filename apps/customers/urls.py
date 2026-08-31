"""URLs para la app de clientes y alta de equipos desde ficha de cliente."""
from django.urls import path

from apps.devices.views import DeviceCreateView

from . import views

urlpatterns = [
    path("clientes/", views.CustomerListView.as_view(), name="customer-list"),
    path("clientes/nuevo/", views.CustomerCreateView.as_view(), name="customer-create"),
    path("clientes/<uuid:pk>/", views.CustomerDetailView.as_view(), name="customer-detail"),
    path("clientes/<uuid:pk>/editar/", views.CustomerUpdateView.as_view(), name="customer-update"),
    path("clientes/<uuid:pk>/desactivar/", views.CustomerDeactivateView.as_view(), name="customer-deactivate"),
    path("clientes/<uuid:pk>/equipos/nuevo/", DeviceCreateView.as_view(), name="device-create"),
]
