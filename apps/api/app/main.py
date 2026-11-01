from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import tenancy as _tenancy  # noqa: F401
from app.core.errors import AppException, app_exception_handler
from app.core.logging import RequestIdAndLoggingMiddleware
from app.routers.admin_clinics import router as admin_clinics_router
from app.routers.auth import router as auth_router
from app.routers.doctors import router as doctors_router
from app.routers.health import router as health_router
from app.routers.members import router as members_router
from app.routers.public_tokens import router as public_tokens_router
from app.routers.tokens import router as tokens_router
from app.routers.webhooks import router as webhooks_router

app = FastAPI(
    title="Clinic Token & Queue SaaS API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

__all__ = ["app"]

app.add_exception_handler(AppException, app_exception_handler)

app.add_middleware(RequestIdAndLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_clinics_router, prefix="/api/v1")
app.include_router(members_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(public_tokens_router, prefix="/api/v1")
app.include_router(tokens_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Clinic Token & Queue SaaS API is running."}
