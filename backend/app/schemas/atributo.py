from pydantic import BaseModel


class AtributoSegmentacaoBase(BaseModel):
    codigo: str
    descricao: str | None = None


class AtributoSegmentacaoCreate(AtributoSegmentacaoBase):
    pass


class AtributoSegmentacaoOut(AtributoSegmentacaoBase):
    id: int

    model_config = {"from_attributes": True}
