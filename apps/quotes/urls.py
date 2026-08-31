"""URLs para la app de presupuestos."""
from django.urls import path

from . import views

urlpatterns = [
    path("ordenes/<uuid:order_pk>/presupuestos/", views.QuoteListView.as_view(), name="quote-list"),
    path("ordenes/<uuid:order_pk>/presupuestos/nuevo/", views.QuoteCreateView.as_view(), name="quote-create"),
    path("ordenes/<uuid:order_pk>/presupuestos/<uuid:pk>/", views.QuoteDetailView.as_view(), name="quote-detail"),
    path("ordenes/<uuid:order_pk>/presupuestos/<uuid:pk>/enviar/", views.QuoteSendView.as_view(), name="quote-send"),
    path("ordenes/<uuid:order_pk>/presupuestos/<uuid:pk>/aprobar/", views.QuoteApproveView.as_view(), name="quote-approve"),
    path("ordenes/<uuid:order_pk>/presupuestos/<uuid:pk>/rechazar/", views.QuoteRejectView.as_view(), name="quote-reject"),
    path("ordenes/<uuid:order_pk>/presupuestos/<uuid:pk>/pdf/", views.QuotePDFView.as_view(), name="quote-pdf"),
]
