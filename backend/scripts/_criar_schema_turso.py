"""Cria o schema (todas as tabelas) direto no Turso via HTTP, sem depender do
dialeto sqlalchemy-libsql (que só compila em Linux/macOS — não roda neste
Windows local). Compila o DDL usando o dialeto sqlite padrão do SQLAlchemy
(libSQL é compatível) e executa via libsql_client puro (aiohttp, sem Rust).

Uso: python scripts/_criar_schema_turso.py
Credenciais: ver scripts/_turso_http.py.
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

from sqlalchemy.dialects import sqlite
from sqlalchemy.schema import CreateTable

from _turso_http import criar_client, encerrar
from app.core.database import Base
from app.models import *  # noqa: F401,F403

client = criar_client()

dialect = sqlite.dialect()
# if_not_exists deixa o script idempotente (pode rodar de novo sem erro). Antes
# eu tentava distinguir "já existe" pela mensagem da exceção, mas o
# libsql_client via HTTP levanta KeyError('result') em erro de SQL, sem a
# mensagem original — então essa checagem por texto nunca funcionaria.
for table in Base.metadata.sorted_tables:
    ddl = str(CreateTable(table, if_not_exists=True).compile(dialect=dialect))
    client.execute(ddl)
    print(f"  ok: {table.name}")

print(f"\n{len(Base.metadata.sorted_tables)} tabela(s) garantida(s) no Turso.")
client.close()
encerrar()
