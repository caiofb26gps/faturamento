from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.models.usuario import Usuario
from app.schemas.auth import TokenResponse, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if usuario is None or not usuario.ativo or not verify_password(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    token = create_access_token(subject=usuario.email, role=usuario.papel.value)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(get_current_user)):
    return usuario
