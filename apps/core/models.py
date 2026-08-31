"""Modelos globales del negocio."""
import uuid

from django.db import models


class BusinessSettings(models.Model):
    """
    Configuración global del negocio. Solo debe existir UN registro.
    Se accede mediante BusinessSettings.get_settings().
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business_name = models.CharField(max_length=200, verbose_name="Nombre del negocio")
    legal_name = models.CharField(
        max_length=200, blank=True, verbose_name="Razón social"
    )
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Dirección")
    currency_code = models.CharField(
        max_length=3,
        default="ARS",
        verbose_name="Código de moneda",
    )
    timezone = models.CharField(
        max_length=50,
        default="America/Argentina/Cordoba",
        verbose_name="Zona horaria",
    )
    order_prefix = models.CharField(
        max_length=10,
        default="OT",
        verbose_name="Prefijo de órdenes",
        help_text='Por ejemplo: "OT" generará OT-0001, OT-0002...',
    )
    default_warranty_days = models.PositiveIntegerField(
        default=30,
        verbose_name="Días de garantía por defecto",
    )
    default_diagnosis_hours = models.PositiveIntegerField(
        default=48,
        verbose_name="Horas de diagnóstico por defecto",
    )
    quiet_hours_start = models.TimeField(
        default="21:00",
        verbose_name="Inicio de horario de silencio",
        help_text="No se envían notificaciones fuera del horario activo.",
    )
    quiet_hours_end = models.TimeField(
        default="08:00",
        verbose_name="Fin de horario de silencio",
    )
    morning_digest_time = models.TimeField(
        default="08:00",
        verbose_name="Hora del resumen matutino",
    )
    evening_digest_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora del resumen vespertino",
        help_text="Dejar vacío para deshabilitar el resumen vespertino.",
    )
    warranty_terms = models.TextField(
        blank=True,
        verbose_name="Términos de garantía",
        help_text="Se imprime en los comprobantes de entrega.",
    )
    quote_terms = models.TextField(
        blank=True,
        verbose_name="Términos de presupuesto",
        help_text="Se imprime al pie de los presupuestos.",
    )
    receipt_terms = models.TextField(
        blank=True,
        verbose_name="Términos del recibo",
        help_text="Se imprime al pie de los recibos de pago.",
    )
    google_oauth_token = models.TextField(
        blank=True,
        verbose_name="Token OAuth de Google Calendar",
        help_text="JSON con access_token y refresh_token. Se gestiona automáticamente.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")

    class Meta:
        verbose_name = "Configuración del negocio"
        verbose_name_plural = "Configuración del negocio"

    def __str__(self):
        return self.business_name or "Configuración del negocio"

    @classmethod
    def get_settings(cls):
        """
        Retorna el único registro de configuración, creándolo si no existe.
        Usar este método en lugar de .objects.first() para garantizar que siempre haya datos.
        """
        instance, _ = cls.objects.get_or_create(
            pk=cls.objects.values_list("pk", flat=True).first()
            or uuid.uuid4(),
            defaults={"business_name": "Mi Servicio Técnico"},
        )
        return instance
