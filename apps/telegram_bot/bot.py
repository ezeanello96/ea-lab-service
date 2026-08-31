# apps/telegram_bot/bot.py
"""
Handlers del bot de Telegram para PC Service Manager.

Todos los handlers son funciones async. El bot corre en un proceso separado
mediante: python manage.py runtelegrambot
"""
import logging
from datetime import timedelta

from django.utils import timezone
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _get_linked_account(telegram_user_id: int):
    """Retorna TelegramAccount si el usuario tiene una cuenta vinculada y activa."""
    from apps.accounts.models import TelegramAccount
    try:
        return TelegramAccount.objects.select_related("user").get(
            telegram_user_id=telegram_user_id,
            is_active=True,
        )
    except TelegramAccount.DoesNotExist:
        return None


def _touch_last_interaction(account) -> None:
    account.last_interaction_at = timezone.now()
    account.save(update_fields=["last_interaction_at"])


def _format_order_line(order) -> str:
    priority_icon = {"URGENT": "🔴", "HIGH": "🟠", "NORMAL": "🟡", "LOW": "⚪"}.get(order.priority, "•")
    return f"{priority_icon} *{order.number}* — {order.customer.full_name} — {order.get_status_display()}"


def _format_task_line(task) -> str:
    overdue_mark = " ⚠️" if task.is_overdue else ""
    due = task.due_at.strftime("%d/%m %H:%M") if task.due_at else "sin fecha"
    return f"• {task.title} ({due}){overdue_mark}"


async def _reply_not_linked(update: Update) -> None:
    await update.message.reply_text(
        "❌ Tu cuenta de Telegram no está vinculada al sistema.\n\n"
        "Pedile a un administrador que genere un código de vinculación y luego usá:\n"
        "`/vincular CODIGO`",
        parse_mode="Markdown",
    )

# ---------------------------------------------------------------------------
# Handlers de comandos
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — mensaje de bienvenida."""
    account = _get_linked_account(update.effective_user.id)
    if account:
        _touch_last_interaction(account)
        await update.message.reply_text(
            f"👋 Hola, {account.user.get_full_name() or account.user.username}!\n"
            "Usá /ayuda para ver los comandos disponibles."
        )
    else:
        await _reply_not_linked(update)


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ayuda — lista de comandos."""
    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)
    await update.message.reply_text(
        "*Comandos disponibles:*\n\n"
        "📋 *Órdenes*\n"
        "`/hoy` — órdenes y tareas de hoy\n"
        "`/manana` — órdenes y tareas de mañana\n"
        "`/pendientes` — órdenes activas\n"
        "`/listos` — equipos listos para retirar\n"
        "`/orden OT-2024-00001` — detalle de una orden\n"
        "`/buscar texto` — buscar órdenes y clientes\n\n"
        "✏️ *Acciones*\n"
        "`/nota OT-2024-00001 texto` — agregar nota a una orden\n"
        "`/completar ID` — marcar tarea como completada\n\n"
        "📊 *Informes*\n"
        "`/vencidos` — tareas vencidas\n"
        "`/resumen` — resumen del día\n\n"
        "🔔 *Notificaciones*\n"
        "`/silenciar [horas]` — silenciar notificaciones (default 8h)\n\n"
        "`/ayuda` — este mensaje",
        parse_mode="Markdown",
    )


