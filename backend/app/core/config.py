from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    # Se preenchidos, têm prioridade sobre database_url — conectam no Turso em vez
    # do SQLite local (ver app/core/database.py). turso_database_url vem do painel
    # do Turso como "libsql://<db>-<org>.turso.io"; o prefixo "libsql://" é
    # removido na hora de montar a engine, então tanto pode vir com ou sem ele.
    turso_database_url: str | None = None
    turso_auth_token: str | None = None
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    credentials_encryption_key: str
    upload_dir: str = "./uploads"
    generated_dir: str = "./generated"


@lru_cache
def get_settings() -> Settings:
    return Settings()
