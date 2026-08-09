from pydantic import BaseModel


class DeParaVerbaBase(BaseModel):
    verba_codigo: str
    descricao_original: str | None = None
    evento_exibicao: str
    grupo: str
    ordem_grupo: int
    ordem_item: int


class DeParaVerbaCreate(DeParaVerbaBase):
    pass


class DeParaVerbaOut(DeParaVerbaBase):
    id: int
    de_para_modelo_id: int

    model_config = {"from_attributes": True}


class DeParaModeloBase(BaseModel):
    nome: str


class DeParaModeloCreate(DeParaModeloBase):
    pass


class DeParaModeloOut(DeParaModeloBase):
    id: int
    total_itens: int = 0
    clientes_vinculados: list[str] = []

    model_config = {"from_attributes": True}


class CampoCadastralMapaBase(BaseModel):
    campo: str
    ordem: int


class CampoCadastralMapaCreate(CampoCadastralMapaBase):
    pass


class CampoCadastralMapaOut(CampoCadastralMapaBase):
    id: int

    model_config = {"from_attributes": True}
