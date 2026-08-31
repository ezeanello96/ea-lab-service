"""Vistas para la app de presupuestos."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.workorders.models import WorkOrder

from .forms import QuoteAnswerForm, QuoteItemFormSet, QuoteSendForm
from .models import Quote
from .services import QuoteError, QuoteService


class QuoteListView(LoginRequiredMixin, View):
    """Lista de presupuestos de una orden."""

    def get(self, request, order_pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quotes = order.quotes.prefetch_related("items").order_by("-version")
        return render(request, "quotes/quote_list.html", {"order": order, "quotes": quotes})


class QuoteCreateView(LoginRequiredMixin, View):
    """Crea nueva versión de presupuesto."""

    def post(self, request, order_pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        try:
            quote = QuoteService.create_version(work_order=order, actor=request.user)
            messages.success(request, f"Presupuesto v{quote.version} creado.")
            return redirect("quote-detail", order_pk=order.pk, pk=quote.pk)
        except QuoteError as e:
            messages.error(request, str(e))
            return redirect("quote-list", order_pk=order.pk)


class QuoteDetailView(LoginRequiredMixin, View):
    """Detalle + editor de ítems de un presupuesto."""

    template_name = "quotes/quote_detail.html"

    def _get_can_view_costs(self, user):
        return getattr(getattr(user, "profile", None), "can_view_costs", False)

    def get(self, request, order_pk, pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quote = get_object_or_404(Quote, pk=pk, work_order=order)
        formset = QuoteItemFormSet(instance=quote) if quote.is_editable else None
        return render(request, self.template_name, {
            "order": order,
            "quote": quote,
            "formset": formset,
            "send_form": QuoteSendForm(),
            "answer_form": QuoteAnswerForm(),
            "can_view_costs": self._get_can_view_costs(request.user),
        })

    def post(self, request, order_pk, pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quote = get_object_or_404(Quote, pk=pk, work_order=order)

        if not quote.is_editable:
            messages.error(request, "Este presupuesto no puede editarse.")
            return redirect("quote-detail", order_pk=order.pk, pk=quote.pk)

        formset = QuoteItemFormSet(request.POST, instance=quote)
        if formset.is_valid():
            items = formset.save(commit=False)
            for item in items:
                item.line_total = item.compute_line_total()
                item.save()
            for obj in formset.deleted_objects:
                obj.delete()
            QuoteService.recalculate(quote=quote)
            messages.success(request, "Presupuesto actualizado.")
            return redirect("quote-detail", order_pk=order.pk, pk=quote.pk)

        return render(request, self.template_name, {
            "order": order,
            "quote": quote,
            "formset": formset,
            "send_form": QuoteSendForm(),
            "answer_form": QuoteAnswerForm(),
            "can_view_costs": self._get_can_view_costs(request.user),
        })


class QuoteSendView(LoginRequiredMixin, View):
    """POST: marca el presupuesto como enviado."""

    def post(self, request, order_pk, pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quote = get_object_or_404(Quote, pk=pk, work_order=order)
        form = QuoteSendForm(request.POST)
        if form.is_valid():
            try:
                QuoteService.send(quote=quote, actor=request.user, channel=form.cleaned_data["channel"])
                messages.success(request, "Presupuesto marcado como enviado.")
            except QuoteError as e:
                messages.error(request, str(e))
        return redirect("quote-detail", order_pk=order.pk, pk=quote.pk)


class QuoteApproveView(LoginRequiredMixin, View):
    """POST: aprueba el presupuesto."""

    def post(self, request, order_pk, pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quote = get_object_or_404(Quote, pk=pk, work_order=order)
        form = QuoteAnswerForm(request.POST)
        if form.is_valid():
            try:
                QuoteService.approve(quote=quote, actor=request.user, **form.cleaned_data)
                messages.success(request, "Presupuesto aprobado. La orden avanza a reparación.")
            except QuoteError as e:
                messages.error(request, str(e))
        return redirect("workorder-detail", pk=order.pk)


class QuoteRejectView(LoginRequiredMixin, View):
    """POST: rechaza el presupuesto."""

    def post(self, request, order_pk, pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quote = get_object_or_404(Quote, pk=pk, work_order=order)
        form = QuoteAnswerForm(request.POST)
        if form.is_valid():
            try:
                QuoteService.reject(quote=quote, actor=request.user, **form.cleaned_data)
                messages.success(request, "Presupuesto rechazado.")
            except QuoteError as e:
                messages.error(request, str(e))
        return redirect("workorder-detail", pk=order.pk)


class QuotePDFView(LoginRequiredMixin, View):
    """Genera el PDF del presupuesto con WeasyPrint."""

    def get(self, request, order_pk, pk):
        order = get_object_or_404(WorkOrder, pk=order_pk)
        quote = get_object_or_404(Quote, pk=pk, work_order=order)
        from django.template.loader import render_to_string

        try:
            from weasyprint import HTML  # type: ignore[import]

            html_string = render_to_string(
                "quotes/quote_pdf.html",
                {
                    "quote": quote,
                    "order": order,
                    "items": quote.items.order_by("position"),
                    "business": _get_business(),
                },
                request=request,
            )
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()
            from django.http import HttpResponse
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'inline; filename="presupuesto-{order.number}-v{quote.version}.pdf"'
            )
            return response
        except ImportError:
            messages.error(
                request,
                "WeasyPrint no está instalado. Instale la dependencia para generar PDFs.",
            )
            return redirect("quote-detail", order_pk=order.pk, pk=quote.pk)


def _get_business():
    try:
        from apps.core.models import BusinessSettings
        return BusinessSettings.objects.first()
    except Exception:
        return None
