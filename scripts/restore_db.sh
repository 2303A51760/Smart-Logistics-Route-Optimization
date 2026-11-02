#!/usr/bin/env bash
# ==============================================================================
# Smart Logistics Platform — PostgreSQL Database Restore Script
# ==============================================================================
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-backup-file.sql.gz | path-to-backup-file.sql>"
    exit 1
fi

BACKUP_FILE="$1"
DB_HOST="${POSTGRES_SERVER:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_NAME="${POSTGRES_DB:-smart_logistics}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "[ERROR] Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "============================================================"
echo "Starting Database Restore to: ${DB_NAME} on ${DB_HOST}:${DB_PORT}"
echo "Source File: ${BACKUP_FILE}"
echo "============================================================"

if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists -v
else
    PGPASSWORD="${POSTGRES_PASSWORD:-postgres}" pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists -v "${BACKUP_FILE}"
fi

echo "[SUCCESS] Database restoration complete."
