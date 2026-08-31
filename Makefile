.PHONY: help build up down restart logs logs-bot shell migrate createsuperuser seed-demo test lint format-check check backup status

help:
	@echo "Comandos disponibles:"
	@echo "  make build           Construir imágenes Docker"
	@echo "  make up              Iniciar servicios"
	@echo "  make down            Detener servicios"
	@echo "  make restart         Reiniciar servicios"
	@echo "  make logs            Ver logs del servicio web"
	@echo "  make logs-bot        Ver logs del bot de Telegram"
	@echo "  make shell           Shell Django (manage.py shell)"
	@echo "  make migrate         Ejecutar migraciones"
	@echo "  make createsuperuser Crear superusuario"
	@echo "  make seed-demo       Cargar datos de demostración"
	@echo "  make test            Ejecutar suite de pruebas"
	@echo "  make lint            Verificar código con ruff"
	@echo "  make format-check    Verificar formato con ruff"
	@echo "  make check           Verificar configuración Django"
	@echo "  make backup          Crear copia de seguridad"
	@echo "  make status          Estado de los servicios"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f web

logs-bot:
	docker compose --profile telegram logs -f bot

shell:
	docker compose exec web python manage.py shell

migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

seed-demo:
	docker compose exec web python manage.py seed_demo

test:
	docker compose exec web pytest tests/

lint:
	docker compose exec web ruff check .

format-check:
	docker compose exec web ruff format --check .

check:
	docker compose exec web python manage.py check

backup:
	docker compose exec web bash /app/scripts/backup.sh

status:
	docker compose ps
