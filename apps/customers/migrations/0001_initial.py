"""Migración inicial de la app de clientes."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerTag",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=60, unique=True, verbose_name="Nombre")),
                ("description", models.TextField(blank=True, verbose_name="Descripción")),
                ("is_active", models.BooleanField(default=True, verbose_name="Activa")),
            ],
            options={
                "verbose_name": "Etiqueta de cliente",
                "verbose_name_plural": "Etiquetas de clientes",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("full_name", models.CharField(max_length=160, verbose_name="Nombre completo")),
                ("business_name", models.CharField(blank=True, max_length=200, verbose_name="Razón social")),
                (
                    "document_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("DNI", "DNI"),
                            ("CUIT", "CUIT"),
                            ("OTHER", "Otro"),
                            ("", "Sin documento"),
                        ],
                        default="",
                        max_length=10,
                        verbose_name="Tipo de documento",
                    ),
                ),
                ("document_number", models.CharField(blank=True, max_length=30, verbose_name="Número de documento")),
                ("phone", models.CharField(max_length=30, verbose_name="Teléfono")),
                (
                    "phone_normalized",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=30,
                        verbose_name="Teléfono normalizado",
                        help_text="Solo dígitos, para búsqueda rápida.",
                    ),
                ),
                ("email", models.EmailField(blank=True, db_index=True, verbose_name="Email")),
                ("address", models.TextField(blank=True, verbose_name="Dirección")),
                (
                    "preferred_channel",
                    models.CharField(
                        choices=[
                            ("PHONE", "Teléfono"),
                            ("EMAIL", "Email"),
                            ("TELEGRAM", "Telegram"),
                            ("IN_PERSON", "Presencial"),
                            ("OTHER", "Otro"),
                        ],
                        default="PHONE",
                        max_length=20,
                        verbose_name="Canal preferido",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notas internas")),
                ("marketing_consent", models.BooleanField(default=False, verbose_name="Consentimiento comercial")),
                ("marketing_consent_at", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de consentimiento")),
                ("marketing_consent_source", models.CharField(blank=True, max_length=100, verbose_name="Origen del consentimiento")),
                ("marketing_opt_out_at", models.DateTimeField(blank=True, null=True, verbose_name="Fecha de baja comercial")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="Activo")),
                ("deactivated_at", models.DateTimeField(blank=True, null=True, verbose_name="Desactivado en")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Creado en")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Actualizado en")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_customers",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creado por",
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True,
                        related_name="customers",
                        to="customers.customertag",
                        verbose_name="Etiquetas",
                    ),
                ),
            ],
            options={
                "verbose_name": "Cliente",
                "verbose_name_plural": "Clientes",
                "ordering": ["full_name"],
                "indexes": [
                    models.Index(fields=["full_name"], name="customer_name_idx"),
                    models.Index(fields=["document_type", "document_number"], name="customer_doc_idx"),
                ],
            },
        ),
    ]
