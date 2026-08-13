from pydantic import BaseModel, Field

from app.models.enums import ComparadorCondicao, LogicaRegra


class RegraCondicaoBase(BaseModel):
    atributo: str
    comparador: ComparadorCondicao = ComparadorCondicao.IGUAL
    valor: str


class RegraCondicaoCreate(RegraCondicaoBase):
    pass


class RegraCondicaoOut(RegraCondicaoBase):
    id: int

    model_config = {"from_attributes": True}


class RegraSegmentacaoBase(BaseModel):
    ordem: int = 0
    logica: LogicaRegra = LogicaRegra.E
    nome_exibicao: str
    email_responsavel: str
    dia_envio: int | None = None
    envio_automatico: bool = False
    analista_id: int | None = None
    aplica_email: bool = True
    aplica_mapa: bool = True


class RegraSegmentacaoCreate(RegraSegmentacaoBase):
    # min_length=1: regra sem condição nenhuma não teria como ser avaliada — daria
    # um "pega tudo" ou um "nunca bate" implícito, os dois silenciosos.
    condicoes: list[RegraCondicaoCreate] = Field(..., min_length=1)


class RegraSegmentacaoUpdate(RegraSegmentacaoCreate):
    pass


class RegraSegmentacaoOut(RegraSegmentacaoBase):
    id: int
    cliente_id: int
    condicoes: list[RegraCondicaoOut] = []

    model_config = {"from_attributes": True}
