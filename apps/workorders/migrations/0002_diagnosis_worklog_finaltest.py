"""Migración que agrega Diagnosis, WorkLog y FinalTest a la app de órdenes."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workorders", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Diagnosis",
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
                (
                    "status",
                    models.CharField(
                        choices=[("DRAFT", "Borrador"), ("FINAL", "Finalizado")],
                        default="DRAFT",
                        max_length=10,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "reported_problem_summary",
                    models.TextField(blank=True, verbose_name="Resumen del problema reportado"),
                ),
                ("findings", models.TextField(blank=True, verbose_name="Hallazgos")),
                ("tests_performed", models.TextField(blank=True, verbose_name="Pruebas realizadas")),
                (
                    "recommended_solution",
                    models.TextField(blank=True, verbose_name="Solución recomendada"),
                ),
                ("risk_notes", models.TextField(blank=True, verbose_name="Notas de riesgo")),
                (
                    "repairable",
                    models.BooleanField(
                        blank=True,
                        null=True,
                        verbose_name="¿Tiene reparación?",
                        help_text="Nulo mientras es borrador.",
                    ),
                ),
                (
                    "estimated_hours",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=6,
                        null=True,
                        verbose_name="Horas estimadas",
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True, verbose_name="Inicio")),
                (
                    "completed_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Finalizado en"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "technician",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="diagnoses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Técnico",
                    ),
                ),
                (
                    "work_order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="diagnosis",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Diagnóstico",
                "verbose_name_plural": "Diagnósticos",
            },
        ),
        migrations.CreateModel(
            name="WorkLog",
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
                (
                    "entry_type",
                    models.CharField(
                        choices=[
                            ("NOTE", "Nota"),
                            ("REPAIR", "Reparación"),
                            ("TEST", "Prueba"),
                            ("PART", "Repuesto"),
                            ("CUSTOMER_CONTACT", "Contacto con cliente"),
                            ("OTHER", "Otro"),
                        ],
                        default="NOTE",
                        max_length=20,
                        verbose_name="Tipo de entrada",
                    ),
                ),
                ("description", models.TextField(verbose_name="Descripción")),
                (
                    "minutes_spent",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Minutos invertidos",
                    ),
                ),
                (
                    "is_customer_visible",
                    models.BooleanField(default=False, verbose_name="Visible al cliente"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="work_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Autor",
                    ),
                ),
                (
                    "work_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="work_logs",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Entrada de trabajo",
                "verbose_name_plural": "Entradas de trabajo",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="FinalTest",
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
                ("name", models.CharField(max_length=200, verbose_name="Prueba")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendiente"),
                            ("PASSED", "Aprobado"),
                            ("FAILED", "Fallido"),
                            ("NOT_APPLICABLE", "No aplica"),
                        ],
                        default="PENDING",
                        max_length=20,
                        verbose_name="Resultado",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notas")),
                (
                    "tested_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Probado en"),
                ),
                (
                    "tested_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="final_tests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Probado por",
                    ),
                ),
                (
                    "work_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="final_tests",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prueba final",
                "verbose_name_plural": "Pruebas finales",
                "ordering": ["name"],
            },
        ),
    ]
