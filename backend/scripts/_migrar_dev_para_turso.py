"""Copia os cadastros do dev.db local para o Turso (via HTTP).

Migra apenas tabelas de cadastro/configuração — não copia lançamentos da DS nem
mapas gerados, que são dados operacionais de cada competência e devem ser
carregados pela própria aplicação (upload da DS).

Idempotente por LINHA (não por tabela): compara os ids já presentes no Turso e
só insere o que falta, então pode rodar de novo depois de uma migração parcial.

Uso: python scripts/_migrar_dev_para_turso.py
"""

import sqlite3
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

from _turso_http import criar_client, encerrar

# Ordem importa: pai antes de filho, por causa das foreign keys.
TABELAS = [
    "usuarios",
    "atributos_segmentacao",
    "campos_cadastrais_mapa",
    "negocio_ds_mapeamento",
    "de_para_modelos",
    "de_para_verbas",
    "clientes",
    "cliente_identificadores",
    "regras_segmentacao",
    "regra_condicoes",
]

LOTE = 200  # linhas por batch; de_para_verbas tem ~420 e o Turso limita payload

local = sqlite3.connect("dev.db")
local.row_factory = sqlite3.Row
client = criar_client()

for tabela in TABELAS:
    linhas = local.execute(f"SELECT * FROM {tabela}").fetchall()
    if not linhas:
        print(f"  [vazia] {tabela}: nada no dev.db")
        continue

    ids_no_turso = {r[0] for r in client.execute(f"SELECT id FROM {tabela}").rows}
    faltando = [linha for linha in linhas if linha["id"] not in ids_no_turso]
    if not faltando:
        print(f"  [ok] {tabela}: {len(linhas)} linha(s) já presente(s)")
        continue

    colunas = linhas[0].keys()
    placeholders = ", ".join("?" for _ in colunas)
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({placeholders})"

    enviadas = 0
    for i in range(0, len(faltando), LOTE):
        batch = faltando[i : i + LOTE]
        client.batch([(sql, [linha[c] for c in colunas]) for linha in batch])
        enviadas += len(batch)
    ja_tinha = len(linhas) - len(faltando)
    sufixo = f" ({ja_tinha} já existia(m))" if ja_tinha else ""
    print(f"  {tabela}: {enviadas} linha(s) copiada(s){sufixo}")

local.close()
client.close()
print("\nMigração de cadastros concluída.")
encerrar()
