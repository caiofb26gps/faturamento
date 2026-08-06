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
    return db.query(RegraSegmentacao).filter(RegraSegmentacao.cliente_id == cliente_id).all()


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
