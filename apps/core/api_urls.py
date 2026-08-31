"""URLs de la API REST v1 (esqueleto inicial)."""
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# Los viewsets se registrarán aquí en fases posteriores:
# router.register(r"customers", CustomerViewSet, basename="customer")
# router.register(r"work-orders", WorkOrderViewSet, basename="workorder")

urlpatterns = router.urls + [
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]
