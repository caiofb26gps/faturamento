from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.auth import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(require_admin)):
    return db.query(Usuario).order_by(Usuario.nome).all()


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar(payload: UsuarioCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_admin)):
    if db.query(Usuario).filter(Usuario.email == payload.email).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um usuário com esse e-mail")
    novo = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        papel=payload.papel,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo
