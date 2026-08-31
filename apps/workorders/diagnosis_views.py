"""Vistas para la gestión de diagnósticos técnicos."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.workorders.diagnosis_service import DiagnosisError, DiagnosisService

from .forms import DiagnosisForm
from .models import Diagnosis, WorkOrder


class DiagnosisView(LoginRequiredMixin, View):
    """GET: muestra el formulario de diagnóstico (crea borrador si no existe).
    POST: guarda borrador o finaliza según el botón presionado.
    """

    template_name = "workorders/diagnosis.html"

    def get(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        diagnosis = DiagnosisService.get_or_create_draft(work_order=order, technician=request.user)
        form = DiagnosisForm(instance=diagnosis)
        return render(request, self.template_name, {
            "order": order,
            "diagnosis": diagnosis,
            "form": form,
        })

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        diagnosis, _ = Diagnosis.objects.get_or_create(
            work_order=order,
            defaults={"technician": request.user, "started_at": timezone.now()},
        )

        if diagnosis.is_final:
            messages.error(request, "El diagnóstico ya fue finalizado y no puede editarse.")
            return redirect("workorder-detail", pk=order.pk)

        form = DiagnosisForm(request.POST, instance=diagnosis)
        action = request.POST.get("action", "save")

        if form.is_valid():
            data = form.cleaned_data
            try:
                DiagnosisService.save_draft(diagnosis=diagnosis, actor=request.user, **data)
                if action == "finalize":
                    DiagnosisService.finalize(diagnosis=diagnosis, actor=request.user)
                    messages.success(request, "Diagnóstico finalizado correctamente.")
                else:
                    messages.success(request, "Diagnóstico guardado como borrador.")
                return redirect("workorder-detail", pk=order.pk)
            except DiagnosisError as e:
                messages.error(request, str(e))

        return render(request, self.template_name, {
            "order": order,
            "diagnosis": diagnosis,
            "form": form,
        })
