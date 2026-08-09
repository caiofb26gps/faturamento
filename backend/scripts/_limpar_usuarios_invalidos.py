"""Remove usuarios cujo e-mail é lixo herdado da coluna 'Analista' da planilha
(ex: '0', 'faturamento rj') — o `migrate_from_excel.py` já foi corrigido para não
criar mais esses stubs, isso aqui limpa quem já tinha sido criado antes da correção.

Antes de apagar, desvincula qualquer cliente/regra que apontava para esse usuário
como analista (fica null em vez de referenciar um usuário quebrado)."""

import sys

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.cliente import Cliente
from app.models.regra import RegraSegmentacao
from app.models.usuario import Usuario


def parece_email(valor: str | None) -> bool:
    return bool(valor) and "@" in valor and "." in valor.split("@", 1)[1]


db = SessionLocal()
try:
    invalidos = [u for u in db.query(Usuario).all() if not parece_email(u.email)]
    print(f"Usuários com e-mail inválido encontrados: {[(u.id, u.email) for u in invalidos]}")

    for u in invalidos:
        n1 = db.query(Cliente).filter(Cliente.analista_responsavel_id == u.id).update({"analista_responsavel_id": None})
        n2 = db.query(RegraSegmentacao).filter(RegraSegmentacao.analista_id == u.id).update({"analista_id": None})
        if n1 or n2:
            print(f"  desvinculado de {n1} cliente(s) e {n2} regra(s): usuario id={u.id}")
        db.delete(u)

    db.commit()
    print(f"Removidos: {len(invalidos)} usuário(s) inválido(s). Restam {db.query(Usuario).count()} usuário(s).")
finally:
    db.close()
