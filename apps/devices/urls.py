"""URLs para la app de equipos."""
from django.urls import path

from . import views

urlpatterns = [
    path("equipos/", views.DeviceListView.as_view(), name="device-list"),
    path("equipos/<uuid:pk>/", views.DeviceDetailView.as_view(), name="device-detail"),
    path("equipos/<uuid:pk>/editar/", views.DeviceUpdateView.as_view(), name="device-update"),
]
