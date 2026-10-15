from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.main import create_app


def settings(**overrides) -> Settings:
    return Settings(postgres_password=SecretStr("test-only"), _env_file=None, **overrides)


def test_liveness_does_not_require_database():
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"


def test_database_failure_is_unavailable_without_exposing_details():
    with TestClient(create_app(settings())) as client:
        with patch(
            "app.api.health.database_ready",
            side_effect=OperationalError("SELECT secret", {}, Exception("private-password")),
        ):
            response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "private-password" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_unmigrated_schema_is_unavailable():
    with TestClient(create_app(settings())) as client:
        with patch("app.api.health.database_ready", return_value=False):
            assert client.get("/api/v1/health/ready").status_code == 503


def test_production_does_not_expose_openapi():
    with TestClient(create_app(settings(app_env="production"))) as client:
        assert client.get("/api/v1/docs").status_code == 404
        assert client.get("/api/v1/openapi.json").status_code == 404


def test_database_password_special_characters_are_preserved():
    configuration = Settings(postgres_password=SecretStr("test:%@/word"), _env_file=None)
    assert configuration.database_url.password == "test:%@/word"
    assert "test:%@/word" not in repr(configuration)
