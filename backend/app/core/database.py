from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
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


@event.listens_for(Engine, "connect")
def _ativar_foreign_keys(dbapi_connection, connection_record):
    """SQLite não valida foreign key por padrão; o Turso valida.

    Sem isso o dev local aceita silenciosamente lixo que a produção rejeita —
    e pior: um DELETE em massa deixa filhos órfãos que depois "grudam" numa
    linha nova que reusa o mesmo id (aconteceu aqui: condições de uma regra
    apagada reapareceram numa regra nova, mudando o que ela testava).
    """
    if not hasattr(dbapi_connection, "execute"):
        return
    try:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    except Exception:  # noqa: BLE001 - não é SQLite (ou não suporta): segue sem o pragma
        pass


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
