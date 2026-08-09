from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.crypto import encrypt_secret
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.cliente import Cliente, ClienteIdentificador
from app.models.enums import AcaoAuditoria, PapelUsuario
from app.models.usuario import Usuario
from app.schemas.cliente import (
    ClienteCreate,
    ClienteIdentificadorCreate,
    ClienteIdentificadorOut,
    ClienteOut,
    ClienteUpdate,
)
from app.services.auditoria import registrar

router = APIRouter(prefix="/clientes", tags=["clientes"])


def _to_out(cliente: Cliente) -> ClienteOut:
    out = ClienteOut.model_validate(cliente)
    out.portal_credenciais_configuradas = bool(cliente.portal_login_cifrado or cliente.portal_senha_cifrada)
    out.total_regras = len(cliente.regras_segmentacao)
    return out


@router.get("", response_model=list[ClienteOut])
def listar_clientes(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Cliente).options(selectinload(Cliente.regras_segmentacao))
    if usuario.papel != PapelUsuario.ADMIN:
        query = query.filter(Cliente.analista_responsavel_id == usuario.id)
    return [_to_out(c) for c in query.order_by(Cliente.nome).all()]


@router.get("/{cliente_id}", response_model=ClienteOut)
def obter_cliente(cliente_id: int, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    cliente = _buscar_cliente_permitido(db, cliente_id, usuario)
    return _to_out(cliente)


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    payload: ClienteCreate, usuario: Usuario = Depends(require_admin), db: Session = Depends(get_db)
):
    dados = payload.model_dump(exclude={"portal_login", "portal_senha"})
    cliente = Cliente(
        **dados,
        portal_login_cifrado=encrypt_secret(payload.portal_login),
        portal_senha_cifrada=encrypt_secret(payload.portal_senha),
    )
    db.add(cliente)
    db.flush()
    registrar(
        db,
        entidade="clientes",
        entidade_id=cliente.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.CRIACAO,
        dados_depois=payload.model_dump(exclude={"portal_login", "portal_senha"}, mode="json"),
    )
    db.commit()
    db.refresh(cliente)
    return _to_out(cliente)


@router.put("/{cliente_id}", response_model=ClienteOut)
def atualizar_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    usuario: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")

    dados_antes = ClienteOut.model_validate(cliente).model_dump(mode="json")

    dados = payload.model_dump(exclude={"portal_login", "portal_senha"})
    for campo, valor in dados.items():
        setattr(cliente, campo, valor)
    if payload.portal_login is not None:
        cliente.portal_login_cifrado = encrypt_secret(payload.portal_login)
    if payload.portal_senha is not None:
        cliente.portal_senha_cifrada = encrypt_secret(payload.portal_senha)

    db.flush()
    registrar(
        db,
        entidade="clientes",
        entidade_id=cliente.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.EDICAO,
        dados_antes=dados_antes,
        dados_depois=dados,
    )
    db.commit()
    db.refresh(cliente)
    return _to_out(cliente)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_cliente(cliente_id: int, usuario: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    registrar(
        db,
        entidade="clientes",
        entidade_id=cliente.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.EXCLUSAO,
        dados_antes=ClienteOut.model_validate(cliente).model_dump(mode="json"),
    )
    db.delete(cliente)
    db.commit()


@router.get("/{cliente_id}/identificadores", response_model=list[ClienteIdentificadorOut])
def listar_identificadores(
    cliente_id: int, usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)
):
    _buscar_cliente_permitido(db, cliente_id, usuario)
    return db.query(ClienteIdentificador).filter(ClienteIdentificador.cliente_id == cliente_id).all()


@router.post(
    "/{cliente_id}/identificadores",
    response_model=ClienteIdentificadorOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_identificador(
    cliente_id: int,
    payload: ClienteIdentificadorCreate,
    usuario: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    identificador = ClienteIdentificador(cliente_id=cliente_id, **payload.model_dump())
    db.add(identificador)
    db.commit()
    db.refresh(identificador)
    return identificador


def _buscar_cliente_permitido(db: Session, cliente_id: int, usuario: Usuario) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    if usuario.papel != PapelUsuario.ADMIN and cliente.analista_responsavel_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem acesso a este cliente")
    return cliente
