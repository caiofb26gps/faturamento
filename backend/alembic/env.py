from logging.config import fileConfig

from alembic import context

from app.core.config import get_settings
from app.core.database import Base, engine
from app.models import *  # noqa: F401,F403 -- garante que todos os modelos sejam registrados

config = context.config
# Só usado pelo modo offline (--sql); o online usa a `engine` já construída em
# app.core.database, que sabe montar a conexão do Turso quando configurado —
# reconstruir isso aqui via engine_from_config perderia o connect_args do libsql.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
