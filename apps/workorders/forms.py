"""Formularios para la app de órdenes de trabajo."""
from django import forms
from django.contrib.auth.models import User

from .models import Diagnosis, FinalTest, WorkLog, WorkOrder


class WorkOrderCreateForm(forms.ModelForm):
    """Formulario para crear una orden de trabajo."""

    class Meta:
        model = WorkOrder
        fields = [
            "customer",
            "device",
            "reported_issue",
            "priority",
            "source",
            "assigned_to",
            "intake_condition",
            "received_accessories",
            "internal_notes",
            "diagnosis_due_at",
            "promised_delivery_at",
        ]
        widgets = {
            "customer": forms.HiddenInput(),
            "device": forms.Select(attrs={"class": "form-control"}),
            "reported_issue": forms.Textarea(attrs={"rows": 6, "class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "source": forms.Select(attrs={"class": "form-control"}),
            "assigned_to": forms.Select(attrs={"class": "form-control"}),
            "intake_condition": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "received_accessories": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "internal_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "diagnosis_due_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "promised_delivery_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
        }
        labels = {
            "customer": "Cliente",
            "device": "Equipo",
            "reported_issue": "Problema informado",
            "priority": "Prioridad",
            "source": "Origen",
            "assigned_to": "Asignado a",
            "intake_condition": "Condición de ingreso",
            "received_accessories": "Accesorios recibidos",
            "internal_notes": "Notas internas",
            "diagnosis_due_at": "Límite de diagnóstico",
            "promised_delivery_at": "Entrega prometida",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar usuarios activos como opciones de asignación
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True).order_by(
            "first_name", "last_name"
        )
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].empty_label = "Sin asignar"
        self.fields["customer"].required = False


class WorkOrderTransitionForm(forms.Form):
    """Formulario para cambiar el estado de una orden."""

    to_status = forms.ChoiceField(
        choices=WorkOrder.Status.choices,
        label="Nuevo estado",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        label="Comentario",
    )


class WorkOrderSearchForm(forms.Form):
    """Formulario de búsqueda y filtrado de órdenes."""

    q = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Número, cliente, problema..."}
        ),
    )
    status = forms.ChoiceField(
        required=False,
        label="Estado",
        choices=[("", "Todos los estados")] + list(WorkOrder.Status.choices),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    priority = forms.ChoiceField(
        required=False,
        label="Prioridad",
        choices=[("", "Todas las prioridades")] + list(WorkOrder.Priority.choices),
        widget=forms.Select(attrs={"class": "form-control"}),
    )


# ---------------------------------------------------------------------------
# Formularios de Diagnóstico
# ---------------------------------------------------------------------------

_REPAIRABLE_CHOICES = [
    ("", "Sin definir"),
    ("True", "Sí"),
    ("False", "No"),
]


class DiagnosisForm(forms.ModelForm):
    """Formulario para crear/editar el diagnóstico técnico de una orden."""

    repairable = forms.ChoiceField(
        choices=_REPAIRABLE_CHOICES,
        required=False,
        label="¿Tiene reparación?",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Diagnosis
        fields = [
            "reported_problem_summary",
            "findings",
            "tests_performed",
            "recommended_solution",
            "risk_notes",
            "repairable",
            "estimated_hours",
        ]
        widgets = {
            "reported_problem_summary": forms.Textarea(
                attrs={"rows": 4, "class": "form-control"}
            ),
            "findings": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "tests_performed": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "recommended_solution": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "risk_notes": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "estimated_hours": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
        }
        labels = {
            "reported_problem_summary": "Resumen del problema reportado",
            "findings": "Hallazgos",
            "tests_performed": "Pruebas realizadas",
            "recommended_solution": "Solución recomendada",
            "risk_notes": "Notas de riesgo",
            "estimated_hours": "Horas estimadas",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mapear valor booleano/None del modelo al string del choice
        if self.instance and self.instance.pk:
            if self.instance.repairable is True:
                self.initial["repairable"] = "True"
            elif self.instance.repairable is False:
                self.initial["repairable"] = "False"
            else:
                self.initial["repairable"] = ""

    def clean_repairable(self):
        value = self.cleaned_data.get("repairable")
        if value == "True":
            return True
        if value == "False":
            return False
        return None


# ---------------------------------------------------------------------------
# Formularios de Reparación
# ---------------------------------------------------------------------------


class WorkLogForm(forms.Form):
    """Formulario para registrar una entrada de trabajo."""

    entry_type = forms.ChoiceField(
        choices=WorkLog.EntryType.choices,
        label="Tipo de entrada",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    description = forms.CharField(
        label="Descripción",
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
    )
    minutes_spent = forms.IntegerField(
        required=False,
        min_value=0,
        label="Minutos invertidos",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
    )
    is_customer_visible = forms.BooleanField(
        required=False,
        label="Visible al cliente",
    )


class FinalTestForm(forms.Form):
    """Formulario para agregar una prueba final."""

    name = forms.CharField(
        max_length=200,
        label="Nombre de la prueba",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "ej: encendido, temperaturas, red, audio, video, puertos USB, batería",
            }
        ),
    )


class FinalTestResultForm(forms.Form):
    """Formulario para actualizar el resultado de una prueba final."""

    status = forms.ChoiceField(
        choices=FinalTest.TestStatus.choices,
        label="Resultado",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    notes = forms.CharField(
        required=False,
        label="Notas",
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )
