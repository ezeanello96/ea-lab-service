"""Vistas para la app de equipos."""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from apps.customers.models import Customer

from .forms import DeviceForm
from .models import Device
from .services import DeviceService

logger = logging.getLogger(__name__)


class DeviceListView(LoginRequiredMixin, ListView):
    """Lista global de equipos ordenados por fecha de registro descendente."""

    model = Device
    template_name = "devices/device_list.html"
    context_object_name = "devices"
    paginate_by = 50

    def get_queryset(self):
        qs = Device.objects.select_related("customer").order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(brand__icontains=q)
                | Q(model__icontains=q)
                | Q(alias__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(customer__full_name__icontains=q)
            )
        device_type = self.request.GET.get("tipo", "")
        if device_type:
            qs = qs.filter(device_category__name=device_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["tipo"] = self.request.GET.get("tipo", "")
        from .models import DeviceCategory
        context["device_categories"] = DeviceCategory.objects.filter(is_active=True)
        return context


class DeviceCreateView(LoginRequiredMixin, View):
    """Vista para registrar un equipo para un cliente existente.

    La URL incluye el UUID del cliente: /clientes/<uuid:pk>/equipos/nuevo/
    """

    template_name = "devices/device_form.html"

    def _get_customer(self):
        return get_object_or_404(Customer, pk=self.kwargs["pk"])

    def get(self, request, pk):
        customer = self._get_customer()
        form = DeviceForm()
        return render(request, self.template_name, {
            "form": form,
            "customer": customer,
            "is_create": True,
        })

    def post(self, request, pk):
        customer = self._get_customer()
        form = DeviceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Advertencia si existe duplicado con mismo número de serie
            serial = data.get("serial_number", "")
            duplicates = None
            if serial:
                duplicates = Device.objects.filter(customer=customer, serial_number=serial)
                if duplicates.exists() and not request.POST.get("confirm_duplicate"):
                    return render(request, self.template_name, {
                        "form": form,
                        "customer": customer,
                        "duplicates": duplicates,
                        "is_create": True,
                    })
            try:
                device = DeviceService.create_device(
                    actor=request.user,
                    customer=customer,
                    **data,
                )
                messages.success(request, f"Equipo '{device}' registrado correctamente.")
                return redirect(reverse("customer-detail", kwargs={"pk": customer.pk}))
            except Exception as exc:
                logger.exception("Error al crear equipo: %s", exc)
                messages.error(request, f"Error al registrar el equipo: {exc}")
        return render(request, self.template_name, {
            "form": form,
            "customer": customer,
            "is_create": True,
        })


class DeviceDetailView(LoginRequiredMixin, DetailView):
    """Ficha del equipo con historial de órdenes de trabajo."""

    model = Device
    template_name = "devices/device_detail.html"
    context_object_name = "device"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = (
            self.object.work_orders
            .select_related("customer", "assigned_to")
            .order_by("-received_at")
        )
        return context


class DeviceUpdateView(LoginRequiredMixin, View):
    """Vista para editar un equipo existente."""

    template_name = "devices/device_form.html"

    def _get_device(self, pk):
        return get_object_or_404(Device, pk=pk)

    def get(self, request, pk):
        device = self._get_device(pk)
        form = DeviceForm(instance=device)
        return render(request, self.template_name, {
            "form": form,
            "device": device,
            "customer": device.customer,
            "is_create": False,
        })

    def post(self, request, pk):
        device = self._get_device(pk)
        form = DeviceForm(request.POST, instance=device)
        if form.is_valid():
            data = form.cleaned_data
            try:
                DeviceService.update_device(device=device, actor=request.user, **data)
                messages.success(request, "Equipo actualizado correctamente.")
                return redirect(reverse("device-detail", kwargs={"pk": device.pk}))
            except Exception as exc:
                logger.exception("Error al actualizar equipo: %s", exc)
                messages.error(request, f"Error al actualizar el equipo: {exc}")
        return render(request, self.template_name, {
            "form": form,
            "device": device,
            "customer": device.customer,
            "is_create": False,
        })
