from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    # Origens extras liberadas no CORS, separadas por vírgula (ex: a URL do
    # frontend em produção). localhost em qualquer porta já é sempre liberado
    # para o dev — ver app/main.py.
    cors_origins: str = ""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    credentials_encryption_key: str
    upload_dir: str = "./uploads"
    generated_dir: str = "./generated"


@lru_cache
def get_settings() -> Settings:
    return Settings()
