"""Vistas para la gestión de tareas."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .forms import TaskForm
from .models import Task
from .services import TaskError, TaskService


class TaskListView(LoginRequiredMixin, View):
    """Panel de tareas dividido en: vencidas / hoy / mañana / próximas / sin fecha."""

    template_name = "tasks/task_list.html"

    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        tomorrow_end = tomorrow_start + timedelta(days=1)

        base_qs = (
            Task.objects.filter(status__in=Task.ACTIVE_STATUSES)
            .select_related("assigned_to", "work_order", "customer")
            .order_by("due_at", "-priority")
        )

        overdue = list(base_qs.filter(due_at__lt=today_start))
        today = list(base_qs.filter(due_at__gte=today_start, due_at__lt=tomorrow_start))
        tomorrow = list(base_qs.filter(due_at__gte=tomorrow_start, due_at__lt=tomorrow_end))
        upcoming = list(base_qs.filter(due_at__gte=tomorrow_end)[:20])
        no_date = list(base_qs.filter(due_at__isnull=True).order_by("-priority")[:20])

        snooze_options = [(1, "1 hora"), (4, "4 horas"), (24, "1 día"), (48, "2 días"), (168, "1 semana")]
        return render(request, self.template_name, {
            "page_title": "Tareas",
            "overdue": overdue,
            "today": today,
            "tomorrow": tomorrow,
            "upcoming": upcoming,
            "no_date": no_date,
            "snooze_options": snooze_options,
        })


class TaskCreateView(LoginRequiredMixin, View):
    template_name = "tasks/task_form.html"

    def get(self, request):
        form = TaskForm()
        return render(request, self.template_name, {"form": form, "page_title": "Nueva tarea"})

    def post(self, request):
        form = TaskForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            TaskService.create_task(
                title=data["title"],
                description=data.get("description", ""),
                priority=data.get("priority", Task.Priority.NORMAL),
                due_at=data.get("due_at"),
                work_order=data.get("work_order"),
                customer=data.get("customer"),
                device=data.get("device"),
                assigned_to=data.get("assigned_to"),
                created_by=request.user,
                recurrence_rule=data.get("recurrence_rule", ""),
            )
            messages.success(request, "Tarea creada correctamente.")
            return redirect("task-list")
        return render(request, self.template_name, {"form": form, "page_title": "Nueva tarea"})


class TaskUpdateView(LoginRequiredMixin, View):
    template_name = "tasks/task_form.html"

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = TaskForm(instance=task)
        return render(request, self.template_name, {
            "form": form,
            "task": task,
            "page_title": f"Editar tarea — {task.title}",
        })

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarea actualizada.")
            return redirect("task-list")
        return render(request, self.template_name, {
            "form": form,
            "task": task,
            "page_title": f"Editar tarea — {task.title}",
        })


class TaskCompleteView(LoginRequiredMixin, View):
    """POST: marca una tarea como completada."""

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        try:
            TaskService.complete(task=task, actor=request.user)
            messages.success(request, f"Tarea «{task.title}» completada.")
        except TaskError as e:
            messages.error(request, str(e))
        return redirect("task-list")


class TaskCancelView(LoginRequiredMixin, View):
    """POST: cancela una tarea."""

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        try:
            TaskService.cancel(task=task, actor=request.user)
            messages.success(request, f"Tarea «{task.title}» cancelada.")
        except TaskError as e:
            messages.error(request, str(e))
        return redirect("task-list")


class TaskSnoozeView(LoginRequiredMixin, View):
    """POST: pospone una tarea. Parámetro POST: hours (int, default 24)."""

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        try:
            hours = int(request.POST.get("hours", 24))
            if hours not in (1, 4, 24, 48, 168):
                hours = 24
            until = timezone.now() + timedelta(hours=hours)
            TaskService.snooze(task=task, actor=request.user, until=until)
            messages.success(request, f"Tarea pospuesta {hours}h.")
        except (TaskError, ValueError) as e:
            messages.error(request, str(e))
        return redirect("task-list")
