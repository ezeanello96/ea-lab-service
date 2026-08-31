"""Fixtures compartidas para toda la suite de pruebas."""
import pytest
from django.contrib.auth.models import User


@pytest.fixture
def admin_user(db):
    """Superusuario para tests que requieren permisos de administrador."""
    user = User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="testpass123",
    )
    return user


@pytest.fixture
def regular_user(db):
    """Usuario sin permisos especiales."""
    user = User.objects.create_user(
        username="user",
        email="user@test.com",
        password="testpass123",
    )
    return user


@pytest.fixture
def client_logged_in(client, regular_user):
    """Cliente HTTP con sesión iniciada como usuario regular."""
    client.force_login(regular_user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Cliente HTTP con sesión iniciada como administrador."""
    client.force_login(admin_user)
    return client
