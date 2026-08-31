"""Formularios para la app de clientes."""
from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):
    """Formulario para crear y editar clientes."""

    class Meta:
        model = Customer
        fields = [
            "full_name",
            "business_name",
            "document_type",
            "document_number",
            "phone",
            "email",
            "address",
            "preferred_channel",
            "notes",
            "marketing_consent",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "business_name": forms.TextInput(attrs={"class": "form-control"}),
            "document_type": forms.Select(attrs={"class": "form-control"}),
            "document_number": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "preferred_channel": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "full_name": "Nombre completo",
            "business_name": "Razón social",
            "document_type": "Tipo de documento",
            "document_number": "Número de documento",
            "phone": "Teléfono",
            "email": "Email",
            "address": "Dirección",
            "preferred_channel": "Canal preferido",
            "notes": "Notas internas",
            "marketing_consent": "Consentimiento comercial",
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            raise forms.ValidationError("El teléfono es obligatorio.")
        return phone


class CustomerSearchForm(forms.Form):
    """Formulario de búsqueda de clientes."""

    q = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre, teléfono, email, documento...",
            }
        ),
    )
