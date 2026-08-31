"""URLs del módulo de reportes."""
from django.urls import path

from .views import ReportFinancialView, ReportOrdersCSVView, ReportOrdersView, ReportTimesView

urlpatterns = [
    path("reportes/ordenes/", ReportOrdersView.as_view(), name="report-orders"),
    path("reportes/ordenes/csv/", ReportOrdersCSVView.as_view(), name="report-orders-csv"),
    path("reportes/tiempos/", ReportTimesView.as_view(), name="report-times"),
    path("reportes/financiero/", ReportFinancialView.as_view(), name="report-financial"),
]
