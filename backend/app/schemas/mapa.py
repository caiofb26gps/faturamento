from pydantic import BaseModel

from app.models.enums import StatusMapaGerado


class MapaGeradoOut(BaseModel):
    id: int
    cliente_id: int
    regra_segmentacao_id: int | None
    competencia: str
    status: StatusMapaGerado
    valores_iniciais: dict | None
    valores_finais: dict | None
    diferenca: dict | None
    alertas: dict | None

    model_config = {"from_attributes": True}
