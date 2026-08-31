#!/usr/bin/env sh
# restore.sh — Restaura un backup generado por backup.sh.
# Uso: bash scripts/restore.sh /ruta/al/pcservice-backup-YYYYMMDD-HHMMSS.tar.gz
#
# ADVERTENCIA: Este script elimina y recrea la base de datos de destino.
# Usarlo solo en desarrollo o con extremo cuidado en producción.

set -e

BACKUP_FILE="$1"

if [ -z "${BACKUP_FILE}" ]; then
  echo "Uso: bash scripts/restore.sh <archivo_backup.tar.gz>"
  exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
  echo "[restore] ERROR: El archivo '${BACKUP_FILE}' no existe."
  exit 1
fi

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-pcservice}"
DB_NAME="${POSTGRES_DB:-pcservice}"
PGPASSWORD="${POSTGRES_PASSWORD:-changeme}"
MEDIA_ROOT="${MEDIA_ROOT:-/app/media}"

TMP_DIR="/tmp/pcservice-restore-$$"

echo "[restore] Iniciando restauración desde: ${BACKUP_FILE}"
echo "[restore] Base de datos destino: ${DB_NAME} en ${DB_HOST}:${DB_PORT}"

# Confirmar si es interactivo
if [ -t 0 ]; then
  printf "[restore] ¿Continuar? Esto eliminará los datos actuales. [s/N] "
  read -r confirm
  case "$confirm" in
    s|S|y|Y) ;;
    *) echo "[restore] Operación cancelada."; exit 0 ;;
  esac
fi

# Extraer backup
mkdir -p "${TMP_DIR}"
echo "[restore] Extrayendo archivo..."
tar -xzf "${BACKUP_FILE}" -C "${TMP_DIR}" --strip-components=1

# Restaurar base de datos
export PGPASSWORD
echo "[restore] Restaurando base de datos..."
pg_restore \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  --clean \
  --if-exists \
  "${TMP_DIR}/db.dump"

# Restaurar media
if [ -d "${TMP_DIR}/media" ]; then
  echo "[restore] Restaurando archivos media en ${MEDIA_ROOT}..."
  rm -rf "${MEDIA_ROOT}"
  cp -r "${TMP_DIR}/media" "${MEDIA_ROOT}"
fi

# Limpiar temporales
rm -rf "${TMP_DIR}"

echo "[restore] Restauración completada exitosamente."
