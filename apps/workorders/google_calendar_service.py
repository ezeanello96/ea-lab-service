"""Servicio de integración con Google Calendar.

Requisitos previos:
  1. En Google Cloud Console: crear proyecto, habilitar Calendar API, crear
     credenciales OAuth 2.0 (tipo "aplicación web"), añadir URI de redirección
     (p.ej. http://localhost:8000/ordenes/google-oauth/callback/).
  2. Variables de entorno necesarias:
       GOOGLE_CLIENT_ID=<tu_client_id>
       GOOGLE_CLIENT_SECRET=<tu_client_secret>
       GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/ordenes/google-oauth/callback/
       GOOGLE_CALENDAR_ID=primary   # o el ID específico del calendario
  3. El primer usuario admin debe completar el flujo OAuth vía /ordenes/google-oauth/.
     El token se guarda en la tabla core.BusinessSettings como JSON.
  4. pip install google-auth google-auth-oauthlib google-api-python-client

Dependencias (agregar a pyproject.toml):
  google-auth>=2.29
  google-auth-oauthlib>=1.2
  google-api-python-client>=2.130
"""
from __future__ import annotations

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

_GOOGLE_CLIENT_ID     = getattr(settings, "GOOGLE_CLIENT_ID", "")
_GOOGLE_CLIENT_SECRET = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
_REDIRECT_URI         = getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", "")
_CALENDAR_ID          = getattr(settings, "GOOGLE_CALENDAR_ID", "primary")


def _is_configured() -> bool:
    return bool(_GOOGLE_CLIENT_ID and _GOOGLE_CLIENT_SECRET and _REDIRECT_URI)


def _load_credentials():
    """Lee el token OAuth almacenado en BusinessSettings."""
    if not _is_configured():
        return None
    try:
        from google.oauth2.credentials import Credentials  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
        from apps.core.models import BusinessSettings

        settings_obj = BusinessSettings.objects.first()
        if not settings_obj or not getattr(settings_obj, "google_oauth_token", None):
            return None

        token_data = json.loads(settings_obj.google_oauth_token)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=_GOOGLE_CLIENT_ID,
            client_secret=_GOOGLE_CLIENT_SECRET,
            scopes=SCOPES,
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_credentials(creds)
        return creds
    except Exception as exc:
        logger.error("Error cargando credenciales de Google Calendar: %s", exc)
        return None


def _save_credentials(creds) -> None:
    try:
        from apps.core.models import BusinessSettings
        settings_obj = BusinessSettings.objects.first()
        if settings_obj:
            token_data = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
            }
            settings_obj.google_oauth_token = json.dumps(token_data)
            settings_obj.save(update_fields=["google_oauth_token"])
    except Exception as exc:
        logger.error("Error guardando credenciales de Google Calendar: %s", exc)


def _build_service(creds):
    from googleapiclient.discovery import build  # type: ignore
    return build("calendar", "v3", credentials=creds)


def get_oauth_authorization_url() -> str:
    """Retorna la URL para iniciar el flujo OAuth 2.0."""
    if not _is_configured():
        raise RuntimeError("Google Calendar no está configurado. Verificá GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET.")
    from google_auth_oauthlib.flow import Flow  # type: ignore
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": _GOOGLE_CLIENT_ID,
                "client_secret": _GOOGLE_CLIENT_SECRET,
                "redirect_uris": [_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return auth_url


def exchange_code_for_token(code: str) -> None:
    """Intercambia el código OAuth por un token y lo persiste."""
    from google_auth_oauthlib.flow import Flow  # type: ignore
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": _GOOGLE_CLIENT_ID,
                "client_secret": _GOOGLE_CLIENT_SECRET,
                "redirect_uris": [_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    _save_credentials(flow.credentials)


def create_event(order) -> tuple[str, str] | None:
    """Crea un evento en Google Calendar y retorna (event_id, html_link) o None."""
    creds = _load_credentials()
    if not creds:
        return None
    try:
        service = _build_service(creds)
        start_dt = order.promised_delivery_at or order.received_at

        import datetime
        if not isinstance(start_dt, datetime.datetime):
            import datetime as dt
            start_dt = dt.datetime.combine(start_dt, dt.time(10, 0))
        end_dt = start_dt + datetime.timedelta(hours=1)

        event_body = {
            "summary": f"[OT] {order.number} — {order.customer.full_name}",
            "description": (
                f"Orden: {order.number}\n"
                f"Cliente: {order.customer.full_name}\n"
                f"Equipo: {order.device}\n"
                f"Problema: {order.reported_issue[:200]}\n"
                f"Estado: {order.get_status_display()}"
            ),
            "start": {"dateTime": start_dt.isoformat(), "timeZone": settings.TIME_ZONE},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": settings.TIME_ZONE},
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 60}],
            },
        }
        created = service.events().insert(calendarId=_CALENDAR_ID, body=event_body).execute()
        return created.get("id", ""), created.get("htmlLink", "")
    except Exception as exc:
        logger.error("Error creando evento en Google Calendar para orden %s: %s", order.number, exc)
        return None


def update_event(order) -> bool:
    """Actualiza el evento vinculado a la orden en Google Calendar."""
    if not order.google_calendar_event_id:
        return False
    creds = _load_credentials()
    if not creds:
        return False
    try:
        service = _build_service(creds)
        start_dt = order.promised_delivery_at or order.received_at
        import datetime
        if not isinstance(start_dt, datetime.datetime):
            import datetime as dt
            start_dt = dt.datetime.combine(start_dt, dt.time(10, 0))
        end_dt = start_dt + datetime.timedelta(hours=1)

        event_body = {
            "summary": f"[OT] {order.number} — {order.customer.full_name}",
            "description": (
                f"Orden: {order.number}\n"
                f"Cliente: {order.customer.full_name}\n"
                f"Equipo: {order.device}\n"
                f"Problema: {order.reported_issue[:200]}\n"
                f"Estado: {order.get_status_display()}"
            ),
            "start": {"dateTime": start_dt.isoformat(), "timeZone": settings.TIME_ZONE},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": settings.TIME_ZONE},
        }
        service.events().update(
            calendarId=_CALENDAR_ID,
            eventId=order.google_calendar_event_id,
            body=event_body,
        ).execute()
        return True
    except Exception as exc:
        logger.error("Error actualizando evento Calendar %s para orden %s: %s",
                     order.google_calendar_event_id, order.number, exc)
        return False


def delete_event(order) -> bool:
    """Elimina el evento de Google Calendar vinculado a la orden."""
    if not order.google_calendar_event_id:
        return False
    creds = _load_credentials()
    if not creds:
        return False
    try:
        service = _build_service(creds)
        service.events().delete(
            calendarId=_CALENDAR_ID,
            eventId=order.google_calendar_event_id,
        ).execute()
        return True
    except Exception as exc:
        logger.error("Error eliminando evento Calendar %s: %s", order.google_calendar_event_id, exc)
        return False
