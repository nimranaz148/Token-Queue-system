from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import AppException, app_exception_handler
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

app = FastAPI(
    title="Clinic Token & Queue SaaS API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_exception_handler(AppException, app_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Clinic Token & Queue SaaS API is running."}
