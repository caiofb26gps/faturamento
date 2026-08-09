"""Dev-only: reduz o banco a apenas o cliente SHERWIN WILLIAMS nas tabelas
transacionais/por-cliente (lançamentos, regras, mapas, envios, identificadores,
importações e o próprio cadastro do cliente), para facilitar testar e refinar o
front sem a lista de 390 clientes no meio do caminho.

Mantém tabelas de referência/sistema intactas (de_para_modelos + itens,
atributos_segmentacao, campos_cadastrais_mapa, usuarios) — não são "dados de
cliente", são configuração que o próprio Sherwin também usa.
"""

import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.cliente import Cliente, ClienteIdentificador
from app.models.envio import Envio
from app.models.importacao import Importacao
from app.models.lancamento import LancamentoVerba
from app.models.mapa import MapaGerado
from app.models.regra import RegraSegmentacao

NOME_CLIENTE = "SHERWIN WILLIAMS"

db = SessionLocal()
try:
    cliente = db.query(Cliente).filter(Cliente.nome == NOME_CLIENTE).one()
    print(f"Mantendo apenas: {cliente.nome} (id={cliente.id})")

    outros_mapas_ids = [m.id for m in db.query(MapaGerado.id).filter(MapaGerado.cliente_id != cliente.id).all()]
    if outros_mapas_ids:
        db.query(Envio).filter(Envio.mapa_gerado_id.in_(outros_mapas_ids)).delete(synchronize_session=False)
    n_mapas = db.query(MapaGerado).filter(MapaGerado.cliente_id != cliente.id).delete(synchronize_session=False)

    n_lanc = db.query(LancamentoVerba).filter(LancamentoVerba.cliente_id != cliente.id).delete(synchronize_session=False)
    n_regras = db.query(RegraSegmentacao).filter(RegraSegmentacao.cliente_id != cliente.id).delete(synchronize_session=False)
    n_ident = db.query(ClienteIdentificador).filter(ClienteIdentificador.cliente_id != cliente.id).delete(synchronize_session=False)

    ids_importacoes_em_uso = {i for (i,) in db.query(LancamentoVerba.importacao_id).distinct().all()}
    todas_importacoes = db.query(Importacao).all()
    n_import = 0
    for imp in todas_importacoes:
        if imp.id not in ids_importacoes_em_uso:
            db.delete(imp)
            n_import += 1

    n_clientes = db.query(Cliente).filter(Cliente.id != cliente.id).delete(synchronize_session=False)

    db.commit()
    print(f"Removidos: {n_clientes} clientes, {n_regras} regras, {n_ident} identificadores, "
          f"{n_lanc} lançamentos, {n_mapas} mapas, {n_import} importações órfãs.")
    print(f"Restam: {db.query(Cliente).count()} cliente(s), {db.query(LancamentoVerba).count()} lançamento(s), "
          f"{db.query(RegraSegmentacao).count()} regra(s), {db.query(MapaGerado).count()} mapa(s).")
finally:
    db.close()
