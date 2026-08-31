"""Tests de autenticación de usuarios."""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse


# ---- Fixtures locales ----

@pytest.fixture
def user(db):
    """Usuario activo con contraseña conocida."""
    return User.objects.create_user(
        username="tecnico",
        email="tecnico@test.com",
        password="ClaveSegura123!",
    )


# ---- Tests ----

class TestLogin:
    """Tests del proceso de inicio de sesión."""

    def test_login_exitoso_redirige_al_dashboard(self, client, user):
        """
        Un usuario con credenciales correctas debe ser redirigido
        al dashboard después de hacer login.
        """
        url = reverse("login")
        response = client.post(url, {
            "usuario": "tecnico",
            "contrasena": "ClaveSegura123!",
        })
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_login_fallido_muestra_error_en_espanol(self, client, user):
        """
        Un intento de login con contraseña incorrecta debe mostrar
        un mensaje de error en español y permanecer en la página de login.
        """
        url = reverse("login")
        response = client.post(url, {
            "usuario": "tecnico",
            "contrasena": "ContraseñaIncorrecta",
        })
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # Debe mostrar algún mensaje de error en español
        assert any(
            phrase in content
            for phrase in ["incorrectos", "incorrecta", "Usuario o contraseña", "contraseña"]
        )

    def test_login_usuario_inexistente_muestra_error(self, client, db):
        """Un usuario que no existe no debe generar un 500."""
        url = reverse("login")
        response = client.post(url, {
            "usuario": "no_existe",
            "contrasena": "cualquier_cosa",
        })
        assert response.status_code == 200

    def test_login_campos_vacios_muestra_errores(self, client, db):
        """Enviar el formulario vacío debe mostrar errores de validación."""
        url = reverse("login")
        response = client.post(url, {})
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "obligatorio" in content.lower() or "requerido" in content.lower() or "required" in content.lower()


class TestDashboardAccess:
    """Tests de control de acceso al dashboard."""

    def test_acceso_sin_login_redirige_a_login(self, client):
        """
        Acceder al dashboard sin autenticarse debe redirigir
        a la página de login.
        """
        url = reverse("dashboard")
        response = client.get(url)
        assert response.status_code == 302
        location = response["Location"]
        assert "/login/" in location

    def test_acceso_con_login_muestra_dashboard(self, client, user):
        """Un usuario autenticado puede ver el dashboard."""
        client.force_login(user)
        url = reverse("dashboard")
        response = client.get(url)
        assert response.status_code == 200

    def test_dashboard_contiene_titulo_en_espanol(self, client, user):
        """El dashboard debe tener contenido en español."""
        client.force_login(user)
        url = reverse("dashboard")
        response = client.get(url)
        content = response.content.decode("utf-8")
        assert "Panel de control" in content or "PC Service" in content


class TestLogout:
    """Tests del proceso de cierre de sesión."""

    def test_logout_cierra_sesion(self, client, user):
        """
        Después de hacer logout, el usuario debe ser redirigido
        al login y no puede acceder al dashboard.
        """
        client.force_login(user)

        # Verificar que está autenticado
        dashboard_url = reverse("dashboard")
        response = client.get(dashboard_url)
        assert response.status_code == 200

        # Hacer logout
        logout_url = reverse("logout")
        response = client.post(logout_url)
        assert response.status_code == 302
        assert "/login/" in response["Location"]

        # Verificar que ya no puede acceder al dashboard
        response = client.get(dashboard_url)
        assert response.status_code == 302
        assert "/login/" in response["Location"]

    def test_logout_via_get_tambien_funciona(self, client, user):
        """El logout por GET también debe cerrar la sesión (compatibilidad)."""
        client.force_login(user)
        logout_url = reverse("logout")
        response = client.get(logout_url)
        assert response.status_code == 302


class TestHealthCheck:
    """Tests del endpoint de salud del sistema."""

    def test_health_retorna_json(self, client, db):
        """El endpoint /health/ debe retornar una respuesta JSON."""
        url = reverse("health")
        response = client.get(url)
        assert response.get("Content-Type", "").startswith("application/json")

    def test_health_contiene_status(self, client, db):
        """La respuesta del health check debe contener el campo 'status'."""
        import json

        url = reverse("health")
        response = client.get(url)
        data = json.loads(response.content)
        assert "status" in data
        assert "db" in data
