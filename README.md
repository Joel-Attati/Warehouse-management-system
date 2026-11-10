# Warehouse Management System

A full-stack, local/on-premises Warehouse Management System built with Next.js, FastAPI, PostgreSQL, and Redis — deployed via Docker Compose.

## Quick Start

### 1. Prerequisites

- Docker Engine ≥ 24 and Docker Compose v2
- Git

### 2. Clone and configure

```bash
git clone <repo-url> wms
cd wms
cp .env.example .env
```

Edit `.env` and change **all** default passwords and the `SECRET_KEY`.

### 3. Start the system

```bash
docker compose up -d
```

On first start:
- PostgreSQL and Redis containers initialize
- The backend runs Alembic migrations automatically
- A first admin user is created from `FIRST_ADMIN_*` env vars

### 4. Access the application

Open your browser and go to: **http://\<server-ip\>** (or `http://localhost` if running locally)

Log in with the credentials from your `.env` file.

---

## Architecture

```
Client Devices → Nginx (:80/:443) → Next.js Frontend (:3000)
                                  → FastAPI Backend  (:8000)
                                      → PostgreSQL   (:5432, internal only)
                                      → Redis        (:6379, internal only)
```

All services communicate over an internal Docker bridge network. Only Nginx is exposed to the host network.

---

## Services

| Service | Container | Internal Port |
|---------|-----------|--------------|
| Nginx (proxy) | `wms_nginx` | 80, 443 (host) |
| Next.js frontend | `wms_frontend` | 3000 |
| FastAPI backend | `wms_backend` | 8000 |
| PostgreSQL | `wms_db` | 5432 |
| Redis | `wms_redis` | 6379 |

---

## API Documentation

When the system is running, the FastAPI interactive docs are available at:
- Swagger UI: `http://<server>/api/docs`
- ReDoc: `http://<server>/api/redoc`

---

## User Roles

| Role | Description |
|------|-------------|
| `admin` | Full access: user management, audit logs, all features |
| `manager` | All warehouse operations, reports, alerts; no user management |
| `staff` | Receive, issue, transfer stock; view inventory |
| `viewer` | Read-only access to inventory, dashboard, reports |

---

## Backup & Restore

### Manual backup

```bash
./scripts/backup.sh
```

Backups are saved to `./backups/` by default.

### Restore from backup

```bash
./scripts/restore.sh ./backups/wms_db_20260101_020000.sql.gz
```

### Recommended: Automated daily backup via cron

```cron
0 2 * * * /path/to/wms/scripts/backup.sh >> /var/log/wms-backup.log 2>&1
```

---

## HTTPS Setup (Optional but Recommended)

Generate a self-signed certificate:

```bash
./scripts/gen-ssl.sh wms.local
```

Then uncomment the HTTPS server block in `nginx/nginx.conf` and restart Nginx:

```bash
docker compose restart nginx
```

Distribute `nginx/ssl/wms.crt` to client devices and import into their OS/browser trust store.

---

## Development

For local development with hot-reload:

```bash
docker compose up -d db redis
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd frontend && npm install
npm run dev
```

Or use the override file (mounts source code into containers):

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

---

## Environment Variables

See `.env.example` for all available variables and their descriptions.

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | PostgreSQL password — **change this** |
| `REDIS_PASSWORD` | Redis password — **change this** |
| `SECRET_KEY` | JWT signing key — **change this, min 32 chars** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token lifetime (default: 60) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (default: 7) |
| `FIRST_ADMIN_*` | First admin credentials (applied once on first startup) |

---

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Set a strong, random `SECRET_KEY` (32+ chars)
- [ ] Enable HTTPS on the internal network
- [ ] Restrict firewall: only port 80/443 accessible from client devices
- [ ] Set up daily automated backups
- [ ] Configure a fixed IP or DHCP reservation for the server
- [ ] Keep Docker images and OS updated on a regular maintenance schedule

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 6–8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 256 GB SSD | 500 GB–1 TB SSD |
| Network | 100 Mbps | Gigabit Ethernet |
| OS | Linux (Ubuntu 22.04+) | Ubuntu 22.04 LTS |

---

## License

Internal use only. All rights reserved.

