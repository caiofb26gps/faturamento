from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Postgres em produção (Railway), SQLite no dev local — a diferença fica toda no
# DATABASE_URL. Os tipos que variam entre os dois estão em app/models/types.py.
engine = create_engine(settings.database_url, pool_pre_ping=True)


@event.listens_for(Engine, "connect")
def _ativar_foreign_keys(dbapi_connection, connection_record):
    """SQLite não valida foreign key por padrão; o Postgres valida.

    Sem isso o dev local aceita silenciosamente lixo que a produção rejeita — e
    pior: um DELETE em massa deixa filhos órfãos que depois "grudam" numa linha
    nova que reusa o mesmo id (aconteceu aqui: condições de uma regra apagada
    reapareceram numa regra nova, mudando o que ela testava).
    """
    if type(dbapi_connection).__module__.split(".")[0] != "sqlite3":
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
