"""Migración inicial de la app de auditoría."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "source",
                    models.CharField(
                        choices=[("WEB", "Web"), ("API", "API"), ("TELEGRAM", "Telegram"), ("SYSTEM", "Sistema")],
                        db_index=True,
                        default="WEB",
                        max_length=20,
                        verbose_name="Origen",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("login", "Inicio de sesión"),
                            ("logout", "Cierre de sesión"),
                            ("login_failed", "Intento de inicio de sesión fallido"),
                            ("create", "Creación"),
                            ("update", "Modificación"),
                            ("delete", "Eliminación"),
                            ("view", "Visualización"),
                            ("export", "Exportación"),
                            ("payment", "Pago"),
                            ("status_change", "Cambio de estado"),
                            ("deliver", "Entrega"),
                            ("other", "Otro"),
                        ],
                        db_index=True,
                        max_length=50,
                        verbose_name="Acción",
                    ),
                ),
                ("object_id", models.CharField(blank=True, max_length=100, verbose_name="ID del objeto")),
                ("object_repr", models.CharField(blank=True, max_length=500, verbose_name="Representación del objeto")),
                ("changes", models.JSONField(blank=True, null=True, verbose_name="Cambios realizados")),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True, verbose_name="Dirección IP")),
                ("user_agent", models.TextField(blank=True, verbose_name="User Agent")),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha y hora")),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Actor",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="contenttypes.contenttype",
                        verbose_name="Tipo de contenido",
                    ),
                ),
            ],
            options={
                "verbose_name": "Registro de auditoría",
                "verbose_name_plural": "Registros de auditoría",
                "ordering": ["-timestamp"],
                "indexes": [
                    models.Index(fields=["actor", "timestamp"], name="audit_actor_timestamp_idx"),
                    models.Index(fields=["action", "timestamp"], name="audit_action_timestamp_idx"),
                    models.Index(fields=["source", "timestamp"], name="audit_source_timestamp_idx"),
                ],
            },
        ),
    ]
