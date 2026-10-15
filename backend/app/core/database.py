from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import URL, Engine, create_engine, text

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def make_engine(url: URL | str) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_timeout=3,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=3000"},
        hide_parameters=True,
    )


def migration_config() -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return config


def required_heads() -> set[str]:
    return set(ScriptDirectory.from_config(migration_config()).get_heads())


def database_ready(engine: Engine, expected_heads: set[str]) -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        actual_heads = set(MigrationContext.configure(connection).get_current_heads())
    return actual_heads == expected_heads
