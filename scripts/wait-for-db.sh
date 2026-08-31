#!/usr/bin/env sh
# wait-for-db.sh — Espera hasta que PostgreSQL esté disponible.
# Uso: bash scripts/wait-for-db.sh

set -e

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-pcservice}"
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "[wait-for-db] Esperando a que PostgreSQL esté disponible en ${DB_HOST}:${DB_PORT}..."

retries=0
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -q 2>/dev/null; do
  retries=$((retries + 1))
  if [ "$retries" -ge "$MAX_RETRIES" ]; then
    echo "[wait-for-db] ERROR: PostgreSQL no respondió después de ${MAX_RETRIES} intentos."
    exit 1
  fi
  echo "[wait-for-db] Intento ${retries}/${MAX_RETRIES}. Reintentando en ${RETRY_INTERVAL}s..."
  sleep "${RETRY_INTERVAL}"
done

echo "[wait-for-db] PostgreSQL disponible. Continuando..."
