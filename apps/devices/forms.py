"""Formularios para la app de equipos."""
from django import forms

from .models import Device


class DeviceForm(forms.ModelForm):
    """Formulario para crear y editar equipos."""

    class Meta:
        model = Device
        fields = [
            "device_type",
            "brand",
            "model",
            "serial_number",
            "alias",
            "operating_system",
            "cpu",
            "ram_description",
            "storage_description",
            "gpu_description",
            "permanent_notes",
        ]
        widgets = {
            "device_type": forms.Select(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "serial_number": forms.TextInput(attrs={"class": "form-control"}),
            "alias": forms.TextInput(attrs={"class": "form-control"}),
            "operating_system": forms.TextInput(attrs={"class": "form-control"}),
            "cpu": forms.TextInput(attrs={"class": "form-control"}),
            "ram_description": forms.TextInput(attrs={"class": "form-control"}),
            "storage_description": forms.TextInput(attrs={"class": "form-control"}),
            "gpu_description": forms.TextInput(attrs={"class": "form-control"}),
            "permanent_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
        labels = {
            "device_type": "Tipo de equipo",
            "brand": "Marca",
            "model": "Modelo",
            "serial_number": "Número de serie",
            "alias": "Alias",
            "operating_system": "Sistema operativo",
            "cpu": "Procesador",
            "ram_description": "Memoria RAM",
            "storage_description": "Almacenamiento",
            "gpu_description": "Tarjeta de video",
            "permanent_notes": "Observaciones permanentes",
        }
