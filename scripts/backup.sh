#!/usr/bin/env sh
# backup.sh — Crea un backup de la base de datos y del directorio media/.
# Genera: pcservice-backup-YYYYMMDD-HHMMSS.tar.gz
# Uso: bash scripts/backup.sh

set -e

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
BACKUP_NAME="pcservice-backup-${TIMESTAMP}"
TMP_DIR="/tmp/${BACKUP_NAME}"
FINAL_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-pcservice}"
DB_NAME="${POSTGRES_DB:-pcservice}"
PGPASSWORD="${POSTGRES_PASSWORD:-changeme}"

echo "[backup] Iniciando backup: ${BACKUP_NAME}"

# Crear directorios temporales
mkdir -p "${TMP_DIR}"
mkdir -p "${BACKUP_DIR}"

# 1. Dump de la base de datos
echo "[backup] Volcando base de datos ${DB_NAME}..."
export PGPASSWORD
pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -F c \
  -f "${TMP_DIR}/db.dump" \
  "${DB_NAME}"

echo "[backup] Dump completado: ${TMP_DIR}/db.dump"

# 2. Copia del directorio media/
MEDIA_ROOT="${MEDIA_ROOT:-/app/media}"
if [ -d "${MEDIA_ROOT}" ]; then
  echo "[backup] Copiando archivos media de ${MEDIA_ROOT}..."
  cp -r "${MEDIA_ROOT}" "${TMP_DIR}/media"
else
  echo "[backup] Directorio media no encontrado (${MEDIA_ROOT}), continuando sin él."
  mkdir -p "${TMP_DIR}/media"
fi

# 3. Crear el archivo tar.gz
echo "[backup] Comprimiendo en ${FINAL_FILE}..."
tar -czf "${FINAL_FILE}" -C "/tmp" "${BACKUP_NAME}"

# 4. Limpiar temporales
rm -rf "${TMP_DIR}"

echo "[backup] Backup completado exitosamente: ${FINAL_FILE}"
echo "[backup] Tamaño: $(du -sh "${FINAL_FILE}" | cut -f1)"
