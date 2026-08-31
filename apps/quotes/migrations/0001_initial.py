"""Migración inicial de la app de presupuestos — modelos Quote y QuoteItem actuales."""
import uuid
from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("workorders", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Quote",
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
                ("version", models.PositiveIntegerField(verbose_name="Versión")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("DRAFT", "Borrador"),
                            ("SENT", "Enviado"),
                            ("APPROVED", "Aprobado"),
                            ("REJECTED", "Rechazado"),
                            ("EXPIRED", "Vencido"),
                            ("REPLACED", "Reemplazado"),
                        ],
                        db_index=True,
                        default="DRAFT",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                ("currency_code", models.CharField(default="ARS", max_length=3, verbose_name="Moneda")),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=14,
                        verbose_name="Subtotal",
                    ),
                ),
                (
                    "discount_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=14,
                        verbose_name="Descuento",
                    ),
                ),
                (
                    "tax_rate",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=5,
                        verbose_name="Tasa de IVA (%)",
                    ),
                ),
                (
                    "tax_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=14,
                        verbose_name="IVA",
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=14,
                        verbose_name="Total",
                    ),
                ),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Válido hasta")),
                ("terms", models.TextField(blank=True, verbose_name="Condiciones")),
                ("internal_notes", models.TextField(blank=True, verbose_name="Notas internas")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="Enviado en")),
                (
                    "sent_channel",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PHONE", "Teléfono"),
                            ("EMAIL", "Email"),
                            ("TELEGRAM", "Telegram"),
                            ("IN_PERSON", "Presencial"),
                            ("OTHER", "Otro"),
                        ],
                        max_length=20,
                        verbose_name="Canal de envío",
                    ),
                ),
                (
                    "answered_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Respondido en"),
                ),
                (
                    "answer_channel",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PHONE", "Teléfono"),
                            ("EMAIL", "Email"),
                            ("TELEGRAM", "Telegram"),
                            ("IN_PERSON", "Presencial"),
                            ("OTHER", "Otro"),
                        ],
                        max_length=20,
                        verbose_name="Canal de respuesta",
                    ),
                ),
                (
                    "answered_by_name",
                    models.CharField(
                        blank=True, max_length=160, verbose_name="Respondido por (nombre)"
                    ),
                ),
                (
                    "answer_comment",
                    models.TextField(blank=True, verbose_name="Comentario de respuesta"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_quotes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creado por",
                    ),
                ),
                (
                    "sent_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sent_quotes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Enviado por",
                    ),
                ),
                (
                    "work_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="quotes",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Presupuesto",
                "verbose_name_plural": "Presupuestos",
                "ordering": ["-version"],
            },
        ),
        migrations.AddConstraint(
            model_name="quote",
            constraint=models.UniqueConstraint(
                fields=["work_order", "version"],
                name="unique_quote_version_per_order",
            ),
        ),
        migrations.CreateModel(
            name="QuoteItem",
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
                ("position", models.PositiveIntegerField(verbose_name="Posición")),
                (
                    "item_type",
                    models.CharField(
                        choices=[
                            ("LABOR", "Mano de obra"),
                            ("PART", "Repuesto"),
                            ("SERVICE", "Servicio"),
                            ("OTHER", "Otro"),
                        ],
                        default="LABOR",
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
                ("description", models.CharField(max_length=500, verbose_name="Descripción")),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="Cantidad"
                    ),
                ),
                (
                    "unit_price",
                    models.DecimalField(
                        decimal_places=2, max_digits=14, verbose_name="Precio unitario"
                    ),
                ),
                (
                    "internal_unit_cost",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=14,
                        null=True,
                        verbose_name="Costo interno unitario",
                    ),
                ),
                (
                    "line_total",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=14,
                        verbose_name="Total línea",
                    ),
                ),
                (
                    "quote",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="quotes.quote",
                        verbose_name="Presupuesto",
                    ),
                ),
            ],
            options={
                "verbose_name": "Ítem de presupuesto",
                "verbose_name_plural": "Ítems de presupuesto",
                "ordering": ["position"],
            },
        ),
        migrations.AddConstraint(
            model_name="quoteitem",
            constraint=models.CheckConstraint(
                check=models.Q(quantity__gt=0), name="quoteitem_quantity_positive"
            ),
        ),
        migrations.AddConstraint(
            model_name="quoteitem",
            constraint=models.CheckConstraint(
                check=models.Q(unit_price__gte=0), name="quoteitem_price_non_negative"
            ),
        ),
    ]
