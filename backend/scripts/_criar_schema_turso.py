"""Cria o schema (todas as tabelas) direto no Turso via HTTP, sem depender do
dialeto sqlalchemy-libsql (que só compila em Linux/macOS — não roda neste
Windows local). Compila o DDL usando o dialeto sqlite padrão do SQLAlchemy
(libSQL é compatível) e executa via libsql_client puro (aiohttp, sem Rust).

Uso: python scripts/_criar_schema_turso.py
Lê TURSO_DATABASE_URL / TURSO_AUTH_TOKEN do .env.
"""

import os
import sys

sys.path.insert(0, ".")

import libsql_client
from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateTable

from app.core.config import get_settings

settings = get_settings()
if not (settings.turso_database_url and settings.turso_auth_token):
    print("TURSO_DATABASE_URL / TURSO_AUTH_TOKEN não configurados no .env")
    sys.exit(1)

# app.core.database cria a engine na importação — e a engine do libsql não roda
# neste Windows local (só tem wheel Rust pra Linux/macOS). Como este script só
# precisa do metadata das tabelas (não de uma conexão real via essa engine),
# escondo as variáveis do Turso antes de importar, forçando o fallback SQLite.
# String vazia (não pop) porque pydantic-settings volta a ler do .env se a
# variável simplesmente não existir em os.environ.
os.environ["TURSO_DATABASE_URL"] = ""
os.environ["TURSO_AUTH_TOKEN"] = ""
get_settings.cache_clear()

from app.core.database import Base  # noqa: E402
from app.models import *  # noqa: F401,F403,E402

url_http = settings.turso_database_url.removeprefix("libsql://")
client = libsql_client.create_client_sync(url=f"https://{url_http}", auth_token=settings.turso_auth_token)

dialect = sqlite.dialect()
criadas, ja_existiam = 0, 0
for table in Base.metadata.sorted_tables:
    ddl = str(CreateTable(table).compile(dialect=dialect))
    try:
        client.execute(ddl)
        criadas += 1
        print(f"  criada: {table.name}")
    except Exception as exc:  # noqa: BLE001
        if "already exists" in str(exc):
            ja_existiam += 1
            print(f"  já existia: {table.name}")
        else:
            print(f"  ERRO em {table.name}: {exc}")
            raise

print(f"\n{criadas} tabela(s) criada(s), {ja_existiam} já existente(s).")
client.close()
