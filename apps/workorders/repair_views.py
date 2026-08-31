"""Vistas para el módulo de reparación: WorkLogs y FinalTests."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from apps.workorders.repair_service import RepairService

from .forms import FinalTestForm, FinalTestResultForm, WorkLogForm
from .models import FinalTest, WorkOrder


class RepairView(LoginRequiredMixin, TemplateView):
    """Vista unificada de reparación: WorkLogs + FinalTests."""

    template_name = "workorders/repair.html"

    def get_context_data(self, **kwargs):
        order = get_object_or_404(WorkOrder, pk=self.kwargs["pk"])
        return {
            "order": order,
            "work_logs": order.work_logs.select_related("author").order_by("created_at"),
            "final_tests": order.final_tests.select_related("tested_by").order_by("name"),
            "log_form": WorkLogForm(),
            "test_form": FinalTestForm(),
            "result_form": FinalTestResultForm(),
            "total_minutes": RepairService.get_total_minutes(order),
            "ready_errors": RepairService.validate_ready_for_pickup(order),
        }


class WorkLogCreateView(LoginRequiredMixin, View):
    """POST: agrega una entrada de trabajo."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        form = WorkLogForm(request.POST)
        if form.is_valid():
            RepairService.add_log(work_order=order, actor=request.user, **form.cleaned_data)
            messages.success(request, "Entrada de trabajo registrada.")
        else:
            messages.error(request, "Error al registrar la entrada.")
        return redirect("repair-view", pk=pk)


class FinalTestCreateView(LoginRequiredMixin, View):
    """POST: agrega una prueba final."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        form = FinalTestForm(request.POST)
        if form.is_valid():
            RepairService.add_final_test(work_order=order, actor=request.user, **form.cleaned_data)
            messages.success(request, "Prueba agregada.")
        return redirect("repair-view", pk=pk)


class FinalTestUpdateView(LoginRequiredMixin, View):
    """POST: actualiza el resultado de una prueba final."""

    def post(self, request, pk, test_pk):
        test = get_object_or_404(FinalTest, pk=test_pk, work_order__pk=pk)
        form = FinalTestResultForm(request.POST)
        if form.is_valid():
            RepairService.set_test_result(test=test, actor=request.user, **form.cleaned_data)
            messages.success(request, f"Prueba '{test.name}' actualizada.")
        return redirect("repair-view", pk=pk)


class MarkReadyForPickupView(LoginRequiredMixin, View):
    """POST: valida pruebas y avanza la orden a READY_FOR_PICKUP."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        errors = RepairService.validate_ready_for_pickup(order)
        if errors:
            for e in errors:
                messages.error(request, e)
            return redirect("repair-view", pk=pk)
        from .services import WorkOrderService
        WorkOrderService.transition(
            order=order,
            actor=request.user,
            to_status=WorkOrder.Status.READY_FOR_PICKUP,
            comment="Pruebas finales aprobadas.",
        )
        messages.success(request, f"Orden {order.number} marcada como lista para retirar.")
        return redirect("workorder-detail", pk=pk)
