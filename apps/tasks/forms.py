"""Formularios para tareas."""
from django import forms
from django.contrib.auth.models import User

from .models import Task


class TaskForm(forms.ModelForm):
    due_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
        label="Fecha límite",
    )

    class Meta:
        model = Task
        fields = [
            "title", "description", "priority", "status",
            "due_at", "assigned_to", "work_order", "customer", "device",
            "recurrence_rule",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "recurrence_rule": forms.TextInput(attrs={"placeholder": "Ej: daily, weekly"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True).order_by("username")
        self.fields["assigned_to"].required = False
        self.fields["work_order"].required = False
        self.fields["customer"].required = False
        self.fields["device"].required = False
        self.fields["recurrence_rule"].required = False
