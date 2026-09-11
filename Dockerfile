FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl postgresql-client \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libglib2.0-0 \
    libharfbuzz0b libffi8 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

# Descargar HTMX si no está incluido en el repositorio
RUN mkdir -p /app/static/vendor && \
    [ -f /app/static/vendor/htmx.min.js ] || \
    curl -fsSL -o /app/static/vendor/htmx.min.js \
      https://unpkg.com/htmx.org@2/dist/htmx.min.js || \
    echo "Advertencia: no se pudo descargar htmx.min.js (sin conectividad)"

RUN python -m django collectstatic --noinput --settings=config.settings.local 2>/dev/null || true

EXPOSE 8000

CMD ["python", "-m", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
