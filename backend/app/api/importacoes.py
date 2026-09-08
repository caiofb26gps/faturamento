import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user
from app.models.enums import TipoImportacao
from app.models.importacao import Importacao
from app.models.usuario import Usuario
from app.schemas.importacao import ImportacaoOut
from app.services.ingestao import criar_importacao, processar_importacao

router = APIRouter(prefix="/importacoes", tags=["importacoes"])

TAMANHO_PEDACO_UPLOAD = 1024 * 1024  # 1 MB


def _rodar_processamento_em_background(importacao_id: int) -> None:
    # Precisa de uma sessão própria: a sessão da requisição (Depends(get_db)) já foi
    # fechada quando o BackgroundTask roda, depois da resposta HTTP ser enviada.
    db = SessionLocal()
    try:
        processar_importacao(db, importacao_id)
    finally:
        db.close()


@router.post("", response_model=ImportacaoOut, status_code=status.HTTP_201_CREATED)
async def enviar_importacao(
    background_tasks: BackgroundTasks,
    arquivo: UploadFile,
    competencia: str = Form(..., description="Formato AAAAMM, ex: 202607"),
    tipo: TipoImportacao = Form(...),
    cliente_id: int | None = Form(None),
    regra_segmentacao_id: int | None = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if tipo == TipoImportacao.AJUSTE and cliente_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ajuste pontual precisa informar cliente_id (é escopado a um cliente)",
        )

    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    nome_arquivo = f"{uuid.uuid4().hex}_{arquivo.filename}"
    caminho = os.path.join(settings.upload_dir, nome_arquivo)
    # Em pedaços, não `await arquivo.read()`: a DS real tem dezenas de MB e ler
    # tudo de uma vez carrega o arquivo inteiro na memória do container.
    with open(caminho, "wb") as destino:
        while pedaco := await arquivo.read(TAMANHO_PEDACO_UPLOAD):
            destino.write(pedaco)

    importacao = criar_importacao(
        db,
        competencia=competencia,
        tipo=tipo,
        usuario_id=usuario.id,
        arquivo_original_path=caminho,
        cliente_id=cliente_id,
        regra_segmentacao_id=regra_segmentacao_id,
    )

    background_tasks.add_task(_rodar_processamento_em_background, importacao.id)
    return importacao


@router.get("/{importacao_id}", response_model=ImportacaoOut)
def obter_importacao(importacao_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    importacao = db.query(Importacao).filter(Importacao.id == importacao_id).first()
    if importacao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Importação não encontrada")
    return importacao


@router.get("", response_model=list[ImportacaoOut])
def listar_importacoes(
    competencia: str | None = None, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)
):
    query = db.query(Importacao)
    if competencia:
        query = query.filter(Importacao.competencia == competencia)
    return query.order_by(Importacao.id.desc()).limit(50).all()
