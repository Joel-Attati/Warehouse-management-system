#!/usr/bin/env bash
# =============================================================
# WMS SSL Certificate Generator (self-signed, for internal LAN)
# Usage: ./scripts/gen-ssl.sh [hostname]
# Example: ./scripts/gen-ssl.sh wms.local
# =============================================================

set -euo pipefail

HOSTNAME="${1:-wms.local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSL_DIR="$(dirname "$SCRIPT_DIR")/nginx/ssl"

mkdir -p "$SSL_DIR"

echo "Generating self-signed certificate for: $HOSTNAME"

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout "$SSL_DIR/wms.key" \
  -out "$SSL_DIR/wms.crt" \
  -subj "/C=US/ST=Local/L=Local/O=Warehouse/CN=$HOSTNAME" \
  -addext "subjectAltName=DNS:$HOSTNAME,DNS:localhost,IP:127.0.0.1"

echo "Certificate generated:"
echo "  Key:  $SSL_DIR/wms.key"
echo "  Cert: $SSL_DIR/wms.crt"
echo ""
echo "To enable HTTPS, uncomment the HTTPS server block in nginx/nginx.conf"
echo "and set server_name to: $HOSTNAME"
echo ""
echo "Import $SSL_DIR/wms.crt into your OS/browser trust store on each client device."

