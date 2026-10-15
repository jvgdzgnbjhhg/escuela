from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    allowed_origins: list[str] = [
        "http://localhost:3100",
        "http://127.0.0.1:3100",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    runtime_db_user: str = "evaluacion_app"
    runtime_db_password: SecretStr | None = None
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "evaluacion"
    postgres_user: str = "evaluacion"
    postgres_password: SecretStr

    @property
    def database_url(self) -> URL:
        # URL.create conserva caracteres especiales sin concatenar credenciales.
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
