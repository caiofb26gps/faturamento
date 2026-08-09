"""Ingere a DS real e gera mapas de alguns clientes conhecidos, só para deixar
o banco de demonstração (dev.db) com dados de verdade para navegar no front."""

import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.cliente import Cliente
from app.models.enums import TipoImportacao
from app.models.usuario import Usuario
from app.services.geracao_mapa import SegmentacaoNaoSuportada, gerar_mapas
from app.services.ingestao import criar_importacao, processar_importacao

CAMINHO_DS = r"C:\Users\caio.batista\Downloads\DS julho.xlsx"
CLIENTES_DEMO = [
    ("3M", "TALENTOS"),
    ("BARRY WEHMILLER", "TALENTOS"),
    ("BAUDUCCO", "TALENTOS"),
    ("A C NIELSEN DO BRASIL", "TALENTOS"),
]

db = SessionLocal()
try:
    usuario = db.query(Usuario).first()
    importacao = criar_importacao(
        db, competencia="202605", tipo=TipoImportacao.CLOSED_INICIAL, usuario_id=usuario.id, arquivo_original_path=CAMINHO_DS
    )
    resumo = processar_importacao(db, importacao.id)
    print(f"ingestão: {resumo.linhas_resolvidas}/{resumo.total_linhas} resolvidas")

    from app.models.lancamento import LancamentoVerba

    for nome, negocio in CLIENTES_DEMO:
        cliente = db.query(Cliente).filter(Cliente.nome == nome, Cliente.negocio == negocio).first()
        if cliente is None:
            print(f"  [pular] {nome}/{negocio} não encontrado no cadastro")
            continue
        competencias = [
            c[0]
            for c in db.query(LancamentoVerba.competencia)
            .filter(LancamentoVerba.cliente_id == cliente.id)
            .distinct()
            .all()
        ]
        for competencia in competencias:
            try:
                mapas, fora_das_regras = gerar_mapas(db, cliente.id, competencia)
                print(f"  {nome} ({competencia}): {len(mapas)} mapa(s) gerado(s), {fora_das_regras.quantidade} fora das regras")
            except SegmentacaoNaoSuportada as exc:
                print(f"  [pular] {nome}: {exc}")
finally:
    db.close()
