"""URLs de la app de tareas."""
from django.urls import path

from . import views

urlpatterns = [
    path("tareas/", views.TaskListView.as_view(), name="task-list"),
    path("tareas/nueva/", views.TaskCreateView.as_view(), name="task-create"),
    path("tareas/<uuid:pk>/editar/", views.TaskUpdateView.as_view(), name="task-update"),
    path("tareas/<uuid:pk>/completar/", views.TaskCompleteView.as_view(), name="task-complete"),
    path("tareas/<uuid:pk>/cancelar/", views.TaskCancelView.as_view(), name="task-cancel"),
    path("tareas/<uuid:pk>/posponer/", views.TaskSnoozeView.as_view(), name="task-snooze"),
]
