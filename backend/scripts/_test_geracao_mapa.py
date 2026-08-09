"""Teste manual: ingere a DS real e gera o mapa de um cliente resolvido, para
inspecionar consistência interna (Subtotal = soma dos grupos, Total = Subtotal +
FEE + Impostos) e o arquivo .xlsx resultante."""

import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.cliente import Cliente
from app.models.enums import TipoImportacao
from app.models.mapa import MapaGerado
from app.models.usuario import Usuario
from app.services.geracao_mapa import gerar_mapas
from app.services.ingestao import criar_importacao, processar_importacao

CAMINHO_DS = r"C:\Users\caio.batista\Downloads\DS julho.xlsx"
NOME_CLIENTE = sys.argv[1] if len(sys.argv) > 1 else "3M"
NEGOCIO = sys.argv[2] if len(sys.argv) > 2 else "TALENTOS"

db = SessionLocal()
try:
    usuario = db.query(Usuario).first()
    importacao = criar_importacao(
        db, competencia="202605", tipo=TipoImportacao.CLOSED_INICIAL, usuario_id=usuario.id, arquivo_original_path=CAMINHO_DS
    )
    resumo = processar_importacao(db, importacao.id)
    print(f"ingestão: {resumo.linhas_resolvidas}/{resumo.total_linhas} resolvidas")

    cliente = db.query(Cliente).filter(Cliente.nome == NOME_CLIENTE, Cliente.negocio == NEGOCIO).first()
    if cliente is None:
        print(f"Cliente {NOME_CLIENTE!r}/{NEGOCIO!r} não encontrado")
        sys.exit(1)
    print(f"cliente: {cliente.nome} (id={cliente.id})")

    from app.models.lancamento import LancamentoVerba

    competencias = [
        c[0]
        for c in db.query(LancamentoVerba.competencia)
        .filter(LancamentoVerba.cliente_id == cliente.id)
        .distinct()
        .all()
    ]
    print(f"competencias disponíveis para este cliente: {competencias}")

    for competencia in competencias:
        mapas, fora_das_regras = gerar_mapas(db, cliente.id, competencia)
        print(f"\ncompetencia {competencia}: {len(mapas)} mapa(s) gerado(s), {fora_das_regras.quantidade} fora das regras")
        for mapa in mapas[:5]:
            print(f"  mapa id={mapa.id} regra_id={mapa.regra_segmentacao_id} alertas={mapa.alertas} arquivo={mapa.arquivo_path}")
            print(f"    valores_iniciais={mapa.valores_iniciais}")
finally:
    db.close()
