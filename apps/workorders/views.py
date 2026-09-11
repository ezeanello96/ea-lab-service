"""Vistas para la app de órdenes de trabajo."""
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.customers.models import Customer
from apps.devices.models import Device

from .forms import WorkOrderCreateForm, WorkOrderSearchForm, WorkOrderTransitionForm
from .models import WorkOrder
from .services import InvalidStatusTransition, WorkOrderService

logger = logging.getLogger(__name__)


class WorkOrderListView(LoginRequiredMixin, ListView):
    """Lista paginada de órdenes de trabajo con filtros por estado, prioridad y búsqueda."""

    model = WorkOrder
    template_name = "workorders/workorder_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        qs = WorkOrder.objects.select_related("customer", "device", "assigned_to").order_by(
            "-received_at"
        )
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        priority = self.request.GET.get("priority", "").strip()
        if q:
            qs = qs.filter(
                Q(number__icontains=q)
                | Q(customer__full_name__icontains=q)
                | Q(reported_issue__icontains=q)
                | Q(device__brand__icontains=q)
                | Q(device__serial_number__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = WorkOrderSearchForm(self.request.GET)
        context["current_status"] = self.request.GET.get("status", "")
        context["current_priority"] = self.request.GET.get("priority", "")
        context["q"] = self.request.GET.get("q", "")
        return context


class WorkOrderKanbanView(LoginRequiredMixin, TemplateView):
    """Vista Kanban: órdenes activas agrupadas por estado en columnas."""

    template_name = "workorders/workorder_kanban.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_active = list(
            WorkOrder.objects.filter(status__in=WorkOrder.ACTIVE_STATUSES)
            .select_related("customer", "device", "assigned_to")
        )
        # Agrupar por estado manteniendo el orden definido en ACTIVE_STATUSES
        columns = []
        for status in WorkOrder.ACTIVE_STATUSES:
            label = WorkOrder.Status(status).label
            orders_in_col = [o for o in all_active if o.status == status]
            columns.append({
                "status": status,
                "label": label,
                "orders": orders_in_col,
                "count": len(orders_in_col),
            })
        context["columns"] = columns
        context["total_active"] = len(all_active)
        return context


class WorkOrderCreateView(LoginRequiredMixin, View):
    """Vista para crear una nueva orden de trabajo.

    Soporta pre-selección de cliente y equipo via query params:
    GET /ordenes/nueva/?customer=UUID&device=UUID
    """

    template_name = "workorders/workorder_form.html"

    def _build_context(self, form, customer=None, device=None, devices=None):
        return {
            "form": form,
            "customer": customer,
            "device": device,
            "devices": devices or [],
        }

    def get(self, request):
        customer_uuid = request.GET.get("customer")
        device_uuid = request.GET.get("device")
        customer = None
        device = None
        devices = []

        if customer_uuid:
            customer = get_object_or_404(Customer, pk=customer_uuid)
            devices = list(customer.devices.filter(is_active=True))
        if device_uuid:
            device = get_object_or_404(Device, pk=device_uuid)

        form = WorkOrderCreateForm(initial={
            "customer": customer.pk if customer else None,
            "device": device.pk if device else None,
            "assigned_to": request.user.pk,
        })
        if customer:
            form.fields["device"].queryset = customer.devices.filter(is_active=True)
        return render(request, self.template_name, self._build_context(form, customer, device, devices))

    def post(self, request):
        customer_uuid = request.POST.get("customer") or request.GET.get("customer")
        customer = None
        devices = []

        if customer_uuid:
            customer = get_object_or_404(Customer, pk=customer_uuid)
            devices = list(customer.devices.filter(is_active=True))

        form = WorkOrderCreateForm(request.POST)
        if customer:
            form.fields["device"].queryset = customer.devices.filter(is_active=True)

        if form.is_valid():
            data = form.cleaned_data
            # Si customer vino del campo hidden, usarlo; si no, usar el del URL
            order_customer = data.get("customer") or customer
            if not order_customer:
                messages.error(request, "Debe seleccionar un cliente para la orden.")
                return render(request, self.template_name, self._build_context(form, customer, None, devices))
            try:
                order = WorkOrderService.create_order(
                    actor=request.user,
                    customer=order_customer,
                    device=data["device"],
                    reported_issue=data["reported_issue"],
                    priority=data.get("priority", WorkOrder.Priority.NORMAL),
                    source=data.get("source", WorkOrder.Source.WALK_IN),
                    assigned_to=data.get("assigned_to"),
                    intake_condition=data.get("intake_condition", ""),
                    received_accessories=data.get("received_accessories", ""),
                    internal_notes=data.get("internal_notes", ""),
                    diagnosis_due_at=data.get("diagnosis_due_at"),
                    promised_delivery_at=data.get("promised_delivery_at"),
                )
                messages.success(request, f"Orden {order.number} creada correctamente.")
                return redirect(reverse("workorder-detail", kwargs={"pk": order.pk}))
            except Exception as exc:
                logger.exception("Error al crear orden: %s", exc)
                messages.error(request, f"Error al crear la orden: {exc}")
        return render(request, self.template_name, self._build_context(form, customer, None, devices))


class WorkOrderDetailView(LoginRequiredMixin, DetailView):
    """Detalle completo de una orden de trabajo con historial y acciones."""

    model = WorkOrder
    template_name = "workorders/workorder_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return WorkOrder.objects.select_related(
            "customer", "device", "assigned_to", "created_by", "related_order"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        allowed_statuses = WorkOrder.ALLOWED_TRANSITIONS.get(order.status, [])
        context["allowed_transitions"] = [
            (s, WorkOrder.Status(s).label) for s in allowed_statuses
        ]
        context["status_history"] = order.status_history.select_related("actor").order_by("created_at")
        # Calcular saldo pendiente real
        balance = 0.0
        try:
            from django.db.models import Sum
            from apps.quotes.models import Quote
            from apps.payments.models import Payment
            approved_quote = (
                order.quotes.filter(status=Quote.Status.APPROVED).order_by("-version").first()
            )
            if approved_quote:
                paid = Payment.objects.filter(work_order=order).aggregate(s=Sum("amount"))["s"] or 0
                balance = max(0.0, float(approved_quote.total) - float(paid))
        except Exception:
            pass
        context["balance"] = balance
        return context


class WorkOrderTransitionView(LoginRequiredMixin, View):
    """Vista para realizar una transición de estado en una orden (POST)."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        to_status = request.POST.get("to_status", "")
        comment = request.POST.get("comment", "")
        try:
            WorkOrderService.transition(
                order=order,
                actor=request.user,
                to_status=to_status,
                comment=comment,
            )
            new_label = WorkOrder.Status(to_status).label
            messages.success(
                request,
                f"Estado de la orden {order.number} actualizado a '{new_label}'.",
            )
        except InvalidStatusTransition as exc:
            messages.error(request, str(exc))
        except ValueError as exc:
            messages.error(request, f"Estado inválido: {exc}")
        except Exception as exc:
            logger.exception("Error en transición de orden %s: %s", pk, exc)
            messages.error(request, f"Error al realizar la transición: {exc}")
        return redirect(reverse("workorder-detail", kwargs={"pk": pk}))


class GoogleOAuthInitView(LoginRequiredMixin, View):
    """Inicia el flujo OAuth 2.0 con Google para acceder a Calendar."""

    def get(self, request):
        if not request.user.is_staff:
            messages.error(request, "Solo los administradores pueden conectar Google Calendar.")
            return redirect(reverse("dashboard"))
        try:
            from .google_calendar_service import get_oauth_authorization_url
            auth_url = get_oauth_authorization_url()
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(auth_url)
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return redirect(reverse("dashboard"))


class GoogleOAuthCallbackView(LoginRequiredMixin, View):
    """Recibe el código de autorización de Google y persiste el token."""

    def get(self, request):
        code = request.GET.get("code")
        if not code:
            messages.error(request, "No se recibió el código de autorización de Google.")
            return redirect(reverse("dashboard"))
        try:
            from .google_calendar_service import exchange_code_for_token
            exchange_code_for_token(code)
            messages.success(request, "Google Calendar conectado exitosamente.")
        except Exception as exc:
            messages.error(request, f"Error al conectar Google Calendar: {exc}")
        return redirect(reverse("dashboard"))


class WorkOrderCalendarCreateView(LoginRequiredMixin, View):
    """POST: crea un evento en Google Calendar para una OT."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        try:
            from .google_calendar_service import create_event
            result = create_event(order)
            if result:
                event_id, html_link = result
                order.google_calendar_event_id = event_id
                order.google_calendar_event_link = html_link
                order.save(update_fields=["google_calendar_event_id", "google_calendar_event_link"])
                messages.success(request, "Evento creado en Google Calendar.")
            else:
                messages.error(request, "No se pudo crear el evento. Verificá que Google Calendar esté conectado.")
        except Exception as exc:
            messages.error(request, f"Error al crear el evento: {exc}")
        return redirect(reverse("workorder-detail", kwargs={"pk": pk}))


class WorkOrderCalendarUpdateView(LoginRequiredMixin, View):
    """POST: actualiza el evento de Calendar vinculado a la OT."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        try:
            from .google_calendar_service import update_event
            if update_event(order):
                messages.success(request, "Evento de Calendar actualizado.")
            else:
                messages.error(request, "No se pudo actualizar el evento.")
        except Exception as exc:
            messages.error(request, f"Error al actualizar el evento: {exc}")
        return redirect(reverse("workorder-detail", kwargs={"pk": pk}))


class WorkOrderCalendarDeleteView(LoginRequiredMixin, View):
    """POST: elimina el evento de Calendar vinculado a la OT."""

    def post(self, request, pk):
        order = get_object_or_404(WorkOrder, pk=pk)
        try:
            from .google_calendar_service import delete_event
            if delete_event(order):
                order.google_calendar_event_id = ""
                order.google_calendar_event_link = ""
                order.save(update_fields=["google_calendar_event_id", "google_calendar_event_link"])
                messages.success(request, "Evento eliminado de Google Calendar.")
            else:
                messages.error(request, "No se pudo eliminar el evento.")
        except Exception as exc:
            messages.error(request, f"Error al eliminar el evento: {exc}")
        return redirect(reverse("workorder-detail", kwargs={"pk": pk}))


class WorkOrderReceiptPDFView(LoginRequiredMixin, View):
    """Genera el PDF del recibo de recepción de la orden con WeasyPrint."""

    def get(self, request, pk):
        order = get_object_or_404(
            WorkOrder.objects.select_related("customer", "device", "assigned_to", "created_by"),
            pk=pk,
        )
        from django.template.loader import render_to_string

        try:
            from weasyprint import HTML  # type: ignore[import]
        except ImportError:
            from django.contrib import messages as msg
            msg.error(request, "WeasyPrint no está instalado. No se puede generar el PDF.")
            return redirect(reverse("workorder-detail", kwargs={"pk": pk}))

        try:
            from apps.core.models import BusinessSettings
            business = BusinessSettings.objects.first()
        except Exception:
            business = None

        html_string = render_to_string(
            "workorders/workorder_receipt_pdf.html",
            {"order": order, "business": business},
            request=request,
        )
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
        from django.http import HttpResponse
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'inline; filename="recibo-{order.number}.pdf"'
        )
        return response


class GlobalSearchView(LoginRequiredMixin, View):
    """Búsqueda global en clientes, equipos y órdenes.

    Devuelve HTML parcial si la petición viene de HTMX,
    HTML completo en cualquier otro caso.
    Requiere mínimo 2 caracteres en el parámetro q.
    """

    template_name = "workorders/workorder_search_results.html"

    def get(self, request):
        q = request.GET.get("q", "").strip()
        context = {"q": q, "customers": [], "devices": [], "orders": []}

        if len(q) >= 2:
            digit_q = "".join(c for c in q if c.isdigit())
            customers = Customer.objects.filter(
                Q(full_name__icontains=q)
                | Q(email__icontains=q)
                | Q(phone__icontains=q)
                | (Q(phone_normalized__icontains=digit_q) if digit_q else Q())
            )[:10]

            devices = Device.objects.filter(
                Q(brand__icontains=q)
                | Q(model__icontains=q)
                | Q(serial_number__icontains=q)
                | Q(alias__icontains=q)
            ).select_related("customer")[:10]

            orders = WorkOrder.objects.filter(
                Q(number__icontains=q)
                | Q(reported_issue__icontains=q)
                | Q(customer__full_name__icontains=q)
            ).select_related("customer")[:10]

            context.update({
                "customers": customers,
                "devices": devices,
                "orders": orders,
            })

        # Usar parcial para HTMX, página completa para navegación directa
        # django_htmx establece request.htmx como truthy si es una petición HTMX
        if getattr(request, "htmx", None):
            return render(request, "workorders/_search_dropdown.html", context)
        return render(request, self.template_name, context)
