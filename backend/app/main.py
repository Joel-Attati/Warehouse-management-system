"""FastAPI Application entry point for Warehouse Management System."""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from app.config import settings
from app.database import AsyncSessionLocal, Base, engine
from app.models.user import User, UserRole
from app.routers import (
    alerts,
    audit,
    auth,
    dashboard,
    health,
    inventory,
    movements,
    products,
    reports,
    users,
    warehouses,
)
from app.utils.password import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wms")


async def seed_initial_users():
    """Ensure standard role accounts exist for initial login."""
    async with AsyncSessionLocal() as session:
        default_accounts = [
            ("admin", "admin@warehouse.local", "admin123", UserRole.admin.value, "System Administrator"),
            ("manager", "manager@warehouse.local", "manager123", UserRole.manager.value, "Warehouse Manager"),
            ("staff", "staff@warehouse.local", "staff123", UserRole.staff.value, "Warehouse Staff"),
            ("viewer", "viewer@warehouse.local", "viewer123", UserRole.viewer.value, "Read Only Viewer"),
        ]
        for uname, uemail, upass, urole, ufullname in default_accounts:
            stmt = select(User).where(User.username == uname)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if not existing:
                user = User(
                    username=uname,
                    email=uemail,
                    hashed_password=hash_password(upass),
                    full_name=ufullname,
                    role=urole,
                    is_active=True,
                )
                session.add(user)
                logger.info("Created account: %s (%s)", uname, urole)
            else:
                existing.hashed_password = hash_password(upass)
                existing.is_active = True
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info("DATABASE_URL BEING USED: %s", settings.DATABASE_URL)
    # Ensure uploads directory exists
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOADS_DIR, "products"), exist_ok=True)

    # Create tables if not present
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial administrator and role accounts
    await seed_initial_users()

    yield

    # Teardown
    await engine.dispose()


app = FastAPI(
    title="Warehouse Management System API",
    description="Modular on-premises REST API for warehouse operations, inventory, and movements.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS setup
origins = settings.BACKEND_CORS_ORIGINS or [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists on host/container
try:
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
except OSError:
    settings.UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)

# Static file serving for uploads
app.mount("/static/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")

# Health endpoints at root
app.include_router(health.router)

# Mount all feature routers under both `/` and `/api` to support flexible proxy configurations
api_router = APIRouter()
feature_routers = [
    health.router,
    auth.router,
    users.router,
    warehouses.router,
    products.router,
    inventory.router,
    movements.router,
    alerts.router,
    dashboard.router,
    reports.router,
    audit.router,
]

for r in feature_routers:
    app.include_router(r)
    api_router.include_router(r)

app.include_router(api_router, prefix="/api")

