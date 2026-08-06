from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except JWTError:
        raise credentials_error

    if email is None:
        raise credentials_error

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not usuario.ativo:
        raise credentials_error
    return usuario


def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.papel != PapelUsuario.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ação restrita a administradores")
    return usuario
