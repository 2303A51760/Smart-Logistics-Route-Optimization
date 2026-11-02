#!/usr/bin/env bash
# ==============================================================================
# Smart Logistics Platform — PostgreSQL Database Backup Script
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_HOST="${POSTGRES_SERVER:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-smart_logistics}"
BACKUP_FILE="${BACKUP_DIR}/smart_logistics_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "============================================================"
echo "Starting Database Backup for: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"
echo "Destination: ${BACKUP_FILE}"
echo "============================================================"

# Execute pg_dump with gzip compression
PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -F c -b -v | gzip > "${BACKUP_FILE}"

echo "[SUCCESS] Backup created successfully: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"
