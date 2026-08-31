# Backup y restauración

## Crear un backup

```bash
make backup
# Equivalente a: docker compose exec web bash /app/scripts/backup.sh
```

El backup se guarda en `BACKUP_DIR` (por defecto `/app/backups/` dentro del contenedor).
El archivo se llama `pcservice-backup-YYYYMMDD-HHMMSS.tar.gz` y contiene:
- `db.dump`: dump completo de PostgreSQL en formato custom (`pg_dump -F c`)
- `media/`: copia del directorio de archivos subidos por usuarios

### Copiar el backup al host

```bash
docker compose exec web ls /app/backups/
docker cp $(docker compose ps -q web):/app/backups/pcservice-backup-YYYYMMDD-HHMMSS.tar.gz ./backups/
```

---

## Restaurar un backup

**Advertencia**: La restauración elimina y reemplaza los datos actuales.

```bash
# Copiar el archivo de backup al contenedor
docker cp ./backups/pcservice-backup-YYYYMMDD-HHMMSS.tar.gz \
  $(docker compose ps -q web):/tmp/

# Ejecutar la restauración
docker compose exec web bash /app/scripts/restore.sh \
  /tmp/pcservice-backup-YYYYMMDD-HHMMSS.tar.gz
```

---

## Backup manual de la base de datos

```bash
docker compose exec db pg_dump \
  -U pcservice \
  -F c \
  -f /tmp/manual_backup.dump \
  pcservice

docker cp $(docker compose ps -q db):/tmp/manual_backup.dump ./
```

---

## Restauración manual de la base de datos

```bash
docker cp ./manual_backup.dump $(docker compose ps -q db):/tmp/

docker compose exec db pg_restore \
  -U pcservice \
  -d pcservice \
  --clean \
  --if-exists \
  /tmp/manual_backup.dump
```

---

## Recomendaciones

- Realizar backups diarios automatizados con cron del host.
- Guardar copias offsite (Google Drive, S3, etc.) en proyectos productivos.
- Verificar periódicamente que los backups se pueden restaurar correctamente.
- El volumen `postgres_data` de Docker NO es un sustituto del backup.
