from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.cliente import Cliente
from app.models.enums import AcaoAuditoria
from app.models.regra import RegraSegmentacao
from app.models.usuario import Usuario
from app.schemas.regra import RegraSegmentacaoCreate, RegraSegmentacaoOut, RegraSegmentacaoUpdate
from app.services.auditoria import registrar

router = APIRouter(prefix="/clientes/{cliente_id}/regras", tags=["regras-segmentacao"])


def _cliente_ou_404(db: Session, cliente_id: int) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return cliente


@router.get("", response_model=list[RegraSegmentacaoOut])
def listar_regras(cliente_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    _cliente_ou_404(db, cliente_id)
    return (
        db.query(RegraSegmentacao)
        .filter(RegraSegmentacao.cliente_id == cliente_id)
        .order_by(RegraSegmentacao.ordem, RegraSegmentacao.id)
        .all()
    )


@router.put("/reordenar", response_model=list[RegraSegmentacaoOut])
def reordenar_regras(
    cliente_id: int,
    ids_em_ordem: list[int],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    """Recebe os ids das regras do cliente na ordem desejada (primeira = testada
    primeiro no "grande SE") e renumera `ordem` de acordo."""
    _cliente_ou_404(db, cliente_id)
    regras = {r.id: r for r in db.query(RegraSegmentacao).filter(RegraSegmentacao.cliente_id == cliente_id).all()}
    if set(ids_em_ordem) != set(regras.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A lista precisa conter exatamente os ids de todas as regras deste cliente",
        )
    for posicao, regra_id in enumerate(ids_em_ordem):
        regras[regra_id].ordem = posicao
    db.commit()
    return (
        db.query(RegraSegmentacao)
        .filter(RegraSegmentacao.cliente_id == cliente_id)
        .order_by(RegraSegmentacao.ordem, RegraSegmentacao.id)
        .all()
    )


@router.post("", response_model=RegraSegmentacaoOut, status_code=status.HTTP_201_CREATED)
def criar_regra(
    cliente_id: int,
    payload: RegraSegmentacaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    _cliente_ou_404(db, cliente_id)
    regra = RegraSegmentacao(cliente_id=cliente_id, **payload.model_dump())
    db.add(regra)
    db.flush()
    registrar(
        db,
        entidade="regras_segmentacao",
        entidade_id=regra.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.CRIACAO,
        dados_depois=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(regra)
    return regra


@router.put("/{regra_id}", response_model=RegraSegmentacaoOut)
def atualizar_regra(
    cliente_id: int,
    regra_id: int,
    payload: RegraSegmentacaoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    regra = (
        db.query(RegraSegmentacao)
        .filter(RegraSegmentacao.id == regra_id, RegraSegmentacao.cliente_id == cliente_id)
        .first()
    )
    if regra is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada")

    dados_antes = RegraSegmentacaoOut.model_validate(regra).model_dump(mode="json")
    for campo, valor in payload.model_dump().items():
        setattr(regra, campo, valor)

    db.flush()
    registrar(
        db,
        entidade="regras_segmentacao",
        entidade_id=regra.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.EDICAO,
        dados_antes=dados_antes,
        dados_depois=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(regra)
    return regra


@router.delete("/{regra_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_regra(
    cliente_id: int,
    regra_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    regra = (
        db.query(RegraSegmentacao)
        .filter(RegraSegmentacao.id == regra_id, RegraSegmentacao.cliente_id == cliente_id)
        .first()
    )
    if regra is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regra não encontrada")
    registrar(
        db,
        entidade="regras_segmentacao",
        entidade_id=regra.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.EXCLUSAO,
        dados_antes=RegraSegmentacaoOut.model_validate(regra).model_dump(mode="json"),
    )
    db.delete(regra)
    db.commit()
