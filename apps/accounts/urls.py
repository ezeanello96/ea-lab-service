"""URLs de la app de cuentas."""
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("telegram/vincular/", views.GeneratePairingCodeView.as_view(), name="telegram-pair"),
    # Gestión de usuarios (solo staff)
    path("usuarios/", views.UserListView.as_view(), name="user-list"),
    path("usuarios/nuevo/", views.UserCreateView.as_view(), name="user-create"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="user-update"),
    path("usuarios/<int:pk>/activar/", views.UserToggleActiveView.as_view(), name="user-toggle-active"),
]
