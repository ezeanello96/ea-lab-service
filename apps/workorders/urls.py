"""URLs para la app de órdenes de trabajo."""
from django.urls import path

from . import views
from .diagnosis_views import DiagnosisView
from .repair_views import (
    FinalTestCreateView,
    FinalTestUpdateView,
    MarkReadyForPickupView,
    RepairView,
    WorkLogCreateView,
)

urlpatterns = [
    path("ordenes/", views.WorkOrderListView.as_view(), name="workorder-list"),
    path("ordenes/<uuid:pk>/recibo/", views.WorkOrderReceiptPDFView.as_view(), name="workorder-receipt"),
    # Google Calendar
    path("ordenes/google-oauth/", views.GoogleOAuthInitView.as_view(), name="google-oauth-init"),
    path("ordenes/google-oauth/callback/", views.GoogleOAuthCallbackView.as_view(), name="google-oauth-callback"),
    path("ordenes/<uuid:pk>/calendar/crear/", views.WorkOrderCalendarCreateView.as_view(), name="workorder-calendar-create"),
    path("ordenes/<uuid:pk>/calendar/actualizar/", views.WorkOrderCalendarUpdateView.as_view(), name="workorder-calendar-update"),
    path("ordenes/<uuid:pk>/calendar/eliminar/", views.WorkOrderCalendarDeleteView.as_view(), name="workorder-calendar-delete"),
    path("ordenes/kanban/", views.WorkOrderKanbanView.as_view(), name="workorder-kanban"),
    path("ordenes/nueva/", views.WorkOrderCreateView.as_view(), name="workorder-create"),
    path("ordenes/<uuid:pk>/", views.WorkOrderDetailView.as_view(), name="workorder-detail"),
    path("ordenes/<uuid:pk>/transicion/", views.WorkOrderTransitionView.as_view(), name="workorder-transition"),
    # Diagnóstico
    path("ordenes/<uuid:pk>/diagnostico/", DiagnosisView.as_view(), name="diagnosis-view"),
    # Reparación
    path("ordenes/<uuid:pk>/reparacion/", RepairView.as_view(), name="repair-view"),
    path("ordenes/<uuid:pk>/reparacion/log/", WorkLogCreateView.as_view(), name="worklog-create"),
    path("ordenes/<uuid:pk>/reparacion/prueba/", FinalTestCreateView.as_view(), name="finaltest-create"),
    path("ordenes/<uuid:pk>/reparacion/prueba/<uuid:test_pk>/", FinalTestUpdateView.as_view(), name="finaltest-update"),
    path("ordenes/<uuid:pk>/reparacion/listo/", MarkReadyForPickupView.as_view(), name="mark-ready"),
]
