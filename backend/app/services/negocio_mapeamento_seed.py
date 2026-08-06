"""De/para NEGOCIO (DS) -> Negocio (cadastro), descoberto empiricamente comparando
a base DS real com a aba MAPAS (ver docs/plano.md). Frágil a novos valores
aparecendo na DS — por isso vive como linhas na tabela `negocio_ds_mapeamento`
(editável) e não como constante fixa no código; este dict é só a semente inicial.
"""

from sqlalchemy.orm import Session

from app.models.negocio_mapeamento import NegocioDsMapeamento

MAPEAMENTO_INICIAL = {
    "FIELD MARKETING": "TRADE",
    "MAO DE OBRA TEMPORARIA": "TALENTOS",
    "CLT": "TALENTOS",
    "MAO DE OBRA INTERMITENTE": "TALENTOS",
    "RECRUTAMENTO E SELECAO": "TALENTOS",
    "ESTAGIARIOS": "TALENTOS",
}


def semear_mapeamento(db: Session) -> int:
    existentes = {m.negocio_ds for m in db.query(NegocioDsMapeamento).all()}
    criados = 0
    for negocio_ds, negocio_cadastro in MAPEAMENTO_INICIAL.items():
        if negocio_ds in existentes:
            continue
        db.add(NegocioDsMapeamento(negocio_ds=negocio_ds, negocio_cadastro=negocio_cadastro))
        criados += 1
    return criados
