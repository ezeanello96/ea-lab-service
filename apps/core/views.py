"""Vistas principales de la app core."""
import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Panel de control principal. Requiere autenticación."""

    template_name = "core/dashboard.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Panel de control"

        active_orders = 0
        ready_devices = 0
        urgent_orders = []
        orders_due_soon = []
        orders_no_tech = []
        latest_orders = []
        pending_balance = 0

        try:
            from apps.workorders.models import WorkOrder
            now = timezone.now()
            in_7_days = now + timedelta(days=7)

            active_orders = WorkOrder.objects.filter(
                status__in=WorkOrder.ACTIVE_STATUSES
            ).count()

            ready_devices = WorkOrder.objects.filter(
                status=WorkOrder.Status.READY_FOR_PICKUP
            ).count()

            urgent_orders = list(
                WorkOrder.objects.filter(
                    status__in=WorkOrder.ACTIVE_STATUSES,
                    priority__in=[WorkOrder.Priority.HIGH, WorkOrder.Priority.URGENT],
                )
                .select_related("customer", "device", "assigned_to")
                .order_by("-priority", "-received_at")[:10]
            )

            orders_due_soon = list(
                WorkOrder.objects.filter(
                    status__in=WorkOrder.ACTIVE_STATUSES,
                    promised_delivery_at__gte=now,
                    promised_delivery_at__lte=in_7_days,
                )
                .select_related("customer", "device", "assigned_to")
                .order_by("promised_delivery_at")[:10]
            )

            orders_no_tech = list(
                WorkOrder.objects.filter(
                    status__in=WorkOrder.ACTIVE_STATUSES,
                    assigned_to__isnull=True,
                )
                .select_related("customer", "device")
                .order_by("-received_at")[:10]
            )

            latest_orders = list(
                WorkOrder.objects.select_related("customer", "device", "assigned_to")
                .order_by("-received_at")[:10]
            )
        except Exception:
            logger.exception("Error cargando datos de OTs para el dashboard")

        try:
            from apps.tasks.services import TaskService
            overdue_tasks = TaskService.get_overdue_count()
        except Exception:
            overdue_tasks = 0

        try:
            from django.db.models import Sum
            from apps.quotes.models import Quote
            from apps.payments.models import Payment

            # Órdenes listas o entregadas con presupuesto aprobado
            approved_total = (
                Quote.objects.filter(
                    status=Quote.Status.APPROVED,
                    work_order__status__in=[
                        WorkOrder.Status.READY_FOR_PICKUP,
                        WorkOrder.Status.DELIVERED,
                        WorkOrder.Status.IN_REPAIR,
                        WorkOrder.Status.IN_TESTING,
                    ],
                )
                .aggregate(total=Sum("total"))["total"] or 0
            )
            paid_total = (
                Payment.objects.filter(
                    work_order__status__in=[
                        WorkOrder.Status.READY_FOR_PICKUP,
                        WorkOrder.Status.DELIVERED,
                        WorkOrder.Status.IN_REPAIR,
                        WorkOrder.Status.IN_TESTING,
                    ]
                )
                .aggregate(total=Sum("amount"))["total"] or 0
            )
            pending_balance = max(0, float(approved_total) - float(paid_total))
        except Exception:
            logger.exception("Error calculando saldo pendiente")

        context["stats"] = {
            "active_orders": active_orders,
            "overdue_tasks": overdue_tasks,
            "ready_devices": ready_devices,
            "pending_balance": pending_balance,
            "orders_due_soon_count": len(orders_due_soon),
            "orders_no_tech_count": len(orders_no_tech),
        }
        context["urgent_orders"] = urgent_orders
        context["orders_due_soon"] = orders_due_soon
        context["orders_no_tech"] = orders_no_tech
        context["latest_orders"] = latest_orders
        return context


class HealthCheckView(View):
    """
    Endpoint de verificación de salud del sistema.
    Retorna JSON con el estado de la base de datos y Redis.
    """

    def get(self, request):
        status = {"status": "ok", "db": "ok", "redis": "ok"}
        http_status = 200

        # Verificar base de datos
        try:
            from django.db import connection

            connection.ensure_connection()
        except Exception as exc:
            logger.error("Health check: fallo en BD: %s", exc)
            status["status"] = "error"
            status["db"] = "error"
            http_status = 503

        # Verificar Redis
        try:
            from django.conf import settings

            import redis

            r = redis.from_url(settings.REDIS_URL)
            r.ping()
        except Exception as exc:
            logger.error("Health check: fallo en Redis: %s", exc)
            status["status"] = "error"
            status["redis"] = "error"
            http_status = 503

        return JsonResponse(status, status=http_status)
