"""Vistas para la app de clientes."""
import csv
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from .forms import CustomerForm, CustomerSearchForm
from .models import Customer
from .services import CustomerService

logger = logging.getLogger(__name__)


def _normalize_digits(text: str) -> str:
    """Extrae solo los dígitos de un texto."""
    return "".join(c for c in text if c.isdigit())


class CustomerListView(LoginRequiredMixin, ListView):
    """Lista paginada de clientes con búsqueda."""

    model = Customer
    template_name = "customers/customer_list.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        qs = Customer.objects.all().order_by("full_name")
        q = self.request.GET.get("q", "").strip()
        if q:
            digits = _normalize_digits(q)
            filter_q = Q(full_name__icontains=q) | Q(email__icontains=q) | Q(document_number__icontains=q)
            if digits:
                filter_q |= Q(phone_normalized__icontains=digits)
            else:
                filter_q |= Q(phone__icontains=q)
            qs = qs.filter(filter_q)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = CustomerSearchForm(self.request.GET)
        context["q"] = self.request.GET.get("q", "")
        return context

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            return self._export_csv()
        return super().get(request, *args, **kwargs)

    def _export_csv(self):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="clientes.csv"'
        response.write("﻿")  # BOM para Excel
        writer = csv.writer(response)
        writer.writerow(["Nombre", "Razón social", "Teléfono", "Email", "Documento", "Activo", "Alta"])
        for c in self.get_queryset():
            writer.writerow([
                c.full_name,
                c.business_name,
                c.phone,
                c.email,
                f"{c.get_document_type_display()} {c.document_number}".strip(),
                "Sí" if c.is_active else "No",
                c.created_at.strftime("%d/%m/%Y"),
            ])
        return response


class CustomerCreateView(LoginRequiredMixin, View):
    """Vista para crear un nuevo cliente."""

    template_name = "customers/customer_form.html"

    def get(self, request):
        form = CustomerForm()
        return render(request, self.template_name, {"form": form, "is_create": True})

    def post(self, request):
        form = CustomerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Detectar posibles duplicados antes de guardar
            temp = Customer(
                full_name=data["full_name"],
                phone=data["phone"],
                email=data.get("email", ""),
                document_type=data.get("document_type", ""),
                document_number=data.get("document_number", ""),
            )
            temp.phone_normalized = _normalize_digits(data["phone"])
            duplicates = temp.possible_duplicates()
            if duplicates.exists() and not request.POST.get("confirm_duplicate"):
                return render(request, self.template_name, {
                    "form": form,
                    "duplicates": duplicates,
                    "is_create": True,
                })
            try:
                customer = CustomerService.create_customer(
                    actor=request.user,
                    full_name=data["full_name"],
                    phone=data["phone"],
                    email=data.get("email", ""),
                    business_name=data.get("business_name", ""),
                    document_type=data.get("document_type", ""),
                    document_number=data.get("document_number", ""),
                    address=data.get("address", ""),
                    preferred_channel=data.get("preferred_channel", Customer.PreferredChannel.PHONE),
                    notes=data.get("notes", ""),
                    marketing_consent=data.get("marketing_consent", False),
                )
                messages.success(request, f"Cliente '{customer.full_name}' creado correctamente.")
                return redirect(reverse("customer-detail", kwargs={"pk": customer.pk}))
            except Exception as exc:
                logger.exception("Error al crear cliente: %s", exc)
                messages.error(request, f"Error al crear el cliente: {exc}")
        return render(request, self.template_name, {"form": form, "is_create": True})


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """Ficha completa del cliente con equipos y órdenes recientes."""

    model = Customer
    template_name = "customers/customer_detail.html"
    context_object_name = "customer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context["devices"] = customer.devices.filter(is_active=True).order_by("brand", "model")
        context["all_devices"] = customer.devices.all().order_by("-created_at")
        context["recent_orders"] = (
            customer.work_orders
            .select_related("device", "assigned_to")
            .order_by("-received_at")[:10]
        )
        return context


class CustomerUpdateView(LoginRequiredMixin, View):
    """Vista para editar un cliente existente."""

    template_name = "customers/customer_form.html"

    def _get_customer(self, pk):
        return get_object_or_404(Customer, pk=pk)

    def get(self, request, pk):
        customer = self._get_customer(pk)
        form = CustomerForm(instance=customer)
        return render(request, self.template_name, {"form": form, "customer": customer, "is_create": False})

    def post(self, request, pk):
        customer = self._get_customer(pk)
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            data = form.cleaned_data
            try:
                CustomerService.update_customer(
                    customer=customer,
                    actor=request.user,
                    **{k: v for k, v in data.items()},
                )
                messages.success(request, "Cliente actualizado correctamente.")
                return redirect(reverse("customer-detail", kwargs={"pk": customer.pk}))
            except Exception as exc:
                logger.exception("Error al actualizar cliente: %s", exc)
                messages.error(request, f"Error al actualizar el cliente: {exc}")
        return render(request, self.template_name, {"form": form, "customer": customer, "is_create": False})


class CustomerDeactivateView(LoginRequiredMixin, View):
    """Vista para activar o desactivar un cliente (POST)."""

    def post(self, request, pk):
        customer = get_object_or_404(Customer, pk=pk)
        if customer.is_active:
            CustomerService.deactivate_customer(customer=customer, actor=request.user)
            messages.success(request, f"Cliente '{customer.full_name}' desactivado.")
        else:
            CustomerService.reactivate_customer(customer=customer, actor=request.user)
            messages.success(request, f"Cliente '{customer.full_name}' reactivado.")
        return redirect(reverse("customer-detail", kwargs={"pk": customer.pk}))
