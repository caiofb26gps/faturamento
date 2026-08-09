from pydantic import BaseModel


class RegraSegmentacaoBase(BaseModel):
    ordem: int = 0
    atributo_segmentacao: str
    valor_segmentacao: str
    nome_exibicao: str
    email_responsavel: str
    dia_envio: int | None = None
    envio_automatico: bool = False
    analista_id: int | None = None
    aplica_email: bool = True
    aplica_mapa: bool = True


class RegraSegmentacaoCreate(RegraSegmentacaoBase):
    pass


class RegraSegmentacaoUpdate(RegraSegmentacaoBase):
    pass


class RegraSegmentacaoOut(RegraSegmentacaoBase):
    id: int
    cliente_id: int

    model_config = {"from_attributes": True}
