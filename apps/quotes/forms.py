"""Formularios para la app de presupuestos."""
from django import forms
from django.forms import inlineformset_factory

from .models import Quote, QuoteItem


class QuoteItemForm(forms.ModelForm):
    """Formulario para un ítem de presupuesto."""

    class Meta:
        model = QuoteItem
        fields = ["position", "item_type", "description", "quantity", "unit_price", "internal_unit_cost"]
        widgets = {
            "position": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "item_type": forms.Select(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "unit_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "internal_unit_cost": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
        }
        labels = {
            "position": "Pos.",
            "item_type": "Tipo",
            "description": "Descripción",
            "quantity": "Cant.",
            "unit_price": "Precio unit.",
            "internal_unit_cost": "Costo interno",
        }


QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=1,
    can_delete=True,
)


class QuoteSendForm(forms.Form):
    """Formulario para marcar un presupuesto como enviado."""

    channel = forms.ChoiceField(
        choices=Quote.SentChannel.choices,
        label="Canal de envío",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class QuoteAnswerForm(forms.Form):
    """Formulario para registrar la respuesta del cliente a un presupuesto."""

    answered_by_name = forms.CharField(
        max_length=160,
        label="Respondido por",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del cliente o representante"}),
    )
    answer_channel = forms.ChoiceField(
        choices=Quote.SentChannel.choices,
        label="Canal",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    answer_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        label="Comentario",
    )
