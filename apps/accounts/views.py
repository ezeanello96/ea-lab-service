"""Vistas de la app de cuentas."""
import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .forms import LoginForm


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Acceso restringido a usuarios staff (administradores)."""
    login_url = "/login/"

    def test_func(self):
        return self.request.user.is_staff

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _log_audit(request, action, user=None, details=""):
    """Registra un evento de auditoría."""
    try:
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            actor=user,
            action=action,
            ip_address=_get_client_ip(request) or None,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            object_repr=details,
        )
    except Exception:
        logger.warning("No se pudo registrar el evento de auditoría: %s", action)


class LoginView(View):
    """Vista de inicio de sesión."""

    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = LoginForm(request)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            _log_audit(request, "login", user=user, details=f"Sesión iniciada: {user.username}")
            logger.info("Inicio de sesión exitoso: %s desde %s", user.username, _get_client_ip(request))
            next_url = request.GET.get("next", "/")
            return redirect(next_url)
        else:
            username = request.POST.get("usuario", "")
            _log_audit(
                request,
                "login_failed",
                details=f"Intento fallido para usuario: {username}",
            )
            logger.warning(
                "Intento de inicio de sesión fallido para usuario '%s' desde %s",
                username,
                _get_client_ip(request),
            )
            messages.error(request, "Usuario o contraseña incorrectos.")

        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    """Vista de cierre de sesión."""

    def post(self, request):
        if request.user.is_authenticated:
            user = request.user
            _log_audit(request, "logout", user=user, details=f"Sesión cerrada: {user.username}")
            logger.info("Cierre de sesión: %s", user.username)
            logout(request)
        return redirect("login")

    def get(self, request):
        """GET también cierra sesión para compatibilidad."""
        return self.post(request)


class UserListView(StaffRequiredMixin, View):
    """Listado de usuarios del sistema. Solo accesible para staff."""

    template_name = "accounts/user_list.html"

    def get(self, request):
        role_filter = request.GET.get("role", "")
        active_filter = request.GET.get("active", "")

        users = User.objects.select_related("profile").order_by("username")

        if role_filter == "staff":
            users = users.filter(is_staff=True)
        elif role_filter == "tech":
            users = users.filter(is_staff=False)

        if active_filter == "1":
            users = users.filter(is_active=True)
        elif active_filter == "0":
            users = users.filter(is_active=False)

        return render(request, self.template_name, {
            "users": users,
            "role_filter": role_filter,
            "active_filter": active_filter,
        })


class UserCreateView(StaffRequiredMixin, View):
    """Crea un nuevo usuario del sistema."""

    template_name = "accounts/user_form.html"

    def get(self, request):
        return render(request, self.template_name, {"editing": False})

    def post(self, request):
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        is_staff = request.POST.get("is_staff") == "1"
        phone = request.POST.get("phone", "").strip()
        can_view_costs = request.POST.get("can_view_costs") == "1"
        can_deliver = request.POST.get("can_deliver_with_balance") == "1"

        errors = []
        if not username:
            errors.append("El nombre de usuario es obligatorio.")
        if User.objects.filter(username=username).exists():
            errors.append(f"El usuario '{username}' ya existe.")
        if not password:
            errors.append("La contraseña es obligatoria.")
        if password != password2:
            errors.append("Las contraseñas no coinciden.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, self.template_name, {
                "editing": False,
                "form_data": request.POST,
            })

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            is_staff=is_staff,
        )
        from .models import UserProfile
        UserProfile.objects.update_or_create(
            user=user,
            defaults={"phone": phone, "can_view_costs": can_view_costs, "can_deliver_with_balance": can_deliver},
        )
        messages.success(request, f"Usuario '{username}' creado correctamente.")
        return redirect("user-list")


class UserUpdateView(StaffRequiredMixin, View):
    """Edita un usuario existente."""

    template_name = "accounts/user_form.html"

    def _get_user(self, pk):
        return get_object_or_404(User.objects.select_related("profile"), pk=pk)

    def get(self, request, pk):
        target_user = self._get_user(pk)
        return render(request, self.template_name, {"editing": True, "target_user": target_user})

    def post(self, request, pk):
        target_user = self._get_user(pk)
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        new_password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        is_staff = request.POST.get("is_staff") == "1"
        phone = request.POST.get("phone", "").strip()
        can_view_costs = request.POST.get("can_view_costs") == "1"
        can_deliver = request.POST.get("can_deliver_with_balance") == "1"

        if new_password and new_password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, self.template_name, {"editing": True, "target_user": target_user})

        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email
        target_user.is_staff = is_staff
        if new_password:
            target_user.set_password(new_password)
        target_user.save()

        from .models import UserProfile
        UserProfile.objects.update_or_create(
            user=target_user,
            defaults={"phone": phone, "can_view_costs": can_view_costs, "can_deliver_with_balance": can_deliver},
        )
        messages.success(request, f"Usuario '{target_user.username}' actualizado.")
        return redirect("user-list")


class UserToggleActiveView(StaffRequiredMixin, View):
    """Activa o desactiva un usuario (soft delete)."""

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        if target_user == request.user:
            messages.error(request, "No podés desactivar tu propio usuario.")
            return redirect("user-list")
        target_user.is_active = not target_user.is_active
        target_user.save()
        action = "activado" if target_user.is_active else "desactivado"
        messages.success(request, f"Usuario '{target_user.username}' {action}.")
        return redirect("user-list")


@method_decorator(login_required, name="dispatch")
class GeneratePairingCodeView(View):
    """Vista para generar un código de vinculación de Telegram."""

    template_name = "accounts/telegram_pairing.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        from .models import TelegramPairingCode

        try:
            instance, plain_code = TelegramPairingCode.generate_for_user(
                user=request.user,
                created_by=request.user,
            )
            logger.info(
                "Código de vinculación Telegram generado para usuario %s por %s",
                request.user.username,
                request.user.username,
            )
            return render(
                request,
                self.template_name,
                {
                    "plain_code": plain_code,
                    "expires_at": instance.expires_at,
                },
            )
        except Exception:
            logger.exception("Error generando código de vinculación Telegram para %s", request.user.username)
            messages.error(request, "No se pudo generar el código. Intentá de nuevo.")
            return render(request, self.template_name)
