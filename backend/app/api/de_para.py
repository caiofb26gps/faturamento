from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.cliente import Cliente
from app.models.de_para import CampoCadastralMapa, DeParaModelo, DeParaVerba
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.schemas.de_para import (
    CampoCadastralMapaCreate,
    CampoCadastralMapaOut,
    DeParaModeloCreate,
    DeParaModeloOut,
    DeParaVerbaCreate,
    DeParaVerbaOut,
)
from app.services.auditoria import registrar

router = APIRouter(prefix="/de-para", tags=["de-para"])


def _com_extras(db: Session, modelo: DeParaModelo) -> DeParaModeloOut:
    total_itens = db.query(func.count(DeParaVerba.id)).filter(DeParaVerba.de_para_modelo_id == modelo.id).scalar()
    clientes_vinculados = [
        nome for (nome,) in db.query(Cliente.nome).filter(Cliente.de_para_modelo_id == modelo.id).all()
    ]
    return DeParaModeloOut.model_validate(modelo).model_copy(
        update={"total_itens": total_itens, "clientes_vinculados": clientes_vinculados}
    )


@router.get("/modelos", response_model=list[DeParaModeloOut])
def listar_modelos(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    modelos = db.query(DeParaModelo).order_by(DeParaModelo.nome).all()
    return [_com_extras(db, modelo) for modelo in modelos]


@router.get("/modelos/{modelo_id}", response_model=DeParaModeloOut)
def obter_modelo(modelo_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    modelo = db.query(DeParaModelo).filter(DeParaModelo.id == modelo_id).first()
    if modelo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo de De/Para não encontrado")
    return _com_extras(db, modelo)


@router.post("/modelos", response_model=DeParaModeloOut, status_code=status.HTTP_201_CREATED)
def criar_modelo(
    payload: DeParaModeloCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_admin)
):
    modelo = DeParaModelo(**payload.model_dump())
    db.add(modelo)
    db.commit()
    db.refresh(modelo)
    return modelo


@router.get("/modelos/{modelo_id}/itens", response_model=list[DeParaVerbaOut])
def listar_itens(
    modelo_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)
):
    return db.query(DeParaVerba).filter(DeParaVerba.de_para_modelo_id == modelo_id).order_by(
        DeParaVerba.ordem_grupo, DeParaVerba.ordem_item
    ).all()


@router.post("/modelos/{modelo_id}/itens", response_model=DeParaVerbaOut, status_code=status.HTTP_201_CREATED)
def criar_item(
    modelo_id: int,
    payload: DeParaVerbaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    modelo = db.query(DeParaModelo).filter(DeParaModelo.id == modelo_id).first()
    if modelo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modelo de De/Para não encontrado")
    item = DeParaVerba(de_para_modelo_id=modelo_id, **payload.model_dump())
    db.add(item)
    db.flush()
    registrar(
        db,
        entidade="de_para_verbas",
        entidade_id=item.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.CRIACAO,
        dados_depois=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(item)
    return item


@router.put("/itens/{item_id}", response_model=DeParaVerbaOut)
def atualizar_item(
    item_id: int,
    payload: DeParaVerbaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    item = db.query(DeParaVerba).filter(DeParaVerba.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de De/Para não encontrado")

    dados_antes = DeParaVerbaOut.model_validate(item).model_dump(mode="json")
    for campo, valor in payload.model_dump().items():
        setattr(item, campo, valor)

    db.flush()
    registrar(
        db,
        entidade="de_para_verbas",
        entidade_id=item.id,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.EDICAO,
        dados_antes=dados_antes,
        dados_depois=payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_item(item_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(require_admin)):
    item = db.query(DeParaVerba).filter(DeParaVerba.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item de De/Para não encontrado")
    db.delete(item)
    db.commit()


@router.get("/campos-cadastrais", response_model=list[CampoCadastralMapaOut])
def listar_campos_cadastrais(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    return db.query(CampoCadastralMapa).order_by(CampoCadastralMapa.ordem).all()


@router.post("/campos-cadastrais", response_model=CampoCadastralMapaOut, status_code=status.HTTP_201_CREATED)
def criar_campo_cadastral(
    payload: CampoCadastralMapaCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_admin)
):
    campo = CampoCadastralMapa(**payload.model_dump())
    db.add(campo)
    db.commit()
    db.refresh(campo)
    return campo
