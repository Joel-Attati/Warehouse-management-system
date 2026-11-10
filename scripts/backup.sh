#!/usr/bin/env bash
# =============================================================
# WMS PostgreSQL Backup Script
# Usage: ./scripts/backup.sh
# Recommended: run via cron daily
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$ROOT_DIR/.env" ]; then
  export $(grep -v '^#' "$ROOT_DIR/.env" | xargs)
fi

BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/wms_db_$TIMESTAMP.sql.gz"
UPLOADS_BACKUP="$BACKUP_DIR/wms_uploads_$TIMESTAMP.tar.gz"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting WMS backup..."

# ── Database backup ─────────────────────────────────────────
echo "[$(date)] Dumping PostgreSQL database..."
docker exec wms_db pg_dump \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean --if-exists \
  | gzip > "$BACKUP_FILE"

echo "[$(date)] Database backup saved to: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# ── Uploads backup ──────────────────────────────────────────
echo "[$(date)] Backing up uploaded files..."
docker run --rm \
  --volumes-from wms_backend \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/wms_uploads_$TIMESTAMP.tar.gz" /app/uploads

echo "[$(date)] Uploads backup saved to: $UPLOADS_BACKUP"

# ── Cleanup old backups ─────────────────────────────────────
echo "[$(date)] Removing backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "wms_db_*.sql.gz" -mtime "+$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name "wms_uploads_*.tar.gz" -mtime "+$RETENTION_DAYS" -delete

echo "[$(date)] Backup complete."

