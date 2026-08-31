"""Vistas para el módulo de reportes."""
import csv
import json
import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView, View

logger = logging.getLogger(__name__)


def _parse_date(value, default):
    from django.utils.dateparse import parse_date
    if value:
        parsed = parse_date(value)
        if parsed:
            return parsed
    return default


class ReportOrdersView(LoginRequiredMixin, TemplateView):
    """Reporte de órdenes de trabajo: filtros, tabla, gráficos, exportación CSV."""

    template_name = "reports/report_orders.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.workorders.models import WorkOrder
        from django.contrib.auth.models import User

        now = timezone.now().date()
        default_from = now.replace(day=1)  # primer día del mes actual
        default_to = now

        date_from = _parse_date(self.request.GET.get("date_from"), default_from)
        date_to   = _parse_date(self.request.GET.get("date_to"),   default_to)
        status_filter    = self.request.GET.get("status", "")
        tech_filter      = self.request.GET.get("tech", "")

        qs = WorkOrder.objects.filter(
            received_at__date__gte=date_from,
            received_at__date__lte=date_to,
        ).select_related("customer", "device", "assigned_to")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if tech_filter:
            if tech_filter == "none":
                qs = qs.filter(assigned_to__isnull=True)
            else:
                qs = qs.filter(assigned_to_id=tech_filter)

        orders = list(qs.order_by("-received_at"))

        # Distribución por estado
        by_status = (
            WorkOrder.objects.filter(
                received_at__date__gte=date_from,
                received_at__date__lte=date_to,
            )
            .values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        status_labels = [WorkOrder.Status(r["status"]).label for r in by_status]
        status_counts = [r["count"] for r in by_status]

        # OTs por mes
        by_month = (
            WorkOrder.objects.filter(
                received_at__date__gte=date_from,
                received_at__date__lte=date_to,
            )
            .annotate(month=TruncMonth("received_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        month_labels = [r["month"].strftime("%b %Y") for r in by_month]
        month_counts = [r["count"] for r in by_month]

        # Técnicos para filtro
        technicians = User.objects.filter(
            assigned_orders__received_at__date__gte=date_from,
            assigned_orders__received_at__date__lte=date_to,
        ).distinct()

        context.update({
            "orders": orders,
            "date_from": date_from,
            "date_to": date_to,
            "status_filter": status_filter,
            "tech_filter": tech_filter,
            "technicians": technicians,
            "status_choices": WorkOrder.Status.choices,
            "total_orders": len(orders),
            # Serialized as JSON for Chart.js
            "status_labels_json": json.dumps(status_labels),
            "status_counts_json": json.dumps(status_counts),
            "month_labels_json": json.dumps(month_labels),
            "month_counts_json": json.dumps(month_counts),
            "has_chart_data": bool(status_labels),
            "has_month_data": bool(month_labels),
        })
        return context


class ReportOrdersCSVView(LoginRequiredMixin, View):
    """Exporta el reporte de OTs a CSV."""

    def get(self, request):
        from apps.workorders.models import WorkOrder

        now = timezone.now().date()
        date_from = _parse_date(request.GET.get("date_from"), now.replace(day=1))
        date_to   = _parse_date(request.GET.get("date_to"),   now)
        status_filter = request.GET.get("status", "")
        tech_filter   = request.GET.get("tech", "")

        qs = WorkOrder.objects.filter(
            received_at__date__gte=date_from,
            received_at__date__lte=date_to,
        ).select_related("customer", "device", "assigned_to")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if tech_filter:
            if tech_filter == "none":
                qs = qs.filter(assigned_to__isnull=True)
            else:
                qs = qs.filter(assigned_to_id=tech_filter)

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="reporte-ordenes-{date_from}-{date_to}.csv"'
        response.write("﻿")  # BOM para Excel

        writer = csv.writer(response)
        writer.writerow([
            "Número", "Estado", "Prioridad", "Cliente", "Equipo",
            "Técnico", "Fecha ingreso", "Entrega prometida", "Fecha entrega",
        ])

        for o in qs.order_by("-received_at"):
            writer.writerow([
                o.number,
                o.get_status_display(),
                o.get_priority_display(),
                o.customer.full_name,
                str(o.device),
                o.assigned_to.get_full_name() if o.assigned_to else "",
                o.received_at.strftime("%d/%m/%Y"),
                o.promised_delivery_at.strftime("%d/%m/%Y") if o.promised_delivery_at else "",
                o.delivered_at.strftime("%d/%m/%Y") if o.delivered_at else "",
            ])

        return response


class ReportTimesView(LoginRequiredMixin, TemplateView):
    """Reporte de tiempos de resolución."""

    template_name = "reports/report_times.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.workorders.models import WorkOrder
        from django.contrib.auth.models import User

        now = timezone.now().date()
        date_from = _parse_date(self.request.GET.get("date_from"), now - timedelta(days=90))
        date_to   = _parse_date(self.request.GET.get("date_to"),   now)

        delivered_qs = WorkOrder.objects.filter(
            status=WorkOrder.Status.DELIVERED,
            delivered_at__date__gte=date_from,
            delivered_at__date__lte=date_to,
            received_at__isnull=False,
        ).select_related("customer", "device", "assigned_to")

        orders_with_time = []
        total_hours = 0
        count = 0
        for o in delivered_qs:
            if o.delivered_at and o.received_at:
                delta = o.delivered_at - o.received_at
                hours = delta.total_seconds() / 3600
                orders_with_time.append({
                    "order": o,
                    "hours": round(hours, 1),
                    "days": round(delta.days + delta.seconds / 86400, 1),
                    "overdue": o.promised_delivery_at and o.delivered_at > o.promised_delivery_at,
                })
                total_hours += hours
                count += 1

        avg_hours = round(total_hours / count, 1) if count else 0
        avg_days = round(avg_hours / 24, 1) if avg_hours else 0

        orders_with_time.sort(key=lambda x: x["hours"], reverse=True)

        # Promedio por técnico
        by_tech = []
        technicians = User.objects.filter(
            assigned_orders__status=WorkOrder.Status.DELIVERED,
            assigned_orders__delivered_at__date__gte=date_from,
            assigned_orders__delivered_at__date__lte=date_to,
        ).distinct()

        for tech in technicians:
            tech_orders = [o for o in orders_with_time if o["order"].assigned_to_id == tech.pk]
            if tech_orders:
                tech_avg = round(sum(o["hours"] for o in tech_orders) / len(tech_orders), 1)
                by_tech.append({
                    "tech": tech,
                    "count": len(tech_orders),
                    "avg_hours": tech_avg,
                    "avg_days": round(tech_avg / 24, 1),
                })
        by_tech.sort(key=lambda x: x["avg_hours"])

        # OTs que superaron la entrega estimada
        overdue_qs = list(WorkOrder.objects.filter(
            status__in=WorkOrder.ACTIVE_STATUSES,
            promised_delivery_at__lt=timezone.now(),
        ).select_related("customer", "device", "assigned_to").order_by("promised_delivery_at"))

        context.update({
            "date_from": date_from,
            "date_to": date_to,
            "orders_with_time": orders_with_time,
            "avg_hours": avg_hours,
            "avg_days": avg_days,
            "count": count,
            "by_tech": by_tech,
            "overdue_active": overdue_qs,
        })
        return context


class ReportFinancialView(LoginRequiredMixin, TemplateView):
    """Reporte de presupuestos y facturación."""

    template_name = "reports/report_financial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.workorders.models import WorkOrder
        from apps.quotes.models import Quote
        from apps.payments.models import Payment

        now = timezone.now().date()
        date_from = _parse_date(self.request.GET.get("date_from"), now.replace(day=1))
        date_to   = _parse_date(self.request.GET.get("date_to"),   now)

        # Total presupuestado (quotes aprobadas en el período)
        total_quoted = (
            Quote.objects.filter(
                status=Quote.Status.APPROVED,
                answered_at__date__gte=date_from,
                answered_at__date__lte=date_to,
            ).aggregate(total=Sum("total"))["total"] or 0
        )

        # Total cobrado en el período
        total_collected = (
            Payment.objects.filter(
                paid_at__date__gte=date_from,
                paid_at__date__lte=date_to,
            ).aggregate(total=Sum("amount"))["total"] or 0
        )

        # OTs con cobro pendiente (READY_FOR_PICKUP o DELIVERED con quote aprobada y saldo)
        # Calculamos por orden cuánto está pagado vs aprobado
        pending_orders_data = []
        candidate_orders = WorkOrder.objects.filter(
            status__in=[WorkOrder.Status.READY_FOR_PICKUP, WorkOrder.Status.DELIVERED],
        ).select_related("customer", "device")

        for order in candidate_orders:
            approved_quote = order.quotes.filter(status=Quote.Status.APPROVED).order_by("-version").first()
            if not approved_quote:
                continue
            paid = Payment.objects.filter(work_order=order).aggregate(s=Sum("amount"))["s"] or 0
            balance = float(approved_quote.total) - float(paid)
            if balance > 0:
                pending_orders_data.append({
                    "order": order,
                    "total": approved_quote.total,
                    "paid": paid,
                    "balance": round(balance, 2),
                })

        pending_orders_data.sort(key=lambda x: x["balance"], reverse=True)
        total_pending = sum(o["balance"] for o in pending_orders_data)

        # Promedio de ticket
        approved_quotes_count = Quote.objects.filter(
            status=Quote.Status.APPROVED,
            answered_at__date__gte=date_from,
            answered_at__date__lte=date_to,
        ).count()
        avg_ticket = round(float(total_quoted) / approved_quotes_count, 2) if approved_quotes_count else 0

        # Cobros por método de pago
        by_method = (
            Payment.objects.filter(
                paid_at__date__gte=date_from,
                paid_at__date__lte=date_to,
            )
            .values("method")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        method_map = dict(Payment.METHOD_CHOICES)
        method_labels = [method_map.get(r["method"], r["method"]) for r in by_method]
        method_totals = [float(r["total"]) for r in by_method]

        context.update({
            "date_from": date_from,
            "date_to": date_to,
            "total_quoted": total_quoted,
            "total_collected": total_collected,
            "total_pending": round(total_pending, 2),
            "pending_orders": pending_orders_data,
            "avg_ticket": avg_ticket,
            "approved_quotes_count": approved_quotes_count,
            # Serialized as JSON for Chart.js
            "method_labels_json": json.dumps(method_labels),
            "method_totals_json": json.dumps(method_totals),
            "has_payment_data": bool(method_labels),
        })
        return context
