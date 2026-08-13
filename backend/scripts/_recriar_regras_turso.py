"""Reconstrói `regras_segmentacao` no Turso para o schema novo (com `logica`, sem
`atributo_segmentacao`/`valor_segmentacao`) e cria `regra_condicoes`.

Por que reconstruir em vez de ALTER: SQLite/libSQL não remove coluna com ALTER, e
as colunas antigas são NOT NULL — deixá-las faria todo INSERT novo falhar (o ORM
não as conhece mais). A forma canônica em SQLite é recriar a tabela.

Seguro aqui porque em produção só existe cadastro de teste (nenhum mapa gerado,
nenhum lançamento), e a fonte da verdade é o dev.db local — os cadastros são
recopiados depois por `_migrar_dev_para_turso.py`. NÃO use este script em um
banco com dados operacionais reais sem antes exportar.

Uso: python scripts/_recriar_regras_turso.py
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

# Confere que não há dado operacional em risco antes de dropar qualquer coisa.
for tabela in ("mapas_gerados", "lancamentos_verbas", "envios"):
    n = client.execute(f"SELECT COUNT(*) FROM {tabela}").rows[0][0]
    print(f"  {tabela}: {n} linha(s)")
    if n > 0:
        print(
            f"\nABORTADO: {tabela} tem {n} linha(s). Este script só é seguro num banco "
            "sem dados operacionais — exporte antes de continuar."
        )
        encerrar(1)

regras_antes = client.execute("SELECT COUNT(*) FROM regras_segmentacao").rows[0][0]
print(f"  regras_segmentacao: {regras_antes} linha(s) (serão recopiadas do dev.db depois)")

print("\nRecriando tabelas...")
client.execute("DROP TABLE IF EXISTS regra_condicoes")
client.execute("DROP TABLE IF EXISTS regras_segmentacao")

dialect = sqlite.dialect()
for nome in ("regras_segmentacao", "regra_condicoes"):
    tabela = Base.metadata.tables[nome]
    client.execute(str(CreateTable(tabela).compile(dialect=dialect)))
    print(f"  criada: {nome}")

print("\nPronto. Rode agora: python scripts/_migrar_dev_para_turso.py")
client.close()
encerrar()
