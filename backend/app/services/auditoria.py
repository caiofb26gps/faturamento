from sqlalchemy.orm import Session

from app.models.auditoria import AuditoriaAlteracao
from app.models.enums import AcaoAuditoria


def registrar(
    db: Session,
    *,
    entidade: str,
    entidade_id: int,
    usuario_id: int,
    acao: AcaoAuditoria,
    dados_antes: dict | None = None,
    dados_depois: dict | None = None,
) -> None:
    db.add(
        AuditoriaAlteracao(
            entidade=entidade,
            entidade_id=entidade_id,
            usuario_id=usuario_id,
            acao=acao,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
        )
    )
