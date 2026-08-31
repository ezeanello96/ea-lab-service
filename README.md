# PC Service Manager

Sistema de gestión para servicio técnico de PCs. Construido con Django 5 + HTMX + PostgreSQL + Redis + Celery.

## Stack

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12, Django 5.x |
| Base de datos | PostgreSQL 16 |
| Caché / broker | Redis 7 |
| Tareas asíncronas | Celery 5 + Celery Beat |
| Frontend | Django Templates + HTMX |
| Contenedores | Docker Compose |
| Linter | Ruff |
| Tests | pytest + pytest-django |

---

## Requisitos

- Docker Desktop (o Docker Engine + Docker Compose v2)
- Git
- `make` (opcional pero recomendado)

---

## Instalación desde cero

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd pc-service-manager
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` y cambiá al menos:
- `DJANGO_SECRET_KEY` → generá uno con `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `POSTGRES_PASSWORD`
- `DATABASE_URL` (actualizá la contraseña)

### 3. Descargar HTMX (archivo estático local)

```bash
curl -Lo static/vendor/htmx.min.js https://unpkg.com/htmx.org@2/dist/htmx.min.js
```

### 4. Construir e iniciar

```bash
make build
make up
```

O sin make:
```bash
docker compose build
docker compose up -d
```

### 5. Crear superusuario

```bash
make createsuperuser
```

O sin make:
```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Acceder

- Aplicación: http://localhost:8000
- Admin: http://localhost:8000/admin/
- API docs: http://localhost:8000/api/v1/docs/
- Health check: http://localhost:8000/health/

---

## Comandos frecuentes

```bash
make up              # Iniciar servicios
make down            # Detener servicios
make logs            # Ver logs del servidor web
make migrate         # Aplicar migraciones
make shell           # Django shell
make test            # Ejecutar tests
make lint            # Verificar código con ruff
make backup          # Crear backup de BD + media
make status          # Estado de los contenedores
```

---

## Estructura del proyecto

```
pc-service-manager/
  config/              # Settings, URLs, Celery, WSGI/ASGI
  apps/
    accounts/          # Usuarios, perfiles, Telegram pairing
    core/              # BusinessSettings, dashboard, health check
    customers/         # Clientes
    devices/           # Equipos de clientes
    workorders/        # Órdenes de trabajo
    quotes/            # Presupuestos
    tasks/             # Tareas internas
    payments/          # Cobros y pagos
    notifications/     # Notificaciones (Telegram, internas)
    telegram_bot/      # Bot de Telegram
    audit/             # Log de auditoría
    reports/           # Reportes y estadísticas
  templates/           # HTML (Django Templates)
  static/              # CSS, JS, vendor (HTMX)
  scripts/             # backup.sh, restore.sh, wait-for-db.sh
  docs/                # Documentación adicional
  tests/               # Suite de pruebas pytest
```

---

## Documentación adicional

- [Decisiones técnicas](docs/DECISIONES.md)
- [Guía de operación](docs/OPERACION.md)
- [Backup y restauración](docs/BACKUP_RESTORE.md)
- [Bot de Telegram](docs/TELEGRAM.md)

---

## Desarrollo local sin Docker

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Necesitás PostgreSQL y Redis corriendo localmente
# Ajustá POSTGRES_HOST=localhost y REDIS_URL=redis://localhost:6379/0 en .env

export DJANGO_SETTINGS_MODULE=config.settings.local
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## Licencia

Uso privado — todos los derechos reservados.
