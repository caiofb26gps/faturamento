from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.cliente import Cliente
from app.models.mapa import MapaGerado
from app.models.usuario import Usuario
from app.schemas.mapa import MapaGeradoOut
from app.services.geracao_mapa import SegmentacaoNaoSuportada, gerar_mapas

router = APIRouter(tags=["mapas"])


@router.post("/clientes/{cliente_id}/mapas/gerar", response_model=list[MapaGeradoOut])
def gerar_mapas_cliente(
    cliente_id: int,
    competencia: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")

    try:
        mapas = gerar_mapas(db, cliente_id, competencia)
    except SegmentacaoNaoSuportada as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not mapas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum lançamento encontrado para este cliente na competência {competencia}",
        )
    return mapas


@router.get("/clientes/{cliente_id}/mapas", response_model=list[MapaGeradoOut])
def listar_mapas_cliente(
    cliente_id: int,
    competencia: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    query = db.query(MapaGerado).filter(MapaGerado.cliente_id == cliente_id)
    if competencia:
        query = query.filter(MapaGerado.competencia == competencia)
    return query.order_by(MapaGerado.id.desc()).all()


@router.get("/mapas/{mapa_id}/arquivo")
def baixar_arquivo_mapa(mapa_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    mapa = db.query(MapaGerado).filter(MapaGerado.id == mapa_id).first()
    if mapa is None or not mapa.arquivo_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapa ou arquivo não encontrado")
    nome = f"mapa_{mapa.competencia}_cliente{mapa.cliente_id}.xlsx"
    return FileResponse(mapa.arquivo_path, filename=nome, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
