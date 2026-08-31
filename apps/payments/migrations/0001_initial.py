"""Migración inicial de la app de pagos."""
import uuid

import django.db.models.deletion
import django.utils.timezone
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
            name="Payment",
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
                    "amount",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Monto (ARS)"
                    ),
                ),
                (
                    "method",
                    models.CharField(
                        choices=[
                            ("cash", "Efectivo"),
                            ("transfer", "Transferencia bancaria"),
                            ("card_debit", "Tarjeta de débito"),
                            ("card_credit", "Tarjeta de crédito"),
                            ("mercado_pago", "Mercado Pago"),
                            ("other", "Otro"),
                        ],
                        default="cash",
                        max_length=20,
                        verbose_name="Método de pago",
                    ),
                ),
                (
                    "reference",
                    models.CharField(blank=True, max_length=100, verbose_name="Referencia"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notas")),
                (
                    "paid_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Fecha de pago"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Registrado en"),
                ),
                (
                    "registered_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="registered_payments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Registrado por",
                    ),
                ),
                (
                    "work_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payments",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pago",
                "verbose_name_plural": "Pagos",
                "ordering": ["-paid_at"],
            },
        ),
    ]
