"""Formularios de la app de cuentas."""
from django import forms
from django.contrib.auth import authenticate


class LoginForm(forms.Form):
    """Formulario de inicio de sesión en español."""

    usuario = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre de usuario",
                "autofocus": True,
                "autocomplete": "username",
            }
        ),
        error_messages={
            "required": "El nombre de usuario es obligatorio.",
            "max_length": "El nombre de usuario no puede superar los 150 caracteres.",
        },
    )
    contrasena = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contraseña",
                "autocomplete": "current-password",
            }
        ),
        error_messages={
            "required": "La contraseña es obligatoria.",
        },
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("usuario")
        password = cleaned_data.get("contrasena")

        if username and password:
            self._user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self._user_cache is None:
                raise forms.ValidationError(
                    "Usuario o contraseña incorrectos. Por favor verificá los datos ingresados.",
                    code="invalid_login",
                )
            if not self._user_cache.is_active:
                raise forms.ValidationError(
                    "Esta cuenta está desactivada.",
                    code="inactive",
                )

        return cleaned_data

    def get_user(self):
        """Retorna el usuario autenticado."""
        return self._user_cache
