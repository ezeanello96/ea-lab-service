# Guía de operación

Referencia rápida para el día a día del sistema.

---

## Iniciar el sistema

```bash
# Primer uso: copiar el archivo de entorno y personalizarlo
cp .env.example .env
# Editar .env con las credenciales reales antes de continuar

# Construir imágenes
make build

# Iniciar todos los servicios en background
make up

# Ver el estado
make status

# Crear el superusuario inicial
make createsuperuser
```

Acceder a `http://localhost:8000` y al admin en `http://localhost:8000/admin/`.

---

## Detener y reiniciar

```bash
make down        # Detener todos los servicios
make restart     # Reiniciar todos los servicios
make logs        # Seguir logs del servidor web
```

---

## Migraciones

```bash
# Aplicar migraciones pendientes
make migrate

# Crear nuevas migraciones (tras modificar modelos)
docker compose exec web python manage.py makemigrations
make migrate
```

---

## Shell Django

```bash
make shell
# Equivalente a: docker compose exec web python manage.py shell
```

---

## Ejecutar tests

```bash
make test
# Con cobertura:
docker compose exec web pytest tests/ --cov=apps --cov-report=term-missing
```

---

## Linting y formato

```bash
make lint          # ruff check .
make format-check  # ruff format --check .

# Aplicar formato automáticamente:
docker compose exec web ruff format .
```

---

## Verificar configuración Django

```bash
make check
# Equivalente a: python manage.py check
```

---

## Bot de Telegram (opcional)

```bash
# Iniciar el bot (requiere TELEGRAM_ENABLED=1 y TELEGRAM_BOT_TOKEN en .env)
docker compose --profile telegram up -d bot

# Ver logs del bot
make logs-bot
```

---

## Monitoreo

- Estado de servicios: `make status`
- Health check: `curl http://localhost:8000/health/`
- Logs de worker Celery: `docker compose logs -f worker`
- Logs de Celery Beat: `docker compose logs -f beat`
