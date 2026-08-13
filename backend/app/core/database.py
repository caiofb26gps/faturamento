from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def _criar_engine():
    if settings.turso_database_url and settings.turso_auth_token:
        # sqlalchemy-libsql só tem wheel pronta pra Linux/macOS (compila Rust em
        # Windows) — só precisa estar instalada onde essa engine é de fato criada
        # (produção/Render), nunca no dev local em SQLite puro.
        host = settings.turso_database_url.removeprefix("libsql://")
        return create_engine(
            f"sqlite+libsql://{host}?secure=true",
            connect_args={"auth_token": settings.turso_auth_token},
            pool_pre_ping=True,
        )
    return create_engine(settings.database_url, pool_pre_ping=True)


engine = _criar_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