async def cmd_vincular(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/vincular CODIGO — vincula la cuenta de Telegram con un usuario del sistema."""
    from apps.accounts.models import TelegramAccount, TelegramPairingCode
    from django.db import transaction

    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Uso: `/vincular CODIGO`\n"
            "El código de vinculación lo genera un administrador desde el sistema web.",
            parse_mode="Markdown",
        )
        return

    plain_code = args[0].strip().upper()
    pairing = TelegramPairingCode.verify(plain_code)

    if pairing is None:
        await update.message.reply_text(
            "❌ El código es inválido o ya venció. Solicitá un código nuevo al administrador."
        )
        return

    tg_user = update.effective_user

    try:
        with transaction.atomic():
            # Invalidar cuenta anterior si existe
            TelegramAccount.objects.filter(
                telegram_user_id=tg_user.id
            ).update(is_active=False)

            account, created = TelegramAccount.objects.update_or_create(
                user=pairing.user,
                defaults={
                    "telegram_user_id": tg_user.id,
                    "chat_id": update.effective_chat.id,
                    "username": tg_user.username or "",
                    "first_name": tg_user.first_name or "",
                    "last_name": tg_user.last_name or "",
                    "verified_at": timezone.now(),
                    "is_active": True,
                    "notifications_enabled": True,
                    "last_interaction_at": timezone.now(),
                },
            )
            pairing.used_at = timezone.now()
            pairing.save(update_fields=["used_at"])

        user_display = pairing.user.get_full_name() or pairing.user.username
        await update.message.reply_text(
            f"✅ ¡Cuenta vinculada correctamente!\n"
            f"Ahora sos *{user_display}* en el sistema.\n\n"
            "Usá /ayuda para ver los comandos disponibles.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.exception("Error vinculando cuenta Telegram: %s", exc)
        await update.message.reply_text(
            "❌ Ocurrió un error al vincular la cuenta. Contactá al administrador."
        )


async def cmd_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/hoy — órdenes activas y tareas vencidas hoy."""
    from apps.workorders.models import WorkOrder
    from apps.tasks.models import Task

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    orders = list(
        WorkOrder.objects.filter(
            status__in=WorkOrder.ACTIVE_STATUSES,
            assigned_to=account.user,
        ).select_related("customer").order_by("-priority", "received_at")[:10]
    )

    tasks_today = list(
        Task.objects.filter(
            due_at__gte=today_start,
            due_at__lt=tomorrow_start,
            status__in=Task.ACTIVE_STATUSES,
            assigned_to=account.user,
        ).order_by("due_at")[:10]
    )

    lines = [f"*📅 Hoy — {now.strftime('%d/%m/%Y')}*\n"]

    if orders:
        lines.append("*Mis órdenes activas:*")
        lines.extend(_format_order_line(o) for o in orders)
    else:
        lines.append("_No tenés órdenes activas asignadas._")

    if tasks_today:
        lines.append("\n*Tareas para hoy:*")
        lines.extend(_format_task_line(t) for t in tasks_today)

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_manana(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/manana — tareas para mañana."""
    from apps.tasks.models import Task

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    now = timezone.now()
    tomorrow_start = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    tasks = list(
        Task.objects.filter(
            due_at__gte=tomorrow_start,
            due_at__lt=tomorrow_end,
            status__in=Task.ACTIVE_STATUSES,
            assigned_to=account.user,
        ).order_by("due_at")[:15]
    )

    if tasks:
        lines = [f"*📅 Mañana — {tomorrow_start.strftime('%d/%m/%Y')}*\n",
                 "*Tareas:*"]
        lines.extend(_format_task_line(t) for t in tasks)
    else:
        lines = [f"*📅 Mañana — {tomorrow_start.strftime('%d/%m/%Y')}*",
                 "_No tenés tareas para mañana._"]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/pendientes — mis órdenes activas."""
    from apps.workorders.models import WorkOrder

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    orders = list(
        WorkOrder.objects.filter(
            status__in=WorkOrder.ACTIVE_STATUSES,
            assigned_to=account.user,
        ).select_related("customer").order_by("-priority", "received_at")[:15]
    )

    if orders:
        lines = [f"*📋 Mis órdenes activas ({len(orders)}):*\n"]
        lines.extend(_format_order_line(o) for o in orders)
    else:
        lines = ["*📋 Mis órdenes activas*", "_No tenés órdenes activas asignadas._"]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_listos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/listos — equipos listos para retirar."""
    from apps.workorders.models import WorkOrder

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    orders = list(
        WorkOrder.objects.filter(
            status=WorkOrder.Status.READY_FOR_PICKUP,
        ).select_related("customer", "device").order_by("ready_at")[:20]
    )

    if orders:
        lines = [f"*✅ Listos para retirar ({len(orders)}):*\n"]
        for o in orders:
            ready_str = o.ready_at.strftime("%d/%m") if o.ready_at else "—"
            lines.append(
                f"• *{o.number}* — {o.customer.full_name}\n"
                f"  {o.device.brand} {o.device.model} — desde {ready_str}"
            )
    else:
        lines = ["*✅ Listos para retirar*", "_No hay equipos esperando retiro._"]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_vencidos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/vencidos — tareas vencidas."""
    from apps.tasks.models import Task

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    overdue = list(
        Task.objects.filter(
            due_at__lt=timezone.now(),
            status__in=Task.ACTIVE_STATUSES,
            assigned_to=account.user,
        ).order_by("due_at")[:15]
    )

    if overdue:
        lines = [f"*⚠️ Tareas vencidas ({len(overdue)}):*\n"]
        lines.extend(_format_task_line(t) for t in overdue)
    else:
        lines = ["*⚠️ Tareas vencidas*", "_No tenés tareas vencidas. ¡Bien!_"]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_orden(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/orden OT-2024-00001 — detalle de una orden."""
    from apps.workorders.models import WorkOrder

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    if not context.args:
        await update.message.reply_text("Uso: `/orden OT-2024-00001`", parse_mode="Markdown")
        return

    number = context.args[0].strip().upper()
    try:
        order = WorkOrder.objects.select_related(
            "customer", "device", "assigned_to"
        ).get(number=number)
    except WorkOrder.DoesNotExist:
        await update.message.reply_text(f"❌ No se encontró la orden *{number}*.", parse_mode="Markdown")
        return

    assigned = order.assigned_to.get_full_name() if order.assigned_to else "Sin asignar"
    promised = order.promised_delivery_at.strftime("%d/%m/%Y") if order.promised_delivery_at else "—"

    text = (
        f"*{order.number}*\n"
        f"Estado: {order.get_status_display()}\n"
        f"Prioridad: {order.get_priority_display()}\n"
        f"Cliente: {order.customer.full_name}\n"
        f"Equipo: {order.device.brand} {order.device.model}\n"
        f"Técnico: {assigned}\n"
        f"Entrega est.: {promised}\n"
        f"Problema: {order.reported_issue[:200]}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/buscar texto — busca órdenes y clientes."""
    from apps.workorders.models import WorkOrder
    from apps.customers.models import Customer

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    if not context.args:
        await update.message.reply_text("Uso: `/buscar nombre o número`", parse_mode="Markdown")
        return

    query = " ".join(context.args).strip()

    from django.db.models import Q
    orders = list(
        WorkOrder.objects.filter(
            Q(number__icontains=query) | Q(customer__full_name__icontains=query)
        ).select_related("customer").filter(
            status__in=WorkOrder.ACTIVE_STATUSES
        )[:8]
    )

    customers = list(
        Customer.objects.filter(
            Q(full_name__icontains=query) | Q(phone_normalized__icontains=query),
            is_active=True,
        )[:5]
    )

    lines = [f"*🔍 Resultados para «{query}»:*\n"]

    if orders:
        lines.append("*Órdenes:*")
        lines.extend(_format_order_line(o) for o in orders)

    if customers:
        lines.append("\n*Clientes:*")
        for c in customers:
            lines.append(f"• {c.full_name} — {c.phone}")

    if not orders and not customers:
        lines.append("_Sin resultados._")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_nota(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/nota OT-2024-00001 texto — agrega una nota interna a una orden."""
    from apps.workorders.models import WorkOrder, WorkLog
    from django.db import transaction

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Uso: `/nota OT-2024-00001 El texto de la nota`",
            parse_mode="Markdown",
        )
        return

    number = args[0].strip().upper()
    note_text = " ".join(args[1:]).strip()

    try:
        order = WorkOrder.objects.get(number=number)
    except WorkOrder.DoesNotExist:
        await update.message.reply_text(f"❌ No se encontró la orden *{number}*.", parse_mode="Markdown")
        return

    with transaction.atomic():
        WorkLog.objects.create(
            work_order=order,
            entry_type=WorkLog.EntryType.NOTE,
            description=f"[Telegram] {note_text}",
            author=account.user,
            is_customer_visible=False,
        )

    await update.message.reply_text(
        f"✅ Nota agregada a *{number}*:\n_{note_text}_",
        parse_mode="Markdown",
    )


async def cmd_completar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/completar ID — marca una tarea como completada por su ID (primeros 8 chars del UUID)."""
    from apps.tasks.models import Task
    from apps.tasks.services import TaskService, TaskError

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    if not context.args:
        await update.message.reply_text("Uso: `/completar ID` (los primeros caracteres del ID de la tarea)", parse_mode="Markdown")
        return

    task_id_prefix = context.args[0].strip().lower()

    tasks = list(
        Task.objects.filter(
            assigned_to=account.user,
            status__in=Task.ACTIVE_STATUSES,
        ).filter(id__startswith=task_id_prefix)[:2]
    )

    if not tasks:
        await update.message.reply_text("❌ No se encontró la tarea. Verificá el ID con /vencidos o /hoy.")
        return

    if len(tasks) > 1:
        await update.message.reply_text("❌ El ID coincide con varias tareas. Usá más caracteres.")
        return

    task = tasks[0]
    try:
        TaskService.complete(task=task, actor=account.user)
        await update.message.reply_text(f"✅ Tarea completada: _{task.title}_", parse_mode="Markdown")
    except TaskError as e:
        await update.message.reply_text(f"❌ {e}")


async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/resumen — resumen del sistema."""
    from apps.workorders.models import WorkOrder
    from apps.tasks.services import TaskService

    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    now = timezone.now()
    active_orders = WorkOrder.objects.filter(status__in=WorkOrder.ACTIVE_STATUSES).count()
    ready = WorkOrder.objects.filter(status=WorkOrder.Status.READY_FOR_PICKUP).count()
    overdue_tasks = TaskService.get_overdue_count()

    text = (
        f"*📊 Resumen — {now.strftime('%d/%m/%Y %H:%M')}*\n\n"
        f"• Órdenes activas: *{active_orders}*\n"
        f"• Listos para retirar: *{ready}*\n"
        f"• Tareas vencidas: *{overdue_tasks}*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_silenciar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/silenciar [horas] — silencia notificaciones. Default: 8h."""
    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return
    _touch_last_interaction(account)

    hours = 8
    if context.args:
        try:
            hours = int(context.args[0])
            hours = max(1, min(hours, 168))  # 1h - 1 semana
        except ValueError:
            pass

    account.muted_until = timezone.now() + timedelta(hours=hours)
    account.save(update_fields=["muted_until"])

    await update.message.reply_text(
        f"🔕 Notificaciones silenciadas por *{hours}h*.\n"
        f"Se reanudan el {account.muted_until.strftime('%d/%m/%Y a las %H:%M')}.",
        parse_mode="Markdown",
    )


async def cmd_desvincular(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/desvincular — desvincula la cuenta de Telegram."""
    account = _get_linked_account(update.effective_user.id)
    if not account:
        await _reply_not_linked(update)
        return

    account.is_active = False
    account.save(update_fields=["is_active"])
    await update.message.reply_text(
        "✅ Cuenta desvinculada. Podés volver a vincularla cuando quieras con `/vincular CODIGO`.",
        parse_mode="Markdown",
    )


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde a comandos desconocidos."""
    await update.message.reply_text(
        "❓ Comando desconocido. Usá /ayuda para ver los comandos disponibles."
    )


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler global de errores del bot."""
    logger.exception("Error en handler del bot: %s", context.error, exc_info=context.error)
