from datetime import datetime

from pydantic import BaseModel

from app.models.enums import StatusImportacao, TipoImportacao


class ImportacaoOut(BaseModel):
    id: int
    competencia: str
    tipo: TipoImportacao
    status: StatusImportacao
    cliente_id: int | None
    regra_segmentacao_id: int | None
    mensagem_erro: str | None
    resumo: dict | None
    criado_em: datetime

    model_config = {"from_attributes": True}
