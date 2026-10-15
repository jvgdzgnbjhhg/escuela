from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response

from app.api.academics import router as academics_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.institutions import router as institutions_router
from app.core.config import Settings
from app.core.database import make_engine, required_heads
from app.core.http import RequestBoundary
from app.services.security import hash_password, new_token


def create_app(settings: Settings | None = None) -> FastAPI:
    configuration = settings if settings is not None else Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = configuration
        app.state.dummy_password_hash = hash_password(new_token())
        app.state.engine = make_engine(configuration.database_url)
        app.state.expected_heads = required_heads()
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(
        title="Plataforma de Evaluación Académica",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if configuration.app_env == "production" else "/api/v1/docs",
        redoc_url=None,
        openapi_url=None if configuration.app_env == "production" else "/api/v1/openapi.json",
    )

    app.add_middleware(RequestBoundary, allowed_origins=configuration.allowed_origins)

    @app.exception_handler(RequestValidationError)
    async def safe_validation(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
                    for error in exc.errors()
                ]
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.exception_handler(IntegrityError)
    async def safe_integrity(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content={"detail": "El registro está duplicado o tiene relaciones incompatibles"},
            headers={"Cache-Control": "no-store"},
        )

    @app.middleware("http")
    async def no_cache_health(request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(institutions_router, prefix="/api/v1")
    app.include_router(academics_router, prefix="/api/v1")
    return app
