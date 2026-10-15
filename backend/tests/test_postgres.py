import os

import pytest
from alembic.runtime.migration import MigrationContext
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import make_url, text

from alembic import command
from app.core.config import Settings
from app.core.database import database_ready, make_engine, migration_config, required_heads
from app.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def database():
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("TEST_DATABASE_URL no definida: usar el perfil test de Docker Compose")
    url = make_url(raw_url)
    if url.drivername != "postgresql+psycopg" or not (url.database or "").endswith("_test"):
        pytest.fail("Las pruebas requieren PostgreSQL y una base dedicada con sufijo _test")
    engine = make_engine(url)
    try:
        yield engine, url
    finally:
        engine.dispose()


def migrate(engine, target):
    config = migration_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, target)


def test_clean_database_upgrade_repeat_and_downgrade(database):
    engine, _ = database
    config = migration_config()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        assert not MigrationContext.configure(connection).get_current_heads()
    assert not database_ready(engine, required_heads())
    migrate(engine, "head")
    migrate(engine, "head")
    assert database_ready(engine, required_heads())
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version()")).scalar_one().startswith("PostgreSQL")


def test_readiness_uses_real_postgresql(database):
    engine, url = database
    migrate(engine, "head")
    config = Settings(
        app_env="test",
        postgres_host=url.host,
        postgres_port=url.port or 5432,
        postgres_user=url.username,
        postgres_password=SecretStr(url.password),
        postgres_db=url.database,
        _env_file=None,
    )
    with TestClient(create_app(config)) as client:
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_transactions_roll_back_on_failure(database):
    engine, _ = database
    # Tabla exclusivamente temporal: ninguna entidad de negocio anticipada.
    with engine.connect() as connection:
        connection.execute(text("CREATE TEMP TABLE phase0_probe (id integer PRIMARY KEY)"))
        connection.commit()
        with pytest.raises(RuntimeError), connection.begin():
            connection.execute(text("INSERT INTO phase0_probe VALUES (1)"))
            raise RuntimeError("fallo simulado")
        assert connection.execute(text("SELECT count(*) FROM phase0_probe")).scalar_one() == 0
