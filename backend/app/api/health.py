from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import database_ready

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "ready", "unavailable"]


@router.get("/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse, responses={503: {"model": HealthResponse}})
def ready(request: Request) -> HealthResponse | JSONResponse:
    try:
        available = database_ready(request.app.state.engine, request.app.state.expected_heads)
    except SQLAlchemyError:
        available = False
    if not available:
        # Nunca devolver detalles de conexión, SQL ni credenciales al cliente.
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable"},
            headers={"Cache-Control": "no-store"},
        )
    return HealthResponse(status="ready")
