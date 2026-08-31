"""Migración inicial de órdenes de trabajo, secuencia e historial."""
import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("devices", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderSequence",
            fields=[
                ("year", models.PositiveIntegerField(primary_key=True, serialize=False, verbose_name="Año")),
                ("last_value", models.PositiveIntegerField(default=0, verbose_name="Último valor")),
            ],
            options={"verbose_name": "Secuencia de órdenes", "verbose_name_plural": "Secuencias de órdenes"},
        ),
        migrations.CreateModel(
            name="WorkOrder",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("number", models.CharField(db_index=True, max_length=20, unique=True, verbose_name="Número de orden")),
                (
                    "relation_type",
                    models.CharField(
                        blank=True,
                        choices=[("WARRANTY", "Garantía"), ("REPEAT_ISSUE", "Reincidencia"), ("FOLLOW_UP", "Seguimiento"), ("OTHER", "Otro")],
                        max_length=20,
                        verbose_name="Tipo de relación",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("RECEIVED", "Recibido"),
                            ("PENDING_DIAGNOSIS", "Pendiente de diagnóstico"),
                            ("IN_DIAGNOSIS", "En diagnóstico"),
                            ("AWAITING_APPROVAL", "Esperando aprobación"),
                            ("APPROVED_FOR_REPAIR", "Aprobado para reparar"),
                            ("REJECTED", "Presupuesto rechazado"),
                            ("WAITING_PART", "Esperando repuesto"),
                            ("IN_REPAIR", "En reparación"),
                            ("IN_TESTING", "En pruebas"),
                            ("READY_FOR_PICKUP", "Listo para retirar"),
                            ("DELIVERED", "Entregado"),
                            ("UNREPAIRABLE", "Sin reparación posible"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        db_index=True,
                        default="RECEIVED",
                        max_length=30,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("LOW", "Baja"), ("NORMAL", "Normal"), ("HIGH", "Alta"), ("URGENT", "Urgente")],
                        db_index=True,
                        default="NORMAL",
                        max_length=10,
                        verbose_name="Prioridad",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("WALK_IN", "Presencial"), ("PHONE", "Teléfono"), ("TELEGRAM", "Telegram"), ("REFERRAL", "Referido"), ("WEB", "Web"), ("OTHER", "Otro")],
                        default="WALK_IN",
                        max_length=20,
                        verbose_name="Origen",
                    ),
                ),
                ("reported_issue", models.TextField(verbose_name="Problema informado")),
                ("intake_condition", models.TextField(blank=True, verbose_name="Condición de ingreso")),
                ("received_accessories", models.TextField(blank=True, verbose_name="Accesorios recibidos")),
                ("internal_notes", models.TextField(blank=True, verbose_name="Notas internas")),
                ("customer_visible_notes", models.TextField(blank=True, verbose_name="Notas visibles al cliente")),
                ("received_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha de ingreso")),
                ("diagnosis_due_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Límite de diagnóstico")),
                ("promised_delivery_at", models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Entrega prometida")),
                ("ready_at", models.DateTimeField(blank=True, null=True, verbose_name="Listo en")),
                ("delivered_at", models.DateTimeField(blank=True, null=True, verbose_name="Entregado en")),
                ("cancelled_at", models.DateTimeField(blank=True, null=True, verbose_name="Cancelado en")),
                ("cancel_reason", models.TextField(blank=True, verbose_name="Motivo de cancelación")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Asignado a",
                        db_index=True,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_orders",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Creado por",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="work_orders",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="work_orders",
                        to="devices.device",
                        verbose_name="Equipo",
                    ),
                ),
                (
                    "related_order",
                    models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="related_orders",
                        to="workorders.workorder",
                        verbose_name="Orden relacionada",
                    ),
                ),
            ],
            options={
                "verbose_name": "Orden de trabajo",
                "verbose_name_plural": "Órdenes de trabajo",
                "ordering": ["-received_at"],
                "indexes": [
                    models.Index(fields=["status", "promised_delivery_at"], name="wo_status_delivery_idx"),
                    models.Index(fields=["customer", "created_at"], name="wo_customer_created_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="WorkOrderStatusHistory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "from_status",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("RECEIVED", "Recibido"), ("PENDING_DIAGNOSIS", "Pendiente de diagnóstico"),
                            ("IN_DIAGNOSIS", "En diagnóstico"), ("AWAITING_APPROVAL", "Esperando aprobación"),
                            ("APPROVED_FOR_REPAIR", "Aprobado para reparar"), ("REJECTED", "Presupuesto rechazado"),
                            ("WAITING_PART", "Esperando repuesto"), ("IN_REPAIR", "En reparación"),
                            ("IN_TESTING", "En pruebas"), ("READY_FOR_PICKUP", "Listo para retirar"),
                            ("DELIVERED", "Entregado"), ("UNREPAIRABLE", "Sin reparación posible"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        max_length=30,
                        verbose_name="Estado anterior",
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("RECEIVED", "Recibido"), ("PENDING_DIAGNOSIS", "Pendiente de diagnóstico"),
                            ("IN_DIAGNOSIS", "En diagnóstico"), ("AWAITING_APPROVAL", "Esperando aprobación"),
                            ("APPROVED_FOR_REPAIR", "Aprobado para reparar"), ("REJECTED", "Presupuesto rechazado"),
                            ("WAITING_PART", "Esperando repuesto"), ("IN_REPAIR", "En reparación"),
                            ("IN_TESTING", "En pruebas"), ("READY_FOR_PICKUP", "Listo para retirar"),
                            ("DELIVERED", "Entregado"), ("UNREPAIRABLE", "Sin reparación posible"),
                            ("CANCELLED", "Cancelado"),
                        ],
                        max_length=30,
                        verbose_name="Estado nuevo",
                    ),
                ),
                ("comment", models.TextField(blank=True, verbose_name="Comentario")),
                (
                    "source",
                    models.CharField(
                        choices=[("WEB", "Web"), ("API", "API"), ("TELEGRAM", "Telegram"), ("SYSTEM", "Sistema")],
                        default="WEB",
                        max_length=20,
                        verbose_name="Origen",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Actor",
                    ),
                ),
                (
                    "work_order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="workorders.workorder",
                        verbose_name="Orden de trabajo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Historial de estado",
                "verbose_name_plural": "Historial de estados",
                "ordering": ["created_at"],
            },
        ),
    ]
