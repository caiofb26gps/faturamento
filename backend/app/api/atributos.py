from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.atributo import AtributoSegmentacao
from app.models.usuario import Usuario
from app.schemas.atributo import AtributoSegmentacaoCreate, AtributoSegmentacaoOut

router = APIRouter(prefix="/atributos-segmentacao", tags=["atributos-segmentacao"])


@router.get("", response_model=list[AtributoSegmentacaoOut])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    return db.query(AtributoSegmentacao).order_by(AtributoSegmentacao.codigo).all()


@router.post("", response_model=AtributoSegmentacaoOut, status_code=status.HTTP_201_CREATED)
def criar(
    payload: AtributoSegmentacaoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_admin)
):
    atributo = AtributoSegmentacao(**payload.model_dump())
    db.add(atributo)
    db.commit()
    db.refresh(atributo)
    return atributo
