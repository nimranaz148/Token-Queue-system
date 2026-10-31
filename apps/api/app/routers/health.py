from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "clinic-api",
        "environment": "active",
    }
