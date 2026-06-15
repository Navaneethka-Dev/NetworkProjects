"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.audit_log import router as audit_log_router
from app.api.auth import router as auth_router
from app.api.backups import router as backups_router
from app.api.compliance import router as compliance_router
from app.api.dashboard import router as dashboard_router
from app.api.deployments import router as deployments_router
from app.api.devices import router as devices_router
from app.api.templates import router as templates_router
from app.api.users import router as users_router
from app.config import settings
from app.database import create_tables


async def _seed_database() -> None:
    """Seed the database with default admin user and sample data (idempotent)."""
    from sqlalchemy import func, select
    from app.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User, RoleEnum
    from app.models.device import Device, DeviceGroup, DeviceStatusEnum

    async with AsyncSessionLocal() as db:
        # ── Create default admin user ────────────────────────────────────────
        existing = await db.execute(select(User).where(User.username == "Navaneeth"))
        if not existing.scalar_one_or_none():
            admin = User(
                username="Navaneeth",
                email="navaneeth@netautomate.local",
                hashed_password=hash_password("Amma123"),
                role=RoleEnum.admin,
                is_active=True,
            )
            db.add(admin)
            await db.flush()

        # ── Seed sample devices in mock mode so dashboard isn't empty ────────
        if settings.MOCK_DEVICES:
            count_result = await db.execute(select(func.count(Device.id)))
            if (count_result.scalar() or 0) == 0:
                # Create device groups first
                core_group = DeviceGroup(name="Core", description="Core switching layer")
                edge_group = DeviceGroup(name="Edge", description="Edge routers and firewalls")
                db.add(core_group)
                db.add(edge_group)
                await db.flush()

                sample_devices = [
                    Device(hostname="core-sw-01",  ip_address="10.0.0.1", device_type="cisco_ios",     vendor="cisco",   model="Catalyst 9300", ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=core_group.id),
                    Device(hostname="core-sw-02",  ip_address="10.0.0.2", device_type="cisco_ios",     vendor="cisco",   model="Catalyst 9300", ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=core_group.id),
                    Device(hostname="core-sw-03",  ip_address="10.0.0.3", device_type="cisco_nxos",    vendor="cisco",   model="Nexus 9300",    ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.offline,     group_id=core_group.id),
                    Device(hostname="dist-rt-01",  ip_address="10.1.0.1", device_type="juniper_junos", vendor="juniper", model="MX480",         ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=edge_group.id),
                    Device(hostname="dist-rt-02",  ip_address="10.1.0.2", device_type="juniper_junos", vendor="juniper", model="MX480",         ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=edge_group.id),
                    Device(hostname="edge-fw-01",  ip_address="10.2.0.1", device_type="cisco_ios",     vendor="cisco",   model="ASA 5506",      ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=edge_group.id),
                    Device(hostname="edge-fw-02",  ip_address="10.2.0.2", device_type="cisco_ios",     vendor="cisco",   model="ASA 5506",      ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.unreachable, group_id=edge_group.id),
                    Device(hostname="acc-sw-01",   ip_address="10.3.0.1", device_type="arista_eos",    vendor="arista",  model="7050",          ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=None),
                    Device(hostname="acc-sw-02",   ip_address="10.3.0.2", device_type="arista_eos",    vendor="arista",  model="7050",          ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.online,      group_id=None),
                    Device(hostname="mgmt-srv-01", ip_address="10.4.0.1", device_type="cisco_ios",     vendor="cisco",   model="ISR 4451",      ssh_port=22, username="admin", password="admin", status=DeviceStatusEnum.maintenance, group_id=None),
                ]
                for dev in sample_devices:
                    db.add(dev)

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables + seed on startup. Use Alembic in production instead of create_tables."""
    await create_tables()
    await _seed_database()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Network Automation Platform — REST API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(devices_router)
app.include_router(templates_router)
app.include_router(deployments_router)
app.include_router(backups_router)
app.include_router(dashboard_router)
app.include_router(compliance_router)
app.include_router(audit_log_router)


@app.get("/api/health", tags=["Health"])
async def health():
    return JSONResponse({"status": "ok", "version": settings.APP_VERSION})


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({"message": f"{settings.APP_NAME} API", "docs": "/api/docs"})
