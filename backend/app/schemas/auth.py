from pydantic import BaseModel, EmailStr

from app.models.enums import PapelUsuario


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    papel: PapelUsuario
    ativo: bool

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    papel: PapelUsuario = PapelUsuario.ANALISTA
