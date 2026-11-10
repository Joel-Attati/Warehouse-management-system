#!/usr/bin/env bash
# =============================================================
# WMS Database Restore Script
# Usage: ./scripts/restore.sh <backup_file.sql.gz>
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$ROOT_DIR/.env" ]; then
  export $(grep -v '^#' "$ROOT_DIR/.env" | xargs)
fi

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <path-to-backup.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "WARNING: This will overwrite the current database '$POSTGRES_DB'."
echo "Backup file: $BACKUP_FILE"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Restore cancelled."
  exit 0
fi

echo "[$(date)] Restoring database from: $BACKUP_FILE"

gunzip -c "$BACKUP_FILE" | docker exec -i wms_db psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB"

echo "[$(date)] Restore complete."

